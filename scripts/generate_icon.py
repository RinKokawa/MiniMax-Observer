"""
SVG 转 ICO 工具
将 SVG 图标转换为 Windows ICO 格式
"""
import os
import io
import cairosvg
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
svg_path = os.path.join(PROJECT_ROOT, "src", "observer-logo.svg")
ico_path = os.path.join(PROJECT_ROOT, "MiniMaxMonitor.ico")

# ICO 文件需要多个尺寸
sizes = [16, 32, 48, 256]
images = []

for size in sizes:
    png_data = cairosvg.svg2png(url=svg_path, output_width=size, output_height=size)
    img = Image.open(io.BytesIO(png_data))
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    images.append(img)

# 保存为 ICO（多尺寸）
images[0].save(
    ico_path,
    format='ICO',
    sizes=[(s, s) for s in sizes],
    append_images=images[1:]
)

print(f"图标已生成: {ico_path}")
