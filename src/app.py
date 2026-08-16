import sys
import os
import re
import uuid
import json
import datetime as dt
import pandas as pd
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory

# Ensure src/ is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from analysis import load_data, compute_basic_stats, deduplicate_cases
from evidence import build_evidence_packets
from llm_interface import generate_section_text
from report_generator import render_report

app = Flask(__name__)

# Configure paths
UPLOAD_FOLDER = os.path.join(project_root, 'uploads')
OUTPUT_FOLDER = os.path.join(project_root, 'output')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Session store (in-memory, keyed by UUID)
_sessions = {}


def _md_to_html(md_text):
    """Convert markdown to styled HTML without external dependencies."""
    lines = md_text.split("\n")
    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
        elif stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
        elif stripped == "---":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<hr>")
        elif stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{stripped[2:]}</li>")
        elif stripped == "":
            if in_list:
                html_lines.append("</ul>")
                in_list = False
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{stripped}</p>")

    if in_list:
        html_lines.append("</ul>")

    body = "\n".join(html_lines)
    body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
    body = re.sub(r"\*(.+?)\*", r"<em>\1</em>", body)

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PADER Report</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px;
       margin: 40px auto; padding: 0 20px; color: #333; line-height: 1.7; }}
h1 {{ color: #1a1a2e; border-bottom: 2px solid #16213e; padding-bottom: 10px; }}
h2 {{ color: #16213e; margin-top: 30px; }}
h3 {{ color: #0f3460; }}
hr {{ border: none; border-top: 1px solid #ddd; margin: 30px 0; }}
strong {{ color: #1a1a2e; }}
ul {{ padding-left: 20px; }}
li {{ margin: 4px 0; }}
em {{ color: #666; font-size: 0.9em; }}
p {{ margin: 8px 0; }}
</style></head><body>
{body}
</body></html>"""


def format_evidence_data(data):
    """Format evidence packet data for display in the review cards."""
    if not isinstance(data, dict):
        return str(data)
    formatted = {}
    for k, v in data.items():
        if isinstance(v, list):
            try:
                formatted[k] = ', '.join([
                    f"{item[0]} ({item[1]})"
                    if isinstance(item, (list, tuple)) and len(item) == 2
                    else str(item)
                    for item in v
                ])
            except Exception:
                formatted[k] = str(v)
        elif isinstance(v, dict):
            formatted[k] = ', '.join([f"{k2}: {v2}" for k2, v2 in v.items()])
        else:
            formatted[k] = str(v)
    return formatted


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400

    session_id = str(uuid.uuid4())
    filepath = os.path.join(UPLOAD_FOLDER, f"{session_id}_{file.filename}")
    file.save(filepath)

    # Run analysis
    df = load_data(Path(filepath))
    stats = compute_basic_stats(df)
    packets = build_evidence_packets(stats)
    cases_df = deduplicate_cases(df)

    session_out = os.path.join(OUTPUT_FOLDER, session_id)
    os.makedirs(session_out, exist_ok=True)

    _sessions[session_id] = {
        'packets': packets,
        'stats': stats,
        'cases_df': cases_df,
        'output_dir': session_out,
        'filename': file.filename,
    }

    return redirect(url_for('review', session_id=session_id))


@app.route('/review/<session_id>', methods=['GET', 'POST'])
def review(session_id):
    if session_id not in _sessions:
        return 'Session not found. Please upload a new file.', 404

    session_data = _sessions[session_id]
    packets = session_data['packets']

    if request.method == 'POST':
        decisions = request.json
        rendered = {}
        for name, packet in packets.items():
            if decisions.get(name) == 'approved':
                rendered[name] = generate_section_text(packet)
            else:
                rendered[name] = f'## {name}\n\n[FLAGGED SECTION – review needed]\n'

        report_md = render_report(rendered)

        # Save outputs
        out_dir = session_data['output_dir']

        # Markdown
        md_path = os.path.join(out_dir, 'report.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report_md)

        # HTML (using built-in converter)
        html_path = os.path.join(out_dir, 'report.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(_md_to_html(report_md))

        # Case listing CSV
        csv_path = os.path.join(out_dir, 'cases.csv')
        session_data['cases_df'].to_csv(csv_path, index=False)

        # Run log JSON
        json_path = os.path.join(out_dir, 'run_log.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(
                {'decisions': decisions, 'stats': session_data['stats']},
                f, indent=2, default=str,
            )

        return jsonify({
            'status': 'success',
            'redirect': url_for('results', session_id=session_id),
        })

    # GET – render the review page
    formatted_packets = []
    for name, packet in packets.items():
        formatted_packets.append({
            'name': name,
            'title': name,
            'data': format_evidence_data(packet.get('data', {})),
        })

    return render_template('review.html', session_id=session_id, packets=formatted_packets)


@app.route('/results/<session_id>')
def results(session_id):
    if session_id not in _sessions:
        return 'Session not found.', 404
    session_data = _sessions[session_id]
    return render_template('results.html', session_id=session_id, stats=session_data['stats'])


@app.route('/download/<session_id>/<filename>')
def download(session_id, filename):
    if session_id not in _sessions:
        return 'Session not found.', 404
    return send_from_directory(
        _sessions[session_id]['output_dir'], filename, as_attachment=True,
    )


if __name__ == '__main__':
    print("=" * 60)
    print("  GenAR PADER Web App")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 60)
    app.run(debug=True, use_reloader=False, port=5000)
