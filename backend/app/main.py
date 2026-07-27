from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="ModelFlow API", version="0.1.0")

    @app.get("/healthz")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
