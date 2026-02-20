"""
OpsPilot 服务管理器 v2.0

功能：
- 现代化美观界面
- 一键启动/关闭后端和前端服务
- 自动检测端口占用并清理
- 服务健康检查与自动重启
- 资源监控（CPU/内存）
- 系统托盘最小化
- 日志导出
- 启动后显示可点击链接
- 开机自启动配置
"""
# type: ignore[import]
from __future__ import annotations

import os
import sys
import subprocess
import threading
import time
import socket
import signal
import json
import webbrowser
from pathlib import Path
from typing import Optional, Dict, List, Callable, Any, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
from queue import Queue

import psutil

# 尝试导入 tkinter
if TYPE_CHECKING:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext

try:
    import tkinter as tk  # type: ignore[import]
    from tkinter import ttk, messagebox, scrolledtext  # type: ignore[import]
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    tk = None  # type: ignore[misc]
    ttk = None  # type: ignore[misc]
    messagebox = None  # type: ignore[misc]
    scrolledtext = None  # type: ignore[misc]
    print("警告: tkinter 未安装，将使用命令行模式")

# 配置文件路径
CONFIG_FILE = Path(__file__).parent / "manager_config.json"


@dataclass
class ServiceConfig:
    """服务配置"""
    name: str
    display_name: str
    port: int
    command: List[str]
    cwd: Optional[str] = None
    auto_restart: bool = True
    health_check_url: Optional[str] = None
    description: str = ""


@dataclass
class ServiceStatus:
    """服务状态"""
    is_running: bool = False
    pid: Optional[int] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    uptime_seconds: int = 0
    last_check: Optional[datetime] = None
    start_time: Optional[datetime] = None
    restart_count: int = 0


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG: Dict[str, Any] = {
        "auto_start_on_launch": False,
        "minimize_to_tray": True,
        "check_updates": True,
        "services": {
            "backend": {
                "auto_restart": True,
                "port": 8000
            },
            "frontend": {
                "auto_restart": True,
                "port": 5173
            }
        }
    }
    
    def __init__(self, config_path: Path = CONFIG_FILE) -> None:
        self.config_path: Path = config_path
        self.config: Dict[str, Any] = self.load()
    
    def load(self) -> Dict[str, Any]:
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    saved: Dict[str, Any] = json.load(f)
                    # 合并默认配置
                    return {**self.DEFAULT_CONFIG, **saved}
            except Exception:
                pass
        return self.DEFAULT_CONFIG.copy()
    
    def save(self) -> None:
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        keys = key.split('.')
        value: Any = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        keys = key.split('.')
        config: Dict[str, Any] = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()


