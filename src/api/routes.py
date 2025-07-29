"""
API路由模块
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 路由将在app.py中直接定义，这里作为扩展点预留 