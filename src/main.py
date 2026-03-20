import sys
import os

import tkinter as tk
from pystray import MenuItem as Item
import pystray
from PIL import Image
import io

from src.config_manager import load_config
from src.api_client import fetch_remains
from src.database import init_db, Database
from src.ui import App

# 项目根目录（兼容 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    # 打包后的可执行文件
    bundle_dir = sys._MEIPASS
    PROJECT_ROOT = os.path.dirname(bundle_dir)
else:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_logo():
    """加载logo图片"""
    if getattr(sys, 'frozen', False):
        logo_path = os.path.join(sys._MEIPASS, "src", "observer-logo.svg")
    else:
        logo_path = os.path.join(PROJECT_ROOT, "src", "observer-logo.svg")
    if os.path.exists(logo_path):
        try:
            import cairosvg
            png_data = cairosvg.svg2png(url=logo_path, output_width=64, output_height=64)
            return Image.open(io.BytesIO(png_data))
        except Exception:
            pass
    # 回退：返回默认图标
    return Image.new('RGB', (64, 64), color="#2563EB")


COLORS = {
    "bg": "#0F172A",
    "surface": "#1E293B",
    "primary": "#2563EB",
    "text": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444"
}

def setup_tray(root, app_ref, lock_file):
    """设置系统托盘"""
    # 加载图标
    icon_image = load_logo()

    def show_window(icon=None, item=None):
        root.deiconify()
        root.lift()
        root.focus_force()

    def refresh_data(icon, item):
        if app_ref and app_ref():
            app_ref().refresh_data()

    def quit_app(icon, item):
        if app_ref and app_ref():
            app_ref().stop()
        release_single_instance(lock_file)
        icon.stop()

    menu = (
        Item('显示窗口', show_window),
        Item('刷新数据', refresh_data),
        Item('退出', quit_app),
    )

    icon = pystray.Icon("minimax-monitor", icon_image, "MiniMax 配额监控", menu, on_click=show_window)
    return icon


def get_lock_file():
    """获取锁文件路径"""
    return os.path.join(PROJECT_ROOT, "minimax-monitor.lock")


def acquire_single_instance():
    """确保同一时间只能启动一个进程。成功返回锁文件对象，失败返回 None"""
    lock_path = get_lock_file()
    try:
        lock_file = open(lock_path, "w")
        # Windows: 使用 msvcrt 加锁，LK_NBLCK = 非阻塞锁
        import msvcrt
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        return lock_file
    except (IOError, OSError, ImportError):
        # 锁文件已存在或其他进程持有锁
        try:
            lock_file.close()
        except Exception:
            pass
        return None


def release_single_instance(lock_file):
    """释放单实例锁"""
    if lock_file:
        try:
            import msvcrt
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
        try:
            lock_file.close()
        except Exception:
            pass
        try:
            os.remove(get_lock_file())
        except Exception:
            pass


def main():
    """主函数"""
    # 单实例检查
    lock_file = acquire_single_instance()
    if lock_file is None:
        root = tk.Tk()
        root.withdraw()  # 隐藏空白窗口
        tk.messagebox.showwarning("提示", "程序已在运行中，请勿重复启动。")
        root.destroy()
        sys.exit(0)

    # 加载配置
    config = load_config()

    # 初始化数据库
    init_db()

    # 创建数据库对象
    db = Database()

    # 创建主窗口
    root = tk.Tk()

    # 创建应用
    app = App(root, config, {"fetch_remains": fetch_remains}, db)

    # 保存应用引用
    app_ref = [app]

    # 设置系统托盘
    tray_icon = setup_tray(root, lambda: app_ref[0] if app_ref else None, lock_file)

    # 在后台线程运行托盘图标
    import threading
    tray_thread = threading.Thread(target=tray_icon.run, daemon=True)
    tray_thread.start()

    # 运行主循环
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.stop()
    finally:
        release_single_instance(lock_file)


if __name__ == "__main__":
    main()
