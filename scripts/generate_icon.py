"""
SVG 转 ICO 工具
将 SVG 图标转换为 Windows ICO 格式（多尺寸）
"""
import os
import io
import cairosvg
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
svg_path = os.path.join(PROJECT_ROOT, "src", "observer-logo.svg")
ico_path = os.path.join(PROJECT_ROOT, "MiniMaxMonitor.ico")

# ICO 文件尺寸
sizes = [16, 32, 48, 256]


def build_ico(png_images):
    """
    手动构建 ICO 文件。
    ICO 格式支持直接嵌入 PNG 数据（自 Windows XP 起），
    这样可以保留完整的透明度和高清细节。
    """
    entries = []
    data_offset = 6 + len(png_images) * 16  # 头部6字节 + 每项16字节

    for png_data, size in png_images:
        w = h = size
        png_size = len(png_data)
        # ICO 目录项（16字节）：
        # 字节0: 宽度(像素)，0表示256
        # 字节1: 高度(像素)，0表示256
        # 字节2: 调色板颜色数（0表示不限制）
        # 字节3: 保留（0）
        # 字节4-5: 颜色平面数（1）
        # 字节6-7: 每个像素的位数（32 for RGBA PNG）
        # 字节8-11: 图像数据大小
        # 字节12-15: 图像数据偏移量
        entry = bytes([
            0 if w >= 256 else w,   # 宽度，256用0表示
            0 if h >= 256 else h,   # 高度，256用0表示
            0,                        # 调色板
            0,                        # 保留
            1, 0,                     # 颜色平面
            32, 0,                    # 每像素位数
        ])
        entry += png_size.to_bytes(4, 'little')          # 数据大小
        entry += data_offset.to_bytes(4, 'little')      # 数据偏移
        entries.append(entry)
        data_offset += png_size

    # ICO 文件头（6字节）：reserved(2) + type(2) + count(2)
    # type=1 表示 ICO 格式
    header = (0).to_bytes(2, 'little')                     # 保留，0
    header += (1).to_bytes(2, 'little')                    # 类型，1=ICO
    header += len(png_images).to_bytes(2, 'little')        # 图像数量

    # 组装完整 ICO
    with open(ico_path, 'wb') as f:
        f.write(header)
        for entry in entries:
            f.write(entry)
        for png_data, _ in png_images:
            f.write(png_data)


def generate_ico():
    """生成 ICO 文件"""
    if not os.path.exists(svg_path):
        print(f"[ERROR] SVG file not found: {svg_path}")
        return

    png_images = []
    for size in sizes:
        png_data = cairosvg.svg2png(url=svg_path, output_width=size, output_height=size)
        img = Image.open(io.BytesIO(png_data))
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        # 保存为 PNG bytes
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        png_images.append((buf.getvalue(), size))

    build_ico(png_images)

    size_kb = os.path.getsize(ico_path) / 1024
    print(f"[OK] Icon generated: {ico_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    import sys
    quiet = '-q' in sys.argv
    generate_ico()
