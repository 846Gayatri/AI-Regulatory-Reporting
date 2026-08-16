"""Convert pader_report.md → pader_report.html with embedded CSS styling."""
import re, pathlib

md = pathlib.Path("output/pader_report.md").read_text(encoding="utf-8")

CSS = """
body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px;
       margin: 40px auto; padding: 0 20px; color: #333; line-height: 1.7; }
h1 { color: #1a1a2e; border-bottom: 2px solid #16213e; padding-bottom: 10px; }
h2 { color: #16213e; margin-top: 30px; }
h3 { color: #0f3460; }
hr { border: none; border-top: 1px solid #ddd; margin: 30px 0; }
strong { color: #1a1a2e; }
ul { padding-left: 20px; }
li { margin: 4px 0; }
em { color: #666; font-size: 0.9em; }
p { margin: 8px 0; }
"""

# Convert markdown to simple HTML
lines = md.split("\n")
html_lines = []
in_list = False

for line in lines:
    stripped = line.strip()

    # Headings
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

# Bold and italic
body = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", body)
body = re.sub(r"\*(.+?)\*", r"<em>\1</em>", body)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PADER Report</title>
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""

pathlib.Path("output/pader_report.html").write_text(html, encoding="utf-8")
print("Created: output/pader_report.html")
