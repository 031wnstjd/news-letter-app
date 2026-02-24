from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


autoescape = select_autoescape(enabled_extensions=("html", "xml"))


def _template_env() -> Environment:
    root = Path(__file__).resolve().parents[3]
    return Environment(loader=FileSystemLoader(str(root / "templates")), autoescape=autoescape)


@dataclass
class CampaignBody:
    html: str
    text: str


def compose_campaign(context: dict) -> CampaignBody:
    env = _template_env()
    html = env.get_template("newsletter.html.j2").render(**context)
    text = env.get_template("newsletter.txt.j2").render(**context)
    return CampaignBody(html=html, text=text)
