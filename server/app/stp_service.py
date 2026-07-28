import asyncio
import json
import os.path
import os
from ipaddress import ip_address

import logging

from app.config import LOGGING_CONFIG
from app.routes import api

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware

os.makedirs("log", exist_ok = True)
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
logger.info('start')

app = FastAPI(title="stp_service")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.include_router(api.router, prefix='', tags=["stp_service"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] , #这里可以填写["*"]，表示允许任意ip
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=7001, workers=1, log_config=LOGGING_CONFIG, debug=False)