class ServiceManager:
    """服务管理器核心类"""
    
    def __init__(self, project_root: str, config_manager: Optional[ConfigManager] = None) -> None:
        self.project_root: Path = Path(project_root)
        self.config_manager: ConfigManager = config_manager or ConfigManager()
        
        # 服务配置
        self.SERVICES: Dict[str, ServiceConfig] = {
            "backend": ServiceConfig(
                name="backend",
                display_name="后端 API 服务",
                port=int(self.config_manager.get('services.backend.port', 8000)),
                command=["python", "-m", "uvicorn", "opspilot.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=None,
                auto_restart=bool(self.config_manager.get('services.backend.auto_restart', True)),
                health_check_url="http://localhost:8000/health",
                description="FastAPI 后端服务，提供 RESTful API"
            ),
            "frontend": ServiceConfig(
                name="frontend",
                display_name="前端开发服务",
                port=int(self.config_manager.get('services.frontend.port', 5173)),
                command=["npm", "run", "dev"],
                cwd="frontend",
                auto_restart=bool(self.config_manager.get('services.frontend.auto_restart', True)),
                description="Vue 3 前端开发服务器"
            ),
        }
        
        self.processes: Dict[str, subprocess.Popen[str]] = {}
        self.status: Dict[str, ServiceStatus] = {
            name: ServiceStatus() for name in self.SERVICES
        }
        self.log_queue: Queue[tuple[str, str, str]] = Queue()
        self._running: bool = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitor: threading.Event = threading.Event()
    
    def log(self, message: str, level: str = "INFO") -> None:
        """添加日志到队列"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put((timestamp, level, message))
    
    def get_port_pid(self, port: int) -> Optional[int]:
        """获取占用指定端口的进程 PID"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                for line in result.stdout.split("\n"):
                    if f":{port}" in line and "LISTENING" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            return int(parts[-1])
            else:
                result = subprocess.run(
                    ["lsof", "-i", f":{port}"],
                    capture_output=True,
                    text=True
                )
                for line in result.stdout.split("\n")[1:]:
                    if line.strip():
                        return int(line.split()[1])
        except Exception:
            pass
        return None
    
    def kill_port(self, port: int) -> bool:
        """关闭占用指定端口的进程"""
        pid = self.get_port_pid(port)
        if not pid:
            return False
        
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                subprocess.run(["kill", "-9", str(pid)], capture_output=True)
            return True
        except Exception:
            return False
    
    def is_port_free(self, port: int) -> bool:
        """检查端口是否空闲"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0
        except Exception:
            return True
    
    def check_health(self, service_name: str) -> bool:
        """检查服务健康状态"""
        config = self.SERVICES.get(service_name)
        if not config or not config.health_check_url:
            return self.status[service_name].is_running
        
        try:
            import urllib.request
            req = urllib.request.Request(config.health_check_url, method='GET')
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
    
    def get_process_resources(self, pid: int) -> tuple[float, float]:
        """获取进程资源使用情况"""
        try:
            process = psutil.Process(pid)
            cpu = process.cpu_percent(interval=0.1)
            memory = process.memory_info().rss / (1024 * 1024)  # MB
            return cpu, memory
        except Exception:
            return 0.0, 0.0
    
    def start_service(self, service_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """启动单个服务"""
        if service_name in self.processes and self.processes[service_name].poll() is None:
            self.log(f"[{service_name}] 服务已在运行中", "WARN")
            return True
        
        config = self.SERVICES[service_name]
        port = config.port
        
        # 检查并清理端口
        if not self.is_port_free(port):
            self.log(f"[{service_name}] 端口 {port} 被占用，正在清理...", "WARN")
            self.kill_port(port)
            time.sleep(1)
        
        # 准备工作目录
        cwd = self.project_root
        if config.cwd:
            cwd = self.project_root / config.cwd
        
        # 启动进程
        try:
            if sys.platform == "win32":
                process = subprocess.Popen(
                    config.command,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
                    shell=True
                )
            else:
                process = subprocess.Popen(
                    config.command,
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    preexec_fn=os.setsid
                )
            
            self.processes[service_name] = process
            self.status[service_name].is_running = True
            self.status[service_name].pid = process.pid
            self.status[service_name].start_time = datetime.now()
            
            self.log(f"[{service_name}] 服务启动成功 (PID: {process.pid})", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"[{service_name}] 启动失败: {str(e)}", "ERROR")
            return False
    
    def stop_service(self, service_name: str, log_callback: Optional[Callable[[str], None]] = None) -> bool:
        """停止单个服务"""
        config = self.SERVICES[service_name]
        
        if service_name not in self.processes:
            # 尝试通过端口关闭
            if self.kill_port(config.port):
                self.log(f"[{service_name}] 已通过端口 {config.port} 关闭服务", "INFO")
                self.status[service_name].is_running = False
                return True
            return False
        
        process = self.processes[service_name]
        
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            process.wait(timeout=5)
            
        except Exception:
            process.kill()
        finally:
            if service_name in self.processes:
                del self.processes[service_name]
            self.status[service_name].is_running = False
            self.status[service_name].pid = None
            
        self.log(f"[{service_name}] 服务已停止", "INFO")
        return True
    
    def restart_service(self, service_name: str) -> bool:
        """重启服务"""
        self.log(f"[{service_name}] 正在重启...", "INFO")
        self.stop_service(service_name)
        time.sleep(1)
        return self.start_service(service_name)
    
    def start_all(self) -> Dict[str, bool]:
        """启动所有服务"""
        self.log("=" * 50, "INFO")
        self.log("正在启动所有服务...", "INFO")
        results = {}
        for name in self.SERVICES:
            results[name] = self.start_service(name)
            time.sleep(2)
        
        success_count = sum(1 for v in results.values() if v)
        self.log(f"启动完成: {success_count}/{len(results)} 服务成功", "SUCCESS")
        self.log("=" * 50, "INFO")
        
        # 启动监控
        self.start_monitor()
        
        return results
    
    def stop_all(self) -> Dict[str, bool]:
        """停止所有服务"""
        self.log("=" * 50, "INFO")
        self.log("正在停止所有服务...", "INFO")
        
        self.stop_monitor()
        
        results = {}
        for name in list(self.processes.keys()):
            results[name] = self.stop_service(name)
        
        # 确保清理所有端口
        for name, config in self.SERVICES.items():
            if not self.is_port_free(config.port):
                self.kill_port(config.port)
                self.log(f"[{name}] 已清理端口 {config.port}", "INFO")
        
        self.log("所有服务已停止", "INFO")
        self.log("=" * 50, "INFO")
        
        return results
    
    def start_monitor(self):
        """启动服务监控"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitor.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitor(self):
        """停止服务监控"""
        self._stop_monitor.set()
    
    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_monitor.wait(5):
            for name, process in list(self.processes.items()):
                status = self.status[name]
                
                # 检查进程是否存活
                if process.poll() is not None:
                    status.is_running = False
                    self.log(f"[{name}] 服务意外退出 (退出码: {process.returncode})", "ERROR")
                    
                    # 自动重启
                    config = self.SERVICES[name]
                    if config.auto_restart and status.restart_count < 5:
                        status.restart_count += 1
                        self.log(f"[{name}] 尝试自动重启 ({status.restart_count}/5)...", "WARN")
                        time.sleep(3)
                        self.start_service(name)
                    continue
                
                # 更新资源使用情况
                if status.pid:
                    cpu, memory = self.get_process_resources(status.pid)
                    status.cpu_percent = cpu
                    status.memory_mb = memory
                
                # 更新运行时间
                if status.start_time:
                    status.uptime_seconds = int((datetime.now() - status.start_time).total_seconds())
                
                status.last_check = datetime.now()
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务状态"""
        result = {}
        for name, config in self.SERVICES.items():
            status = self.status[name]
            port_in_use = not self.is_port_free(config.port)
            
            result[name] = {
                "name": config.display_name,
                "port": config.port,
                "is_running": status.is_running or port_in_use,
                "pid": status.pid,
                "cpu_percent": status.cpu_percent,
                "memory_mb": status.memory_mb,
                "uptime_seconds": status.uptime_seconds,
                "restart_count": status.restart_count,
                "url": f"http://localhost:{config.port}",
                "description": config.description,
                "auto_restart": config.auto_restart
            }
        return result


class ModernTheme:
    """现代化主题配置"""
    
    # 颜色方案
    COLORS: Dict[str, str] = {
        "bg_primary": "#1a1a2e",
        "bg_secondary": "#16213e",
        "bg_card": "#0f3460",
        "accent": "#e94560",
        "accent_hover": "#ff6b6b",
        "success": "#00d26a",
        "warning": "#ffc107",
        "error": "#ff4757",
        "text_primary": "#ffffff",
        "text_secondary": "#a0a0a0",
        "border": "#2d3436",
    }
    
    # 字体
    FONTS: Dict[str, tuple[str, int, Optional[str]]] = {
        "title": ("Segoe UI", 18, "bold"),
        "subtitle": ("Segoe UI", 12, "bold"),
        "normal": ("Segoe UI", 10, None),
        "small": ("Segoe UI", 9, None),
        "mono": ("Consolas", 9, None),
    }


class ManagerGUI:
    """现代化服务管理器 GUI"""
    
    def __init__(self, manager: ServiceManager) -> None:
        self.manager: ServiceManager = manager
        self.config_manager: ConfigManager = manager.config_manager
        
        # 创建主窗口
        self.root: tk.Tk = tk.Tk()
        self.root.title("OpsPilot 服务管理器 v2.0")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 应用主题
        self.apply_theme()
        
        # 系统托盘
        self.tray_icon: Any = None
        self.has_tray: bool = False
        self.setup_tray()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 启动状态更新
        self.update_status()
        
        # 启动日志消费
        self.consume_logs()
        
        # 自动启动检查
        if self.config_manager.get("auto_start_on_launch"):
            self.root.after(1000, self.auto_start)
    
    def apply_theme(self):
        """应用主题"""
        self.root.configure(bg=ModernTheme.COLORS["bg_primary"])
        
        # 配置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 框架样式
        style.configure("Dark.TFrame", background=ModernTheme.COLORS["bg_primary"])
        style.configure("Card.TFrame", background=ModernTheme.COLORS["bg_card"])
        style.configure("Secondary.TFrame", background=ModernTheme.COLORS["bg_secondary"])
        
        # 标签样式
        style.configure("Title.TLabel", 
                       background=ModernTheme.COLORS["bg_primary"],
                       foreground=ModernTheme.COLORS["text_primary"],
                       font=ModernTheme.FONTS["title"])
        
        style.configure("Subtitle.TLabel",
                       background=ModernTheme.COLORS["bg_primary"],
                       foreground=ModernTheme.COLORS["text_primary"],
                       font=ModernTheme.FONTS["subtitle"])
        
        style.configure("Normal.TLabel",
                       background=ModernTheme.COLORS["bg_primary"],
                       foreground=ModernTheme.COLORS["text_secondary"],
                       font=ModernTheme.FONTS["normal"])
        
        style.configure("Success.TLabel",
                       background=ModernTheme.COLORS["bg_primary"],
                       foreground=ModernTheme.COLORS["success"],
                       font=ModernTheme.FONTS["normal"])
        
        style.configure("Error.TLabel",
                       background=ModernTheme.COLORS["bg_primary"],
                       foreground=ModernTheme.COLORS["error"],
                       font=ModernTheme.FONTS["normal"])
        
        style.configure("Card.TLabel",
                       background=ModernTheme.COLORS["bg_card"],
                       foreground=ModernTheme.COLORS["text_primary"],
                       font=ModernTheme.FONTS["normal"])
        
        style.configure("Link.TLabel",
                       background=ModernTheme.COLORS["bg_primary"],
                       foreground=ModernTheme.COLORS["accent"],
                       font=ModernTheme.FONTS["normal"],
                       cursor="hand2")
        
        # 按钮样式
        style.configure("Primary.TButton",
                       background=ModernTheme.COLORS["accent"],
                       foreground=ModernTheme.COLORS["text_primary"],
                       font=ModernTheme.FONTS["normal"],
                       padding=(15, 8),
                       borderwidth=0)
        
        style.map("Primary.TButton",
                 background=[("active", ModernTheme.COLORS["accent_hover"])])
        
        style.configure("Success.TButton",
                       background=ModernTheme.COLORS["success"],
                       foreground=ModernTheme.COLORS["text_primary"],
                       font=ModernTheme.FONTS["normal"],
                       padding=(10, 5),
                       borderwidth=0)
        
        style.configure("Danger.TButton",
                       background=ModernTheme.COLORS["error"],
                       foreground=ModernTheme.COLORS["text_primary"],
                       font=ModernTheme.FONTS["normal"],
                       padding=(10, 5),
                       borderwidth=0)
        
        style.configure("Small.TButton",
                       font=ModernTheme.FONTS["small"],
                       padding=(8, 4))
        
        # LabelFrame 样式
        style.configure("Card.TLabelframe",
                       background=ModernTheme.COLORS["bg_card"],
                       foreground=ModernTheme.COLORS["text_primary"])
        style.configure("Card.TLabelframe.Label",
                       background=ModernTheme.COLORS["bg_card"],
                       foreground=ModernTheme.COLORS["text_primary"],
                       font=ModernTheme.FONTS["subtitle"])
    
    def setup_tray(self):
        """设置系统托盘"""
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # 创建托盘图标
            def create_icon():
                img = Image.new('RGB', (64, 64), color=ModernTheme.COLORS["accent"])
                dc = ImageDraw.Draw(img)
                dc.ellipse([16, 16, 48, 48], fill=ModernTheme.COLORS["text_primary"])
                return img
            
            def on_show(icon, item):
                self.root.after(0, self.root.deiconify)
            
            def on_exit(icon, item):
                self.root.after(0, self.quit_app)
            
            def on_start_all(icon, item):
                self.root.after(0, self.start_all)
            
            def on_stop_all(icon, item):
                self.root.after(0, self.stop_all)
            
            menu = pystray.Menu(
                pystray.MenuItem("显示窗口", on_show, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("启动所有服务", on_start_all),
                pystray.MenuItem("停止所有服务", on_stop_all),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", on_exit),
            )
            
            self.tray_icon = pystray.Icon(
                "OpsPilot",
                create_icon(),
                "OpsPilot 服务管理器",
                menu
            )
            
            # 启动托盘
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            self.has_tray = True
            
        except ImportError:
            self.has_tray = False
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, style="Dark.TFrame", padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题栏
        self.create_header(main_frame)
        
        # 服务卡片区域
        self.create_service_cards(main_frame)
        
        # 快捷操作区
        self.create_quick_actions(main_frame)
        
        # 日志区域
        self.create_log_area(main_frame)
        
        # 底部状态栏
        self.create_footer(main_frame)
    
    def create_header(self, parent: tk.Widget) -> None:
        """创建标题栏"""
        header = ttk.Frame(parent, style="Dark.TFrame")
        header.pack(fill=tk.X, pady=(0, 15))
        
        # Logo 和标题
        title_frame = ttk.Frame(header, style="Dark.TFrame")
        title_frame.pack(side=tk.LEFT)
        
        ttk.Label(
            title_frame,
            text="🚀 OpsPilot",
            style="Title.TLabel"
        ).pack(side=tk.LEFT)
        
        ttk.Label(
            title_frame,
            text="  服务管理器",
            style="Subtitle.TLabel"
        ).pack(side=tk.LEFT, pady=(8, 0))
        
        # 版本标签
        ttk.Label(
            header,
            text="v2.0",
            style="Normal.TLabel"
        ).pack(side=tk.RIGHT)
    
    def create_service_cards(self, parent: tk.Widget) -> None:
        """创建服务卡片"""
        cards_frame = ttk.Frame(parent, style="Dark.TFrame")
        cards_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.service_widgets: Dict[str, Dict[str, Any]] = {}
        
        for idx, (name, config) in enumerate(self.manager.SERVICES.items()):
            card = self.create_service_card(cards_frame, name, config)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if idx == 0 else 10, 0))
            
            self.service_widgets[name] = {
                'status_label': None,
                'link_label': None,
                'pid_label': None,
                'cpu_label': None,
                'memory_label': None,
                'uptime_label': None,
                'start_btn': None,
                'stop_btn': None,
                'restart_btn': None,
            }
    
    def create_service_card(self, parent: tk.Widget, name: str, config: ServiceConfig) -> ttk.Frame:
        """创建单个服务卡片"""
        card = ttk.Frame(parent, style="Card.TFrame", padding="15")
        
        # 服务名称
        header = ttk.Frame(card, style="Card.TFrame")
        header.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            header,
            text=f"📦 {config.display_name}",
            style="Card.TLabel",
            font=ModernTheme.FONTS["subtitle"]
        ).pack(side=tk.LEFT)
        
        # 状态指示器
        self.service_widgets[name]['status_label'] = ttk.Label(
            header,
            text="⏸️ 已停止",
            style="Card.TLabel"
        )
        self.service_widgets[name]['status_label'].pack(side=tk.RIGHT)
        
        # 端口信息
        port_frame = ttk.Frame(card, style="Card.TFrame")
        port_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(
            port_frame,
            text=f"端口: {config.port}",
            style="Card.TLabel"
        ).pack(side=tk.LEFT)
        
        # 链接（可点击）
        self.service_widgets[name]['link_label'] = ttk.Label(
            port_frame,
            text=f"http://localhost:{config.port}",
            style="Link.TLabel"
        )
        self.service_widgets[name]['link_label'].pack(side=tk.RIGHT)
        self.service_widgets[name]['link_label'].bind("<Button-1>", 
            lambda e, url=f"http://localhost:{config.port}": self.open_url(url))
        
        # 资源使用信息
        resource_frame = ttk.Frame(card, style="Card.TFrame")
        resource_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.service_widgets[name]['pid_label'] = ttk.Label(
            resource_frame, text="PID: -", style="Card.TLabel"
        )
        self.service_widgets[name]['pid_label'].pack(side=tk.LEFT, padx=(0, 15))
        
        self.service_widgets[name]['cpu_label'] = ttk.Label(
            resource_frame, text="CPU: -", style="Card.TLabel"
        )
        self.service_widgets[name]['cpu_label'].pack(side=tk.LEFT, padx=(0, 15))
        
        self.service_widgets[name]['memory_label'] = ttk.Label(
            resource_frame, text="内存: -", style="Card.TLabel"
        )
        self.service_widgets[name]['memory_label'].pack(side=tk.LEFT)
        
        self.service_widgets[name]['uptime_label'] = ttk.Label(
            resource_frame, text="", style="Card.TLabel"
        )
        self.service_widgets[name]['uptime_label'].pack(side=tk.RIGHT)
        
        # 操作按钮
        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.pack(fill=tk.X)
        
        self.service_widgets[name]['start_btn'] = ttk.Button(
            btn_frame, text="▶ 启动", style="Success.TButton",
            command=lambda n=name: self.start_service(n)
        )
        self.service_widgets[name]['start_btn'].pack(side=tk.LEFT, padx=(0, 5))
        
        self.service_widgets[name]['stop_btn'] = ttk.Button(
            btn_frame, text="⏹ 停止", style="Danger.TButton",
            command=lambda n=name: self.stop_service(n)
        )
        self.service_widgets[name]['stop_btn'].pack(side=tk.LEFT, padx=(0, 5))
        
        self.service_widgets[name]['restart_btn'] = ttk.Button(
            btn_frame, text="🔄 重启", style="Small.TButton",
            command=lambda n=name: self.restart_service(n)
        )
        self.service_widgets[name]['restart_btn'].pack(side=tk.LEFT)
        
        return card
    
    def create_quick_actions(self, parent: tk.Widget) -> None:
        """创建快捷操作区"""
        actions_frame = ttk.Frame(parent, style="Dark.TFrame")
        actions_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 一键操作
        ttk.Button(
            actions_frame,
            text="🚀 一键启动全部",
            style="Primary.TButton",
            command=self.start_all
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="⏹ 停止全部",
            style="Danger.TButton",
            command=self.stop_all
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(
            actions_frame,
            text="🔄 刷新状态",
            style="Small.TButton",
            command=self.update_status
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # 快捷链接
        ttk.Label(
            actions_frame,
            text="快捷链接:",
            style="Normal.TLabel"
        ).pack(side=tk.LEFT, padx=(20, 10))
        
        ttk.Button(
            actions_frame,
            text="🌐 前端",
            style="Small.TButton",
            command=lambda: self.open_url("http://localhost:5173")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            actions_frame,
            text="📚 API文档",
            style="Small.TButton",
            command=lambda: self.open_url("http://localhost:8000/docs")
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            actions_frame,
            text="📊 ReDoc",
            style="Small.TButton",
            command=lambda: self.open_url("http://localhost:8000/redoc")
        ).pack(side=tk.LEFT)
    
    def create_log_area(self, parent: tk.Widget) -> None:
        """创建日志区域"""
        log_frame = ttk.LabelFrame(
            parent, 
            text="📋 运行日志",
            style="Card.TLabelframe",
            padding="10"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 日志工具栏
        toolbar = ttk.Frame(log_frame, style="Card.TFrame")
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(
            toolbar, text="🗑 清空日志", style="Small.TButton",
            command=self.clear_log
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            toolbar, text="💾 导出日志", style="Small.TButton",
            command=self.export_log
        ).pack(side=tk.LEFT)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=12,
            font=ModernTheme.FONTS["mono"],
            bg=ModernTheme.COLORS["bg_secondary"],
            fg=ModernTheme.COLORS["text_primary"],
            insertbackground=ModernTheme.COLORS["text_primary"],
            selectbackground=ModernTheme.COLORS["accent"],
            borderwidth=0,
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置日志标签颜色
        self.log_text.tag_configure("INFO", foreground=ModernTheme.COLORS["text_primary"])
        self.log_text.tag_configure("SUCCESS", foreground=ModernTheme.COLORS["success"])
        self.log_text.tag_configure("WARN", foreground=ModernTheme.COLORS["warning"])
        self.log_text.tag_configure("ERROR", foreground=ModernTheme.COLORS["error"])
    
    def create_footer(self, parent: tk.Widget) -> None:
        """创建底部状态栏"""
        footer = ttk.Frame(parent, style="Dark.TFrame")
        footer.pack(fill=tk.X)
        
        # 左侧设置
        settings_frame = ttk.Frame(footer, style="Dark.TFrame")
        settings_frame.pack(side=tk.LEFT)
        
        # 自动启动选项
        self.auto_start_var = tk.BooleanVar(
            value=self.config_manager.get("auto_start_on_launch", False)
        )
        auto_start_cb = ttk.Checkbutton(
            settings_frame,
            text="开机自动启动服务",
            variable=self.auto_start_var,
            command=self.toggle_auto_start,
            style="Dark.TCheckbutton"
        )
        auto_start_cb.pack(side=tk.LEFT, padx=(0, 15))
        
        # 自动重启选项
        self.auto_restart_var = tk.BooleanVar(
            value=self.config_manager.get("services.backend.auto_restart", True)
        )
        auto_restart_cb = ttk.Checkbutton(
            settings_frame,
            text="服务崩溃自动重启",
            variable=self.auto_restart_var,
            command=self.toggle_auto_restart,
            style="Dark.TCheckbutton"
        )
        auto_restart_cb.pack(side=tk.LEFT)
        
        # 右侧按钮
        ttk.Button(
            footer,
            text="⚙️ 设置",
            style="Small.TButton",
            command=self.show_settings
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            footer,
            text="退出",
            style="Small.TButton",
            command=self.quit_app
        ).pack(side=tk.RIGHT)
    
    def update_status(self) -> None:
        """更新服务状态"""
        status = self.manager.get_all_status()
        
        for name, info in status.items():
            widgets = self.service_widgets[name]
            
            # 更新状态
            if info["is_running"]:
                widgets['status_label'].config(text="✅ 运行中", foreground=ModernTheme.COLORS["success"])
                widgets['link_label'].config(state="normal")
            else:
                widgets['status_label'].config(text="⏸️ 已停止", foreground=ModernTheme.COLORS["text_secondary"])
                widgets['link_label'].config(state="disabled")
            
            # 更新资源信息
            if info["pid"]:
                widgets['pid_label'].config(text=f"PID: {info['pid']}")
            else:
                widgets['pid_label'].config(text="PID: -")
            
            if info["cpu_percent"] > 0:
                widgets['cpu_label'].config(text=f"CPU: {info['cpu_percent']:.1f}%")
            else:
                widgets['cpu_label'].config(text="CPU: -")
            
            if info["memory_mb"] > 0:
                widgets['memory_label'].config(text=f"内存: {info['memory_mb']:.1f}MB")
            else:
                widgets['memory_label'].config(text="内存: -")
            
            # 更新运行时间
            if info["uptime_seconds"] > 0:
                uptime = self.format_uptime(info["uptime_seconds"])
                widgets['uptime_label'].config(text=f"⏱ {uptime}")
            else:
                widgets['uptime_label'].config(text="")
            
            # 更新按钮状态
            if info["is_running"]:
                widgets['start_btn'].config(state="disabled")
                widgets['stop_btn'].config(state="normal")
            else:
                widgets['start_btn'].config(state="normal")
                widgets['stop_btn'].config(state="disabled")
        
        # 每3秒更新一次
        self.root.after(3000, self.update_status)
    
    def format_uptime(self, seconds: int) -> str:
        """格式化运行时间"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            return f"{seconds // 60}分钟"
        elif seconds < 86400:
            return f"{seconds // 3600}小时{seconds % 3600 // 60}分"
        else:
            return f"{seconds // 86400}天{seconds % 86400 // 3600}小时"
    
    def consume_logs(self) -> None:
        """消费日志队列"""
        try:
            while True:
                timestamp, level, message = self.manager.log_queue.get_nowait()
                self.append_log(timestamp, level, message)
        except:
            pass
        
        # 每100ms检查一次
        self.root.after(100, self.consume_logs)
    
    def append_log(self, timestamp: str, level: str, message: str) -> None:
        """添加日志"""
        self.log_text.insert(tk.END, f"[{timestamp}] ", "INFO")
        self.log_text.insert(tk.END, f"[{level}] ", level)
        self.log_text.insert(tk.END, f"{message}\n", "INFO")
        self.log_text.see(tk.END)
    
    def clear_log(self) -> None:
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
    
    def export_log(self) -> None:
        """导出日志"""
        from datetime import datetime
        log_content = self.log_text.get(1.0, tk.END)
        
        filename = f"opspilot_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = Path.cwd() / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(log_content)
            messagebox.showinfo("导出成功", f"日志已保存到:\n{filepath}")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出日志失败: {e}")
    
    def open_url(self, url: str) -> None:
        """打开URL"""
        webbrowser.open(url)
    
    def start_service(self, name: str) -> None:
        """启动服务"""
        def run() -> None:
            self.manager.start_service(name)
        threading.Thread(target=run, daemon=True).start()
    
    def stop_service(self, name: str) -> None:
        """停止服务"""
        def run() -> None:
            self.manager.stop_service(name)
        threading.Thread(target=run, daemon=True).start()
    
    def restart_service(self, name: str) -> None:
        """重启服务"""
        def run() -> None:
            self.manager.restart_service(name)
        threading.Thread(target=run, daemon=True).start()
    
    def start_all(self) -> None:
        """启动所有服务"""
        def run() -> None:
            self.manager.start_all()
        threading.Thread(target=run, daemon=True).start()
    
    def stop_all(self) -> None:
        """停止所有服务"""
        def run() -> None:
            self.manager.stop_all()
        threading.Thread(target=run, daemon=True).start()
    
    def auto_start(self) -> None:
        """自动启动"""
        self.manager.log("检测到自动启动设置，正在启动服务...", "INFO")
        self.start_all()
    
    def toggle_auto_start(self) -> None:
        """切换自动启动"""
        self.config_manager.set("auto_start_on_launch", self.auto_start_var.get())
    
    def toggle_auto_restart(self) -> None:
        """切换自动重启"""
        value = self.auto_restart_var.get()
        self.config_manager.set("services.backend.auto_restart", value)
        self.config_manager.set("services.frontend.auto_restart", value)
        
        # 更新服务配置
        for name in self.manager.SERVICES:
            self.manager.SERVICES[name].auto_restart = value
    
    def show_settings(self) -> None:
        """显示设置对话框"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("400x300")
        settings_window.configure(bg=ModernTheme.COLORS["bg_primary"])
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # 设置内容
        frame = ttk.Frame(settings_window, style="Dark.TFrame", padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(
            frame,
            text="⚙️ 服务配置",
            style="Title.TLabel"
        ).pack(anchor='w', pady=(0, 20))
        
        # 后端端口
        backend_port_frame = ttk.Frame(frame, style="Dark.TFrame")
        backend_port_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(backend_port_frame, text="后端端口:", style="Normal.TLabel").pack(side=tk.LEFT)
        backend_port_entry = ttk.Entry(backend_port_frame, width=10)
        backend_port_entry.insert(0, str(self.manager.SERVICES["backend"].port))
        backend_port_entry.pack(side=tk.RIGHT)
        
        # 前端端口
        frontend_port_frame = ttk.Frame(frame, style="Dark.TFrame")
        frontend_port_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(frontend_port_frame, text="前端端口:", style="Normal.TLabel").pack(side=tk.LEFT)
        frontend_port_entry = ttk.Entry(frontend_port_frame, width=10)
        frontend_port_entry.insert(0, str(self.manager.SERVICES["frontend"].port))
        frontend_port_entry.pack(side=tk.RIGHT)
        
        def save_settings():
            try:
                backend_port = int(backend_port_entry.get())
                frontend_port = int(frontend_port_entry.get())
                
                self.config_manager.set("services.backend.port", backend_port)
                self.config_manager.set("services.frontend.port", frontend_port)
                
                messagebox.showinfo("保存成功", "设置已保存，重启管理器后生效")
                settings_window.destroy()
            except ValueError:
                messagebox.showerror("错误", "端口必须是数字")
        
        ttk.Button(
            frame,
            text="保存设置",
            style="Primary.TButton",
            command=save_settings
        ).pack(pady=20)
    
    def on_close(self) -> None:
        """关闭窗口"""
        if self.config_manager.get("minimize_to_tray") and self.has_tray:
            self.root.withdraw()
        else:
            self.quit_app()
    
    def quit_app(self) -> None:
        """退出应用"""
        if messagebox.askyesno("确认退出", "退出前是否停止所有服务？"):
            self.manager.stop_all()
            time.sleep(1)
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.root.quit()
    
    def run(self) -> None:
        """运行 GUI"""
        self.append_log(datetime.now().strftime("%H:%M:%S"), "INFO", "OpsPilot 服务管理器已启动")
        self.append_log(datetime.now().strftime("%H:%M:%S"), "INFO", f"项目路径: {self.manager.project_root}")
        self.root.mainloop()


def main() -> None:
    """主函数"""
    # 获取项目根目录
    if getattr(sys, 'frozen', False):
        project_root = Path(sys.executable).parent
    else:
        project_root = Path(__file__).parent
    
    # 创建配置管理器
    config_manager = ConfigManager(project_root / "manager_config.json")
    
    # 创建服务管理器
    manager = ServiceManager(project_root, config_manager)
    
    if HAS_TKINTER:
        # 启动 GUI 模式
        app = ManagerGUI(manager)
        app.run()
    else:
        # 命令行模式
        run_cli(manager)


def run_cli(manager: ServiceManager) -> None:
    """命令行模式"""
    print("=" * 50)
    print("OpsPilot 服务管理器 v2.0 (命令行模式)")
    print("=" * 50)
    print("\n可用命令:")
    print("  1. 启动所有服务")
    print("  2. 停止所有服务")
    print("  3. 查看状态")
    print("  4. 打开前端")
    print("  5. 打开 API 文档")
    print("  6. 退出")
    print()
    
    while True:
        try:
            choice = input("请输入命令编号: ").strip()
            
            if choice == "1":
                print("正在启动所有服务...")
                manager.start_all()
            elif choice == "2":
                print("正在停止所有服务...")
                manager.stop_all()
            elif choice == "3":
                status = manager.get_all_status()
                print("\n服务状态:")
                for name, info in status.items():
                    running = "✅ 运行中" if info["is_running"] else "⏸️ 已停止"
                    print(f"  {info['name']}: {running} (端口 {info['port']})")
                    if info["pid"]:
                        print(f"    PID: {info['pid']}, CPU: {info['cpu_percent']:.1f}%, 内存: {info['memory_mb']:.1f}MB")
                    print(f"    链接: {info['url']}")
                print()
            elif choice == "4":
                webbrowser.open("http://localhost:5173")
            elif choice == "5":
                webbrowser.open("http://localhost:8000/docs")
            elif choice == "6":
                manager.stop_all()
                print("再见！")
                break
            else:
                print("无效命令，请重新输入")
                
        except KeyboardInterrupt:
            print("\n正在退出...")
            manager.stop_all()
            break


if __name__ == "__main__":
    main()
