"""
OpsPilot 服务管理器

功能：
- 一键启动后端和前端服务
- 一键关闭所有服务
- 自动检测端口占用并清理
- 简洁的可视化操作界面
"""
import os
import sys
import subprocess
import threading
import time
import socket
from pathlib import Path
from typing import Optional, Dict, List

# 尝试导入 tkinter
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, scrolledtext
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    print("警告: tkinter 未安装，将使用命令行模式")


class ServiceManager:
    """服务管理器核心类"""
    
    # 服务配置
    SERVICES = {
        "backend": {
            "name": "后端 API 服务",
            "port": 8000,
            "command": ["python", "-m", "uvicorn", "opspilot.main:app", "--host", "0.0.0.0", "--port", "8000"],
            "cwd": None,  # 使用项目根目录
        },
        "frontend": {
            "name": "前端开发服务",
            "port": 5173,
            "command": ["npm", "run", "dev"],
            "cwd": "frontend",
        },
    }
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.processes: Dict[str, subprocess.Popen] = {}
        self.logs: Dict[str, List[str]] = {name: [] for name in self.SERVICES}
        self._running = False
        
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
    
    def start_service(self, service_name: str, log_callback=None) -> bool:
        """启动单个服务"""
        if service_name in self.processes and self.processes[service_name].poll() is None:
            if log_callback:
                log_callback(f"[{service_name}] 服务已在运行中")
            return True
        
        config = self.SERVICES[service_name]
        port = config["port"]
        
        # 检查并清理端口
        if not self.is_port_free(port):
            if log_callback:
                log_callback(f"[{service_name}] 端口 {port} 被占用，正在清理...")
            self.kill_port(port)
            time.sleep(1)
        
        # 准备工作目录
        cwd = self.project_root
        if config["cwd"]:
            cwd = self.project_root / config["cwd"]
        
        # 启动进程
        try:
            if sys.platform == "win32":
                # Windows 下使用 CREATE_NEW_PROCESS_GROUP 以便能够终止进程树
                process = subprocess.Popen(
                    config["command"],
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW,
                    shell=True
                )
            else:
                process = subprocess.Popen(
                    config["command"],
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    preexec_fn=os.setsid
                )
            
            self.processes[service_name] = process
            self._running = True
            
            if log_callback:
                log_callback(f"[{service_name}] 服务启动中... (PID: {process.pid})")
            
            return True
            
        except Exception as e:
            if log_callback:
                log_callback(f"[{service_name}] 启动失败: {str(e)}")
            return False
    
    def stop_service(self, service_name: str, log_callback=None) -> bool:
        """停止单个服务"""
        if service_name not in self.processes:
            # 尝试通过端口关闭
            port = self.SERVICES[service_name]["port"]
            if self.kill_port(port):
                if log_callback:
                    log_callback(f"[{service_name}] 已通过端口 {port} 关闭服务")
                return True
            return False
        
        process = self.processes[service_name]
        
        try:
            if sys.platform == "win32":
                # Windows 下终止进程树
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                # Linux/Mac 下终止进程组
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            
            process.wait(timeout=5)
            
        except Exception:
            process.kill()
        finally:
            del self.processes[service_name]
            
        if log_callback:
            log_callback(f"[{service_name}] 服务已停止")
        
        return True
    
    def start_all(self, log_callback=None) -> Dict[str, bool]:
        """启动所有服务"""
        results = {}
        for name in self.SERVICES:
            results[name] = self.start_service(name, log_callback)
            time.sleep(2)  # 等待服务启动
        return results
    
    def stop_all(self, log_callback=None) -> Dict[str, bool]:
        """停止所有服务"""
        results = {}
        for name in list(self.processes.keys()):
            results[name] = self.stop_service(name, log_callback)
        
        # 确保清理所有端口
        for name, config in self.SERVICES.items():
            port = config["port"]
            if not self.is_port_free(port):
                self.kill_port(port)
                if log_callback:
                    log_callback(f"[{name}] 已清理端口 {port}")
        
        self._running = False
        return results
    
    def get_status(self) -> Dict[str, dict]:
        """获取所有服务状态"""
        status = {}
        for name, config in self.SERVICES.items():
            port = config["port"]
            port_in_use = not self.is_port_free(port)
            process_running = name in self.processes and self.processes[name].poll() is None
            
            status[name] = {
                "name": config["name"],
                "port": port,
                "port_in_use": port_in_use,
                "process_running": process_running,
                "status": "运行中" if (port_in_use or process_running) else "已停止"
            }
        return status


