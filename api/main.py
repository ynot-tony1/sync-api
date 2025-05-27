"""
Main FastAPI application.
"""
import os
import logging
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.processing_routes import router as processing_router
from api.routes.file_routes import router as file_router
from api.routes.ws_routes import router as ws_router
logger: logging.Logger = logging.getLogger("uvicorn.info")

app: FastAPI = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(processing_router)
app.include_router(file_router)
app.include_router(ws_router)
