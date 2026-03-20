import tkinter as tk
from tkinter import ttk, messagebox, font
import threading
import time
import os
import sys
import subprocess
import json
import io
from datetime import datetime, timedelta

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_window_icon():
    """加载窗口图标"""
    logo_path = os.path.join(PROJECT_ROOT, "src", "observer-logo.svg")
    if os.path.exists(logo_path):
        try:
            import cairosvg
            png_data = cairosvg.svg2png(url=logo_path, output_width=32, output_height=32)
            icon = tk.PhotoImage(data=png_data)
            return icon
        except Exception:
            pass
    return None

# 颜色配置
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

# 中文字体候选列表
CHINESE_FONTS = ["Microsoft YaHei", "PingFang SC", "SimHei", "Microsoft JhengHei", "STHeiti"]

def get_available_font(fallback_fonts, size, weight="normal"):
    """获取第一个可用的字体"""
    available = set(font.families())
    for f in fallback_fonts:
        if f in available:
            return (f, size, weight)
    return ("Segoe UI", size, weight)

class App:
    def __init__(self, root, config, api_client, db):
        self.root = root
        self.config = config
        self.api_client = api_client
        self.db = db
        self.running = True
        self.refresh_job = None

        # 设置全局字体（支持中文的回退字体）
        default_font = get_available_font(CHINESE_FONTS, 10)
        self.root.option_add("*Font", default_font)
        self.refreshing = False  # 防止重复刷新

        # 预计算常用的字体
        self.title_font = get_available_font(CHINESE_FONTS, 16, "bold")
        self.default_font = get_available_font(CHINESE_FONTS, 10)
        self.large_font = get_available_font(CHINESE_FONTS, 12)
        self.large_bold_font = get_available_font(CHINESE_FONTS, 12)

        self.setup_window()
        self.create_ui()
        self.models = []  # 模型列表
        self.current_model = None  # 当前选中的模型
        self.all_model_data = {}  # 所有模型的完整数据
        self.start_auto_refresh()

    def setup_window(self):
        """设置窗口"""
        self.root.title("MiniMax 配额监控")
        self.root.geometry("800x420")
        self.root.configure(bg=COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # 设置窗口图标
        icon = load_window_icon()
        if icon:
            self.root.iconphoto(True, icon)

    def create_ui(self):
        """创建UI"""
        # 标题栏
        header = tk.Frame(self.root, bg=COLORS["surface"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(header, text="MiniMax 配额监控", font=self.title_font,
                        bg=COLORS["surface"], fg=COLORS["text"])
        title.pack(side=tk.LEFT, padx=20)

        # 设置按钮
        settings_btn = tk.Button(header, text="设置", command=self.open_settings,
                                 bg=COLORS["primary"], fg=COLORS["text"], relief=tk.FLAT,
                                 padx=15, pady=5)
        settings_btn.pack(side=tk.RIGHT, padx=20)

        # 日志按钮
        logs_btn = tk.Button(header, text="日志", command=self.open_logs_folder,
                            bg=COLORS["surface"], fg=COLORS["text"], relief=tk.FLAT,
                            padx=15, pady=5)
        logs_btn.pack(side=tk.RIGHT, padx=5)

        # 趋势按钮
        trend_btn = tk.Button(header, text="趋势", command=self.open_trend_window,
                            bg=COLORS["surface"], fg=COLORS["text"], relief=tk.FLAT,
                            padx=15, pady=5)
        trend_btn.pack(side=tk.RIGHT, padx=5)

        # 刷新按钮
        refresh_btn = tk.Button(header, text="刷新", command=self.refresh_data,
                                bg=COLORS["primary"], fg=COLORS["text"], relief=tk.FLAT,
                                padx=15, pady=5)
        refresh_btn.pack(side=tk.RIGHT, padx=5)

        # 主内容区
        main = tk.Frame(self.root, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 状态卡片
        self.status_card = tk.Frame(main, bg=COLORS["surface"], relief=tk.RAISED, bd=0)
        self.status_card.pack(fill=tk.X, pady=(0, 20))

        status_label = tk.Label(self.status_card, text="当前状态", font=self.title_font,
                               bg=COLORS["surface"], fg=COLORS["text"])
        status_label.pack(anchor=tk.W, padx=16, pady=(16, 10))

        # 状态内容
        self.status_content = tk.Frame(self.status_card, bg=COLORS["surface"])
        self.status_content.pack(fill=tk.X, padx=16, pady=(0, 16))

        self.model_label = tk.Label(self.status_content, text="模型: -",
                                    font=self.large_font, bg=COLORS["surface"], fg=COLORS["text"])
        self.model_label.pack(anchor=tk.W)

        # 模型选择下拉框
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(self.status_content, textvariable=self.model_var,
                                         state="readonly", font=self.default_font)
        self.model_combo.pack(anchor=tk.W, pady=(5, 10))
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_selected)

        # 区间时间显示
        self.interval_time_label = tk.Label(self.status_content, text="区间: -",
                                           font=self.default_font, bg=COLORS["surface"], fg=COLORS["text_secondary"])
        self.interval_time_label.pack(anchor=tk.W)

        self.daily_label = tk.Label(self.status_content, text="当前区间: - / -",
                                    font=self.large_font, bg=COLORS["surface"], fg=COLORS["text"])
        self.daily_label.pack(anchor=tk.W, pady=5)

        # 剩余时间倒计时
        self.remain_time_label = tk.Label(self.status_content, text="剩余时间: -",
                                          font=self.large_font, bg=COLORS["surface"], fg=COLORS["success"])
        self.remain_time_label.pack(anchor=tk.W)

        self.weekly_label = tk.Label(self.status_content, text="本周: - / -",
                                     font=self.large_font, bg=COLORS["surface"], fg=COLORS["text"])
        self.weekly_label.pack(anchor=tk.W)

        self.time_label = tk.Label(self.status_content, text="最后更新: -",
                                   font=self.default_font, bg=COLORS["surface"], fg=COLORS["text_secondary"])
        self.time_label.pack(anchor=tk.W, pady=5)

        # 区间结束时间（用于倒计时）
        self.interval_end_time = None
        self.remain_job = None

        # 进度条
        self.daily_progress = ttk.Progressbar(self.status_card, length=300, mode='determinate')
        self.daily_progress.pack(fill=tk.X, padx=16, pady=(0, 10))

        self.weekly_progress = ttk.Progressbar(self.status_card, length=300, mode='determinate')
        self.weekly_progress.pack(fill=tk.X, padx=16, pady=(0, 16))

    def refresh_data(self):
        """刷新数据"""
        # 防止重复刷新
        if self.refreshing:
            return

        self.refreshing = True

        def fetch():
            data, error = self.api_client["fetch_remains"](
                self.config["cookie"],
                self.config["group_id"]
            )

            self.root.after(0, lambda: self.update_ui(data, error))

        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()

    def update_ui(self, data, error):
        """更新UI"""
        if error:
            self.model_label.config(text=f"错误: {error}", fg=COLORS["danger"])
            self.refreshing = False
            return

        if data and "model_remains" in data:
            # 存储所有模型数据
            self.all_model_data = {}
            for m in data["model_remains"]:
                model_name = m.get("model_name", "Unknown")
                self.all_model_data[model_name] = m

            # 更新模型列表
            self.models = list(self.all_model_data.keys())

            # 如果没有选中模型，默认选中第一个
            if not self.current_model or self.current_model not in self.models:
                self.current_model = self.models[0] if self.models else None

            # 更新下拉框
            self.model_combo['values'] = self.models
            if self.current_model:
                self.model_var.set(self.current_model)

            # 显示当前模型数据
            self.display_model_data()

        self.refreshing = False

    def display_model_data(self):
        """显示当前选中模型的数据"""
        if not self.current_model or self.current_model not in self.all_model_data:
            return

        model = self.all_model_data[self.current_model]
        model_name = model.get("model_name", "-")

        # 区间时间
        start_time = model.get("start_time", 0) // 1000  # 转为秒
        end_time = model.get("end_time", 0) // 1000      # 转为秒

        # 格式化时间
        start_str = datetime.fromtimestamp(start_time).strftime("%H:%M")
        end_str = datetime.fromtimestamp(end_time).strftime("%H:%M")

        # 注意：usage_count 是剩余次数，不是已用次数
        interval_total = model.get("current_interval_total_count", 0)
        interval_remain = model.get("current_interval_usage_count", 0)
        interval_used = interval_total - interval_remain  # 计算已用次数

        weekly_total = model.get("current_weekly_total_count", 0)
        weekly_remain = model.get("current_weekly_usage_count", 0)
        weekly_used = weekly_total - weekly_remain if weekly_total > 0 else 0

        self.model_label.config(text=f"模型: {model_name}")
        self.interval_time_label.config(text=f"区间: {start_str} - {end_str}")
        self.daily_label.config(text=f"当前区间: {interval_used} / {interval_total}")
        self.weekly_label.config(text=f"本周: {weekly_used} / {weekly_total}")
        self.time_label.config(text=f"最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 更新进度条
        daily_pct = (interval_used / interval_total * 100) if interval_total > 0 else 0
        weekly_pct = (weekly_used / weekly_total * 100) if weekly_total > 0 else 0

        self.daily_progress['value'] = daily_pct
        self.weekly_progress['value'] = weekly_pct

        # 设置倒计时
        self.interval_end_time = end_time
        self.update_remain_time()
        self.start_remain_timer()

    def on_model_selected(self, event):
        """模型选择变化回调"""
        self.current_model = self.model_var.get()
        self.display_model_data()

    def update_remain_time(self):
        """更新剩余时间显示"""
        if self.interval_end_time is None:
            return

        now = int(datetime.now().timestamp())
        remaining = self.interval_end_time - now

        if remaining <= 0:
            self.remain_time_label.config(text="剩余时间: 已过期", fg=COLORS["danger"])
        else:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            seconds = remaining % 60
            self.remain_time_label.config(text=f"剩余时间: {hours}小时{minutes}分{seconds}秒", fg=COLORS["success"])

    def start_remain_timer(self):
        """启动剩余时间倒计时定时器"""
        if self.remain_job:
            self.root.after_cancel(self.remain_job)

        def tick():
            self.update_remain_time()
            self.remain_job = self.root.after(1000, tick)

        tick()

    def start_auto_refresh(self):
        """启动自动刷新"""
        # 从配置获取刷新间隔（分钟）
        self.refresh_interval = self.config.get("refresh_interval", 15)

        def schedule():
            if self.running:
                self.refresh_data()
                # 刷新完成后立即计算下一次刷新
                delay = self.calculate_next_delay()
                self.refresh_job = self.root.after(delay, schedule)

        # 首次刷新 (延迟一点执行)
        self.root.after(1000, self.refresh_data)

        # 首次定时
        delay = self.calculate_next_delay()
        self.refresh_job = self.root.after(delay, schedule)

    def calculate_next_delay(self):
        """计算到下一次刷新的延迟（毫秒）"""
        now = datetime.now()

        if self.refresh_interval == 1:
            # 每分钟刷新：等待到下一分钟的0秒
            next_time = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        else:
            # 其他间隔：整10分刷新
            next_minute = ((now.minute // 10) + 1) * 10
            if next_minute >= 60:
                next_minute = 0
                next_hour = now.hour + 1
                if next_hour >= 24:
                    next_hour = 0
            else:
                next_hour = now.hour

            next_time = now.replace(hour=next_hour, minute=next_minute, second=0, microsecond=0)
            if next_time <= now:
                next_time = next_time + timedelta(minutes=10)

        delta = (next_time - now).total_seconds() * 1000
        return int(delta)

    def open_settings(self):
        """打开设置窗口"""
        SettingsWindow(self.root, self.config, self.default_font)

    def open_logs_folder(self):
        """打开logs文件夹"""
        logs_dir = os.path.join(PROJECT_ROOT, "logs")
        os.makedirs(logs_dir, exist_ok=True)

        # 跨平台打开文件夹
        if os.name == 'nt':  # Windows
            os.startfile(logs_dir)
        elif sys.platform == 'darwin':  # macOS
            subprocess.run(['open', logs_dir])
        else:  # Linux
            subprocess.run(['xdg-open', logs_dir])

    def open_trend_window(self):
        """打开趋势分析窗口"""
        TrendWindow(self.root, self.title_font, self.default_font, self.large_font)

    def on_close(self):
        """关闭窗口"""
        if self.config.get("minimize_to_tray", True):
            self.root.withdraw()
        else:
            self.stop()

    def stop(self):
        """停止应用"""
        self.running = False
        if self.refresh_job:
            self.root.after_cancel(self.refresh_job)
        if self.remain_job:
            self.root.after_cancel(self.remain_job)
        self.root.destroy()


class SettingsWindow:
    def __init__(self, parent, config, default_font):
        self.config = config
        self.default_font = default_font
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.geometry("400x350")
        self.window.configure(bg=COLORS["bg"])
        self.window.transient(parent)
        self.window.grab_set()

        self.create_ui()

    def create_ui(self):
        """创建设置UI"""
        main = tk.Frame(self.window, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Cookie
        tk.Label(main, text="HERTZ-SESSION Cookie:", bg=COLORS["bg"],
                fg=COLORS["text"], font=self.default_font).pack(anchor=tk.W)

        self.cookie_entry = tk.Entry(main, bg=COLORS["surface"], fg=COLORS["text"],
                                     insertbackground=COLORS["text"], font=self.default_font)
        self.cookie_entry.insert(0, self.config.get("cookie", ""))
        self.cookie_entry.pack(fill=tk.X, pady=(5, 15))

        # Group ID
        tk.Label(main, text="Group ID:", bg=COLORS["bg"],
                fg=COLORS["text"], font=self.default_font).pack(anchor=tk.W)

        self.group_id_entry = tk.Entry(main, bg=COLORS["surface"], fg=COLORS["text"],
                                       insertbackground=COLORS["text"], font=self.default_font)
        self.group_id_entry.insert(0, self.config.get("group_id", ""))
        self.group_id_entry.pack(fill=tk.X, pady=(5, 15))

        # 刷新间隔
        tk.Label(main, text="刷新间隔 (分钟):", bg=COLORS["bg"],
                fg=COLORS["text"], font=self.default_font).pack(anchor=tk.W)

        self.interval_var = tk.IntVar(value=self.config.get("refresh_interval", 15))
        intervals = [(1, "1 分钟"), (5, "5 分钟"), (15, "15 分钟"), (30, "30 分钟"), (60, "1 小时")]

        for minutes, label in intervals:
            rb = tk.Radiobutton(main, text=label, variable=self.interval_var,
                               value=minutes, bg=COLORS["bg"], fg=COLORS["text"],
                               selectcolor=COLORS["surface"], font=self.default_font)
            rb.pack(anchor=tk.W)

        # 按钮
        btn_frame = tk.Frame(main, bg=COLORS["bg"])
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))

        save_btn = tk.Button(btn_frame, text="保存", command=self.save,
                            bg=COLORS["primary"], fg=COLORS["text"],
                            relief=tk.FLAT, padx=20, pady=8, font=self.default_font)
        save_btn.pack(side=tk.RIGHT)

        cancel_btn = tk.Button(btn_frame, text="取消", command=self.window.destroy,
                              bg=COLORS["surface"], fg=COLORS["text"],
                              relief=tk.FLAT, padx=20, pady=8, font=self.default_font)
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def save(self):
        """保存设置"""
        from config_manager import save_config

        self.config["cookie"] = self.cookie_entry.get().strip()
        self.config["group_id"] = self.group_id_entry.get().strip()
        self.config["refresh_interval"] = self.interval_var.get()

        save_config(self.config)
        self.window.destroy()
        messagebox.showinfo("提示", "设置已保存，需要重启应用才能生效")


class TrendWindow:
    def __init__(self, parent, title_font, default_font, large_font):
        self.window = tk.Toplevel(parent)
        self.title_font = title_font
        self.default_font = default_font
        self.large_font = large_font
        self.window.title("使用趋势分析")
        self.window.geometry("900x600")
        self.window.configure(bg=COLORS["bg"])
        self.window.transient(parent)

        # 导入 matplotlib
        import matplotlib
        matplotlib.use('TkAgg')
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from matplotlib.figure import Figure
        import matplotlib.font_manager as fm

        # 配置中文字体
        chinese_fonts = ["Microsoft YaHei", "PingFang SC", "SimHei", "Microsoft JhengHei", "STHeiti"]
        available_fonts = set(f.name for f in fm.fontManager.ttflist)
        for font_name in chinese_fonts:
            if font_name in available_fonts:
                matplotlib.rcParams['font.sans-serif'] = [font_name]
                break
        matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

        self.Figure = Figure
        self.FigureCanvasTkAgg = FigureCanvasTkAgg

        self.create_ui()
        self.load_data()

    def create_ui(self):
        """创建UI"""
        main = tk.Frame(self.window, bg=COLORS["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 顶部控制栏
        control_frame = tk.Frame(main, bg=COLORS["bg"])
        control_frame.pack(fill=tk.X, pady=(0, 10))

        # 模型选择
        tk.Label(control_frame, text="选择模型:", bg=COLORS["bg"],
                fg=COLORS["text"], font=self.default_font).pack(side=tk.LEFT)

        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(control_frame, textvariable=self.model_var,
                                         state="readonly", font=self.default_font, width=25)
        self.model_combo.pack(side=tk.LEFT, padx=10)
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_selected)

        # 刷新按钮
        refresh_btn = tk.Button(control_frame, text="刷新", command=self.load_data,
                              bg=COLORS["primary"], fg=COLORS["text"],
                              relief=tk.FLAT, padx=15, pady=5, font=self.default_font)
        refresh_btn.pack(side=tk.LEFT, padx=10)

        # 图表区域
        self.chart_frame = tk.Frame(main, bg=COLORS["surface"])
        self.chart_frame.pack(fill=tk.BOTH, expand=True)

        # 状态标签
        self.status_label = tk.Label(main, text="", bg=COLORS["bg"],
                                   fg=COLORS["text_secondary"], font=self.default_font)
        self.status_label.pack(pady=5)

    def load_data(self):
        """加载logs数据"""
        logs_dir = os.path.join(PROJECT_ROOT, "logs")

        if not os.path.exists(logs_dir):
            self.status_label.config(text="日志目录不存在")
            return

        # 收集所有日志文件
        log_files = []
        for root, dirs, files in os.walk(logs_dir):
            for f in sorted(files):
                if f.endswith('.json'):
                    log_files.append(os.path.join(root, f))

        if not log_files:
            self.status_label.config(text="没有找到日志文件")
            return

        # 解析日志数据
        self.model_data = {}  # {model_name: [(timestamp, used_count), ...]}

        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if "model_remains" not in data:
                    continue

                # 从文件名提取时间
                rel_path = os.path.relpath(log_file, logs_dir)
                parts = rel_path.replace('.json', '').split(os.sep)
                if len(parts) >= 3:
                    date_str = parts[0]  # YYYY-MM-DD
                    hour_str = parts[1]   # HH
                    minute_str = parts[2]  # MM
                    try:
                        timestamp = datetime.strptime(f"{date_str} {hour_str} {minute_str}", "%Y-%m-%d %H %M").timestamp() * 1000
                    except:
                        continue
                else:
                    continue

                for model in data["model_remains"]:
                    model_name = model.get("model_name", "Unknown")
                    interval_total = model.get("current_interval_total_count", 0)
                    interval_remain = model.get("current_interval_usage_count", 0)
                    interval_used = interval_total - interval_remain

                    if model_name not in self.model_data:
                        self.model_data[model_name] = []

                    self.model_data[model_name].append((timestamp, interval_used))

            except Exception as e:
                continue

        # 按时间排序
        for model_name in self.model_data:
            self.model_data[model_name].sort(key=lambda x: x[0])

        # 更新模型列表
        models = list(self.model_data.keys())
        self.model_combo['values'] = models

        if models:
            self.model_var.set(models[0])
            self.status_label.config(text=f"共加载 {len(log_files)} 个日志文件, {len(models)} 个模型")
            self.on_model_selected()
        else:
            self.status_label.config(text="没有有效的日志数据")

    def on_model_selected(self, event=None):
        """模型选择变化"""
        model_name = self.model_var.get()
        if model_name not in self.model_data:
            return

        # 清除旧图表
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        data = self.model_data[model_name]
        if not data:
            return

        # 创建图表
        fig = self.Figure(figsize=(8, 5), facecolor=COLORS["surface"])
        ax = fig.add_subplot(111)

        # 设置背景色
        ax.set_facecolor("#1E293B")

        # 提取时间和数据
        times = [datetime.fromtimestamp(t/1000) for t, _ in data]
        values = [v for _, v in data]

        # 绘制曲线
        ax.plot(times, values, color="#2563EB", linewidth=2, marker='o', markersize=4)

        # 设置标签
        ax.set_title(f"{model_name} - 使用量趋势", color="#F8FAFC", fontsize=12)
        ax.set_xlabel("时间", color="#94A3B8")
        ax.set_ylabel("已使用次数", color="#94A3B8")

        # 设置刻度颜色
        ax.tick_params(colors="#94A3B8")
        for spine in ax.spines.values():
            spine.set_color("#475569")

        # 旋转x轴标签
        fig.autofmt_xdate()

        # 调整边距
        fig.tight_layout()

        # 创建画布
        canvas = self.FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
