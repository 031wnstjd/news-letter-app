from pydantic import BaseModel
from fastapi import APIRouter

from .client import AISummarizer

router = APIRouter(prefix='/v1/summaries', tags=['summaries'])


class GenerateSummaryIn(BaseModel):
    title: str
    url: str
    source_text: str


def summarize_for_api(title: str, source_text: str, url: str) -> dict:
    result = AISummarizer().summarize_item(title=title, source_text=source_text, url=url)
    return {'ok': result.ok, 'lines': result.lines, 'error': result.error}


@router.post('/generate')
def generate(payload: GenerateSummaryIn) -> dict:
    return summarize_for_api(payload.title, payload.source_text, payload.url)
