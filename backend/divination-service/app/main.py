import logging
import os

from fastapi import FastAPI

from app.router import router

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title="divination-service", version="0.1.0")

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
