# coding=utf-8
"""
@file    web
@date    2023/8/8 11:26
@author  zlf
"""
import time
from functools import wraps

from fastapi import FastAPI, Request
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from dto import ClusterRequest
from database import create_job


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/cluster", response_model=int)
    # @used_time
    async def post(body: ClusterRequest, request: Request):
        return create_job(body)

    @app.get("/job/{job_id}")
    @used_time
    async def res(job_id: int, request: Request):
        return {"item_id": job_id}

    return app


def used_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request: Request = kwargs["request"]
        if request is None:
            logger.warning("Missing Request parameter.")
        start_time = int(round(time.time() * 1000))
        res = await func(*args, **kwargs)
        end_time = int(round(time.time() * 1000))
        logger.info("From host: {}, Used time: {}ms, Method: {}, Url: {}",
                    request.client.host if request is not None else "Missing",
                    end_time - start_time,
                    request.method if request is not None else "Missing",
                    request.url if request is not None else "Missing")
        return res

    import inspect
    sig = inspect.signature(wrapper)
    sig.replace(parameters=[
        *filter(
            lambda p: p.kind not in (
                inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD),
            inspect.signature(wrapper).parameters.values()
        )
    ], return_annotation=inspect.signature(func).return_annotation)
    return wrapper
