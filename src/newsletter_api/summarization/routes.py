from pydantic import BaseModel
from fastapi import APIRouter

from .client import AISummarizer, summarize_text

router = APIRouter(prefix='/v1/summaries', tags=['summaries'])


class GenerateSummaryIn(BaseModel):
    title: str
    url: str
    source_text: str


def summarize_for_api(title: str, source_text: str, url: str) -> dict:
    result = AISummarizer().summarize_item(title=title, source_text=source_text, url=url)
    if result.ok:
        return {'ok': True, 'lines': result.lines, 'error': ''}
    fallback = summarize_text(source_text)
    return {'ok': fallback.ok, 'lines': fallback.lines, 'error': result.error}


@router.post('/generate')
def generate(payload: GenerateSummaryIn) -> dict:
    return summarize_for_api(payload.title, payload.source_text, payload.url)
