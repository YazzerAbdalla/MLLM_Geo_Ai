import sys
from unittest.mock import MagicMock
sys.modules['ee'] = MagicMock()

import os
print("1")
from dotenv import load_dotenv
print("2")
import ee
print("3")
from fastapi import FastAPI
print("4")
from app.interfaces.api import router as api_router
print("5")
from app.infrastructure.db import engine, Base
print("6")
from app.infrastructure.redis_store import RedisJobStore
print("7")
from app.infrastructure.job_store import _redis_store
print("8")
