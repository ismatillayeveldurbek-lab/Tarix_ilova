"""FastAPI ilovasi: /api/... marshrutlari va Mini App fayllari (webapp/dist)."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import admin, app_routes
from app.config import BASE_DIR

WEBAPP_DIST = BASE_DIR.parent / "webapp" / "dist"


def create_app(lifespan=None) -> FastAPI:
    api = FastAPI(title="Tarix ilova API", lifespan=lifespan)
    api.include_router(app_routes.router)
    api.include_router(admin.router)

    @api.get("/api/health")
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
