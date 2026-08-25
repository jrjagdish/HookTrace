import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Importing db triggers Base.metadata.create_all(); routers below also depend on it.
import db  # noqa: F401
from routers.auth import router as auth_router
from routers.chat import router as chat_router
from routers.repositories import router as repositories_router



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("repochat")

app = FastAPI(title="RepoChat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth_router)
app.include_router(repositories_router)
app.include_router(chat_router)
