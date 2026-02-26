"""
Pytest 配置文件 - 设置 Python 模块路径
"""
import sys
from pathlib import Path

# 将 backend 目录添加到 Python 路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))
