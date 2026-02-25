"""
OpsPilot 服务管理器 - 简洁版

功能：
- 启动/停止/重启后端和前端服务
- 实时状态监控
- 简洁美观的界面
"""
import os
import sys
import subprocess
import threading
import time
import socket
import webbrowser
from pathlib import Path
from typing import Optional, Dict

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    print("错误: 需要安装 tkinter 库")


# 项目根目录
PROJECT_ROOT = Path(__file__).parent


class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.services = {
            "backend": {
                "name": "后端服务",
                "port": 8000,
                "command": ["python", "-m", "uvicorn", "OpsPilot.opspilot.main:app", "--host", "0.0.0.0", "--port", "8000"],
                "cwd": str(PROJECT_ROOT / "OpsPilot"),
                "running": False,
                "pid": None,
            },
            "frontend": {
                "name": "前端服务",
                "port": 5173,
                "command": ["npm", "run", "dev"],
                "cwd": str(PROJECT_ROOT / "OpsPilot" / "frontend"),
                "running": False,
                "pid": None,
            }
        }
        self.log_callback: Optional[callable] = None
    
    def log(self, message: str):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message)
        print(f"[{time.strftime('%H:%M:%S')}] {message}")
    
    def set_log_callback(self, callback):
        """设置日志回调"""
        self.log_callback = callback
    
    def is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def kill_port(self, port: int):
        """杀掉占用端口的进程"""
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    f'netstat -ano | findstr :{port} | findstr LISTENING',
                    shell=True, capture_output=True, text=True
                )
                if result.stdout:
                    parts = result.stdout.strip().split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        subprocess.run(f'taskkill /F /PID {pid}', shell=True)
                        self.log(f"已清理端口 {port}")
            else:
                subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True)
        except Exception as e:
            self.log(f"清理端口失败: {e}")
    
    def start_service(self, name: str) -> bool:
        """启动服务"""
        service = self.services[name]
        
        if service["running"]:
            self.log(f"[{service['name']}] 已在运行")
            return True
        
        # 检查端口
        if self.is_port_in_use(service["port"]):
            self.log(f"[{service['name']}] 端口 {service['port']} 被占用，正在清理...")
            self.kill_port(service["port"])
            time.sleep(1)
        
        try:
            # Windows 下使用 CREATE_NO_WINDOW
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            
            process = subprocess.Popen(
                service["command"],
                cwd=service["cwd"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                creationflags=creationflags
            )
            
            self.processes[name] = process
            service["running"] = True
            service["pid"] = process.pid
            
            self.log(f"[{service['name']}] 已启动 (PID: {process.pid})")
            return True
            
        except Exception as e:
            self.log(f"[{service['name']}] 启动失败: {e}")
            return False
    
    def stop_service(self, name: str):
        """停止服务"""
        service = self.services[name]
        
        if name in self.processes:
            process = self.processes[name]
            try:
                if sys.platform == "win32":
                    subprocess.run(f'taskkill /F /T /PID {process.pid}', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    process.terminate()
                del self.processes[name]
            except:
                pass
        
        # 确保端口释放
        if self.is_port_in_use(service["port"]):
            self.kill_port(service["port"])
        
        service["running"] = False
        service["pid"] = None
        self.log(f"[{service['name']}] 已停止")
    
    def restart_service(self, name: str):
        """重启服务"""
        self.log(f"[{service['name']}] 重启中...")
        self.stop_service(name)
        time.sleep(1)
        self.start_service(name)
    
    def check_status(self):
        """检查所有服务状态"""
        for name, service in self.services.items():
            if name in self.processes:
                process = self.processes[name]
                if process.poll() is not None:
                    service["running"] = False
                    service["pid"] = None
            else:
                service["running"] = False
    
    def get_status(self) -> Dict:
        """获取状态"""
        self.check_status()
        return {
            name: {
                "name": s["name"],
                "port": s["port"],
                "running": s["running"],
                "pid": s["pid"],
                "url": f"http://localhost:{s['port']}"
            }
            for name, s in self.services.items()
        }


class ManagerApp:
    """管理器应用"""
    
    def __init__(self):
        self.manager = ServiceManager()
        self.root = tk.Tk()
        self.root.title("OpsPilot 服务管理")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)
        
        # 设置主题
        self.setup_theme()
        
        # 创建界面
        self.create_widgets()
        
        # 设置日志回调
        self.manager.set_log_callback(self.add_log)
        
        # 启动状态检查
        self.check_status()
    
    def setup_theme(self):
        """设置主题"""
        self.root.configure(bg="#1e1e2e")
        
        # 颜色
        self.colors = {
            "bg": "#1e1e2e",
            "card": "#2d2d44",
            "primary": "#7c3aed",
            "success": "#10b981",
            "danger": "#ef4444",
            "warning": "#f59e0b",
            "text": "#f8fafc",
            "text_secondary": "#94a3b8",
        }
        
        # 样式
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["card"])
        
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"])
        style.configure("Card.TLabel", background=self.colors["card"], foreground=self.colors["text"])
        
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", font=("Segoe UI", 12))
        
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 5))
        style.map("TButton", background=[("active", self.colors["primary"])])
        
        style.configure("Success.TButton", background=self.colors["success"], foreground="white")
        style.configure("Danger.TButton", background=self.colors["danger"], foreground="white")
    
    def create_widgets(self):
        """创建界面"""
        # 主框架
        main = ttk.Frame(self.root, style="TFrame", padding=20)
        main.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title = ttk.Label(main, text="🚀 OpsPilot", style="Title.TLabel")
        title.pack(pady=(0, 5))
        
        subtitle = ttk.Label(main, text="服务管理器", style="TLabel")
        subtitle.pack(pady=(0, 20))
        
        # 服务卡片容器
        self.cards_frame = ttk.Frame(main, style="TFrame")
        self.cards_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.service_widgets = {}
        
        # 创建服务卡片
        for name in ["backend", "frontend"]:
            card = self.create_service_card(name)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            self.service_widgets[name] = card
        
        # 操作按钮
        btn_frame = ttk.Frame(main, style="TFrame")
        btn_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(
            btn_frame, text="🚀 启动全部",
            style="Success.TButton",
            command=self.start_all
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, text="⏹ 停止全部",
            style="Danger.TButton",
            command=self.stop_all
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame, text="🔄 刷新",
            command=self.check_status
        ).pack(side=tk.LEFT, padx=5)
        
        # 快捷链接
        link_frame = ttk.Frame(main, style="TFrame")
        link_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(link_frame, text="快捷链接:", style="TLabel").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            link_frame, text="🌐 前端",
            command=lambda: webbrowser.open("http://localhost:5173")
        ).pack(side=tk.LEFT, padx=3)
        
        ttk.Button(
            link_frame, text="📚 API文档",
            command=lambda: webbrowser.open("http://localhost:8000/docs")
        ).pack(side=tk.LEFT, padx=3)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main, text="日志", style="Card.TFrame", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_frame,
            height=10,
            bg="#1a1a2e",
            fg="#e2e8f0",
            font=("Consolas", 9),
            borderwidth=0,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部状态栏
        status_frame = ttk.Frame(main, style="TFrame")
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(
            status_frame,
            text="就绪",
            style="TLabel"
        )
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Button(
            status_frame, text="退出",
            command=self.quit
        ).pack(side=tk.RIGHT)
    
    def create_service_card(self, name: str) -> ttk.Frame:
        """创建服务卡片"""
        service = self.manager.services[name]
        
        card = ttk.Frame(self.cards_frame, style="Card.TFrame", padding=15)
        
        # 服务名称和状态
        header = ttk.Frame(card, style="Card.TFrame")
        header.pack(fill=tk.X, pady=(0, 10))
        
        name_label = ttk.Label(
            header,
            text=f"📦 {service['name']}",
            style="Card.TLabel",
            font=("Segoe UI", 11, "bold")
        )
        name_label.pack(side=tk.LEFT)
        
        status_label = ttk.Label(
            header,
            text="⏸ 已停止",
            style="Card.TLabel",
            foreground=self.colors["text_secondary"]
        )
        status_label.pack(side=tk.RIGHT)
        
        # 端口信息
        port_label = ttk.Label(
            card,
            text=f"端口: {service['port']}",
            style="Card.TLabel"
        )
        port_label.pack(pady=(0, 5))
        
        # PID
        pid_label = ttk.Label(
            card,
            text="PID: -",
            style="Card.TLabel"
        )
        pid_label.pack(pady=(0, 10))
        
        # 按钮
        btn_frame = ttk.Frame(card, style="Card.TFrame")
        btn_frame.pack(fill=tk.X)
        
        start_btn = ttk.Button(
            btn_frame, text="▶ 启动",
            style="Success.TButton",
            command=lambda: self.start_service(name)
        )
        start_btn.pack(side=tk.LEFT, padx=2)
        
        stop_btn = ttk.Button(
            btn_frame, text="⏹ 停止",
            style="Danger.TButton",
            command=lambda: self.stop_service(name),
            state=tk.DISABLED
        )
        stop_btn.pack(side=tk.LEFT, padx=2)
        
        # 保存引用
        card.info = {
            "status_label": status_label,
            "pid_label": pid_label,
            "start_btn": start_btn,
            "stop_btn": stop_btn,
            "port": service["port"]
        }
        
        return card
    
    def add_log(self, message: str):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def update_card(self, name: str, info: dict):
        """更新卡片状态"""
        card = self.service_widgets[name]
        data = card.info
        
        if info["running"]:
            data["status_label"].config(text="✅ 运行中", foreground=self.colors["success"])
            data["pid_label"].config(text=f"PID: {info['pid']}")
            data["start_btn"].config(state=tk.DISABLED)
            data["stop_btn"].config(state=tk.NORMAL)
        else:
            data["status_label"].config(text="⏸ 已停止", foreground=self.colors["text_secondary"])
            data["pid_label"].config(text="PID: -")
            data["start_btn"].config(state=tk.NORMAL)
            data["stop_btn"].config(state=tk.DISABLED)
    
    def check_status(self):
        """检查状态"""
        status = self.manager.get_status()
        running_count = 0
        
        for name, info in status.items():
            self.update_card(name, info)
            if info["running"]:
                running_count += 1
        
        self.status_label.config(text=f"运行中: {running_count}/2")
        
        # 3秒后再次检查
        self.root.after(3000, self.check_status)
    
    def start_service(self, name: str):
        """启动服务"""
        def run():
            self.manager.start_service(name)
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_service(self, name: str):
        """停止服务"""
        def run():
            self.manager.stop_service(name)
        
        threading.Thread(target=run, daemon=True).start()
    
    def start_all(self):
        """启动全部"""
        def run():
            for name in self.manager.services:
                self.manager.start_service(name)
                time.sleep(1)
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_all(self):
        """停止全部"""
        def run():
            for name in self.manager.services:
                self.manager.stop_service(name)
        
        threading.Thread(target=run, daemon=True).start()
    
    def quit(self):
        """退出"""
        if messagebox.askyesno("确认", "是否停止所有服务并退出？"):
            self.stop_all()
            time.sleep(1)
            self.root.quit()
    
    def run(self):
        """运行"""
        self.add_log("OpsPilot 服务管理器已启动")
        self.root.mainloop()


def main():
    """主函数"""
    if not HAS_TKINTER:
        print("错误: 需要安装 tkinter 库")
        print("在 Windows 上，请安装 python-tk 包")
        return
    
    app = ManagerApp()
    app.run()


if __name__ == "__main__":
    main()