from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=['frontend'])

_TEMPLATES_DIR = Path(__file__).resolve().parents[3] / 'templates'
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


@router.get('/', response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        'web/index.html.j2',
        {
            'app_name': 'AI Dev Daily',
            'subtitle': '실제로 동작하는 AI 뉴스레터 요약 워크벤치',
        },
    )
