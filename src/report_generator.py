# src/report_generator.py
"""Render the final PADER markdown report.

The pipeline builds a dictionary ``rendered_sections`` where each key is a
section name (e.g. "Summary", "Serious Cases") and the value is the Markdown
text for that section.  This module loads a very small Jinja2 template and
injects the dictionary so the report can be customised later without changing
code.
"""

import os
import datetime as dt
from pathlib import Path
from typing import Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template lives in ``src/templates/report_template.md`` relative to this file
TEMPLATE_PATH = Path(__file__).parent / "templates" / "report_template.md"


def _load_template() -> Environment:
    """Create a Jinja2 environment pointing at the template directory.

    Returns a ready‑to‑render template object.
    """
    loader = FileSystemLoader(searchpath=str(TEMPLATE_PATH.parent))
    env = Environment(
        loader=loader,
        autoescape=select_autoescape(["html", "xml"]),
        keep_trailing_newline=True,
    )
    return env.get_template(TEMPLATE_PATH.name)


def render_report(sections: Dict[str, str]) -> str:
    """Render the final markdown report.

    Parameters
    ----------
    sections: dict
        Mapping of section name → rendered markdown text for that section.

    Returns
    -------
    str
        The complete markdown document.
    """
    template = _load_template()
    # The template expects a variable called ``sections`` containing the dict.
    return template.render(
        sections=sections,
        generated_date=dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
