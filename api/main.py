from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.config.settings import ALLOWED_LOCAL_1, ALLOWED_LOCAL_2
from api.routes.processing_routes import router as processing_router
from api.routes.file_routes import router as file_router
import logging
from api.routes.ws_routes import router as ws_router  
from device_config import DEVICE
logger = logging.getLogger("uvicorn.info")

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


app.include_router(processing_router)
app.include_router(file_router)
app.include_router(ws_router)


@app.get("/", tags=["root"])
def read_root():
    return {"message": "welcome to sync-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_exclude=["syncnet_python/data/work/pytmp*"] 
    )