class ManagerGUI:
    """服务管理器 GUI"""
    
    def __init__(self, manager: ServiceManager):
        self.manager = manager
        self.root = tk.Tk()
        self.root.title("OpsPilot 服务管理器")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 启动状态更新
        self.update_status()
    
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义样式
        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Status.TLabel", font=("Arial", 10))
        style.configure("Running.TLabel", foreground="green")
        style.configure("Stopped.TLabel", foreground="red")
        style.configure("Action.TButton", font=("Arial", 11), padding=10)
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            title_frame, 
            text="🚀 OpsPilot 服务管理器",
            style="Title.TLabel"
        ).pack(side=tk.LEFT)
        
        # 服务状态框架
        status_frame = ttk.LabelFrame(main_frame, text="服务状态", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_labels = {}
        for name, config in self.manager.SERVICES.items():
            frame = ttk.Frame(status_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(
                frame, 
                text=f"{config['name']} (端口 {config['port']}):",
                width=25,
                anchor='w'
            ).pack(side=tk.LEFT)
            
            self.status_labels[name] = ttk.Label(
                frame,
                text="检查中...",
                style="Status.TLabel"
            )
            self.status_labels[name].pack(side=tk.LEFT, padx=10)
        
        # 操作按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(
            button_frame,
            text="▶️ 启动所有服务",
            style="Action.TButton",
            command=self.start_all
        ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="⏹️ 停止所有服务",
            style="Action.TButton",
            command=self.stop_all
        ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="🔄 刷新状态",
            style="Action.TButton",
            command=self.update_status
        ).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # 单独服务控制框架
        service_frame = ttk.LabelFrame(main_frame, text="单独服务控制", padding="10")
        service_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.service_buttons = {}
        for name, config in self.manager.SERVICES.items():
            frame = ttk.Frame(service_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=config['name'], width=20, anchor='w').pack(side=tk.LEFT)
            
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(side=tk.LEFT)
            
            start_btn = ttk.Button(
                btn_frame,
                text="启动",
                width=8,
                command=lambda n=name: self.start_service(n)
            )
            start_btn.pack(side=tk.LEFT, padx=2)
            
            stop_btn = ttk.Button(
                btn_frame,
                text="停止",
                width=8,
                command=lambda n=name: self.stop_service(n)
            )
            stop_btn.pack(side=tk.LEFT, padx=2)
            
            self.service_buttons[name] = (start_btn, stop_btn)
        
        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部信息
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            footer_frame,
            text="🌐 打开前端",
            command=self.open_frontend
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            footer_frame,
            text="📚 打开 API 文档",
            command=self.open_api_docs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            footer_frame,
            text="退出",
            command=self.on_exit
        ).pack(side=tk.RIGHT, padx=5)
    
    def log(self, message: str):
        """添加日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def update_status(self):
        """更新服务状态"""
        status = self.manager.get_status()
        
        for name, info in status.items():
            label = self.status_labels[name]
            label.config(text=info["status"])
            
            if info["status"] == "运行中":
                label.config(style="Running.TLabel")
            else:
                label.config(style="Stopped.TLabel")
        
        # 每5秒更新一次
        self.root.after(5000, self.update_status)
    
    def start_service(self, name: str):
        """启动单个服务"""
        def run():
            self.log(f"正在启动 {name}...")
            success = self.manager.start_service(name, self.log)
            if success:
                self.log(f"✅ {name} 启动成功")
            else:
                self.log(f"❌ {name} 启动失败")
            self.update_status()
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_service(self, name: str):
        """停止单个服务"""
        self.log(f"正在停止 {name}...")
        success = self.manager.stop_service(name, self.log)
        if success:
            self.log(f"✅ {name} 已停止")
        else:
            self.log(f"❌ {name} 停止失败")
        self.update_status()
    
    def start_all(self):
        """启动所有服务"""
        def run():
            self.log("=" * 50)
            self.log("正在启动所有服务...")
            results = self.manager.start_all(self.log)
            
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            
            self.log(f"启动完成: {success_count}/{total_count} 服务成功")
            self.log("=" * 50)
            self.update_status()
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_all(self):
        """停止所有服务"""
        self.log("=" * 50)
        self.log("正在停止所有服务...")
        results = self.manager.stop_all(self.log)
        self.log("所有服务已停止")
        self.log("=" * 50)
        self.update_status()
    
    def open_frontend(self):
        """打开前端页面"""
        import webbrowser
        webbrowser.open("http://localhost:5173")
    
    def open_api_docs(self):
        """打开 API 文档"""
        import webbrowser
        webbrowser.open("http://localhost:8000/docs")
    
    def on_exit(self):
        """退出程序"""
        if messagebox.askyesno("确认退出", "退出前是否停止所有服务？"):
            self.manager.stop_all(self.log)
            time.sleep(1)
        self.root.quit()
    
    def run(self):
        """运行 GUI"""
        self.log("OpsPilot 服务管理器已启动")
        self.log(f"项目路径: {self.manager.project_root}")
        self.root.mainloop()


def main():
    """主函数"""
    # 获取项目根目录
    if getattr(sys, 'frozen', False):
        # 打包后的可执行文件
        project_root = Path(sys.executable).parent
    else:
        # 脚本运行
        project_root = Path(__file__).parent
    
    # 创建服务管理器
    manager = ServiceManager(project_root)
    
    if HAS_TKINTER:
        # 启动 GUI 模式
        app = ManagerGUI(manager)
        app.run()
    else:
        # 命令行模式
        print("=" * 50)
        print("OpsPilot 服务管理器 (命令行模式)")
        print("=" * 50)
        print("\n可用命令:")
        print("  1. 启动所有服务")
        print("  2. 停止所有服务")
        print("  3. 查看状态")
        print("  4. 退出")
        print()
        
        while True:
            try:
                choice = input("请输入命令编号: ").strip()
                
                if choice == "1":
                    print("正在启动所有服务...")
                    manager.start_all(print)
                elif choice == "2":
                    print("正在停止所有服务...")
                    manager.stop_all(print)
                elif choice == "3":
                    status = manager.get_status()
                    for name, info in status.items():
                        print(f"  {info['name']}: {info['status']}")
                elif choice == "4":
                    manager.stop_all(print)
                    print("再见！")
                    break
                else:
                    print("无效命令，请重新输入")
                    
            except KeyboardInterrupt:
                print("\n正在退出...")
                manager.stop_all(print)
                break


if __name__ == "__main__":
    main()
