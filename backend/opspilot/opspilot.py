"""
opspilot 模块别名 - 指向 src 模块

这个文件用于兼容旧代码中的 'from opspilot.xxx import' 导入方式。
"""
import sys
from pathlib import Path

# 将当前目录添加到路径
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

# 重新导入 src 模块的所有内容
from src import *
from src import __version__

# 创建 opspilot 模块并复制 src 的所有属性
import types
opspilot = types.ModuleType('opspilot')
opspilot.__dict__.update(src_dir.glob('**/__init__.py'))

# 将 opspilot 注册到 sys.modules
sys.modules['opspilot'] = opspilot
