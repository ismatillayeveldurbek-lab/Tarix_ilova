"""FastAPI ilovasi: /api/... marshrutlari va Mini App fayllari (webapp/dist)."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from app.api.routes import admin, app_routes, v1
from app.config import BASE_DIR
from app.db import SessionLocal
from app.models import Media

WEBAPP_DIST = BASE_DIR.parent / "webapp" / "dist"


def create_app(lifespan=None) -> FastAPI:
    api = FastAPI(title="Tarix ilova API", lifespan=lifespan)
    api.include_router(app_routes.router)
    api.include_router(admin.router)
    api.include_router(v1.router)

    @api.get("/api/media/{media_id}", include_in_schema=False)
    async def media(media_id: int) -> Response:
        async with SessionLocal() as session:
            m = await session.get(Media, media_id)
        if m is None:
            raise HTTPException(404)
        return Response(m.data, media_type=m.mime, headers={
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
        })

    @api.api_route("/api/health", methods=["GET", "HEAD"])
    async def health() -> dict:
        return {"ok": True}

    if WEBAPP_DIST.exists():
        api.mount("/assets", StaticFiles(directory=WEBAPP_DIST / "assets"), name="assets")

        @api.get("/{path:path}", include_in_schema=False)
        async def spa(path: str) -> FileResponse:
            if path.startswith("api/"):
                raise HTTPException(404)
            file = (WEBAPP_DIST / path).resolve()
            if path and file.is_file() and WEBAPP_DIST.resolve() in file.parents:
                return FileResponse(file)
            return FileResponse(WEBAPP_DIST / "index.html", headers={"Cache-Control": "no-cache"})
    return api
