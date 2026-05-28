from pathlib import Path

from django.conf import settings
from django.http import HttpResponse


def react_app(request):
    index_path = settings.REPO_DIR / "frontend" / "dist" / "index.html"
    if not Path(index_path).exists():
        return HttpResponse(
            "Frontend build not found. Run `npm run build` inside the frontend folder.",
            status=503,
        )
    return HttpResponse(index_path.read_text(encoding="utf-8"))
