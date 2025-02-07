from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config.settings import ALLOWED_LOCAL_1, ALLOWED_LOCAL_2
from api.routes.processing_routes import router as processing_router
from api.routes.file_routes import router as file_router
import logging

logger = logging.getLogger("fastapi")

app = FastAPI()

origins = [
    ALLOWED_LOCAL_1,
    ALLOWED_LOCAL_2,
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include the routers in the app
app.include_router(processing_router)
app.include_router(file_router)

@app.get("/", tags=["root"])
def read_root():
    return {"message": "welcome to sync-api"}