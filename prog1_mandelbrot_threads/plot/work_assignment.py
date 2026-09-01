import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# 高对比度线程颜色盘（RGBA）
THREAD_COLORS = [
    (255, 65, 54),   # Thread 0: 红色
    (46, 204, 64),   # Thread 1: 绿色
    (0, 116, 217),   # Thread 2: 蓝色
    (255, 133, 27),  # Thread 3: 橙色
    (177, 13, 201),  # Thread 4: 紫色
    (57, 204, 204),  # Thread 5: 青色
    (255, 220, 0),   # Thread 6: 黄色
    (240, 18, 190),  # Thread 7: 粉色
]

def load_font(size=14):
    """加载系统字体，若未找到则回退至默认字体"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def visualize_block(img_rgba, num_threads, alpha=50, border_width=3):
    """绘制块状（Block）划分：为每个线程绘制连续的水平矩形框与遮罩"""
    width, height = img_rgba.size
    img_out = img_rgba.copy()
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    font = load_font(14)
    
    num_row = (height - 1) // num_threads + 1
    
    for t in range(num_threads):
        start_row = t * num_row
        end_row = min(start_row + num_row, height)
        if start_row >= height:
            break
            
        color = THREAD_COLORS[t % len(THREAD_COLORS)]
        fill_color = color + (alpha,)
        border_color = color + (255,)
        
        # 绘制半透明覆盖层
        draw_overlay.rectangle([0, start_row, width, end_row], fill=fill_color)
        
        # 绘制线程边界外框
        draw_overlay.rectangle([0, start_row, width - 1, end_row - 1], outline=border_color, width=border_width)
        
        font = load_font(24)

        label = f"Thread {t}"
        bx0, by0 = 12, start_row + 8
        bw, bh = 130, 36

        draw_overlay.rectangle([bx0, by0, bx0 + bw, by0 + bh], fill=(0, 0, 0, 200), outline=border_color, width=1)
        draw_overlay.text((bx0 + 10, by0 + 4), label, fill=(255, 255, 255, 255), font=font)
        
    return Image.alpha_composite(img_out, overlay)

def visualize_round_robin(img_rgba, num_threads, alpha=90, draw_zoom=True, zoom_factor=6):
    """绘制交错（Round-Robin）划分：每行按 threadId 循环染色，并生成右下角局部放大图"""
    width, height = img_rgba.size
    img_out = img_rgba.copy()
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    
    # 1. 逐行叠加线程颜色半透明线条
    for r in range(height):
        t = r % num_threads
        color = THREAD_COLORS[t % len(THREAD_COLORS)]
        fill_color = color + (alpha,)
        draw_overlay.line([(0, r), (width, r)], fill=fill_color, width=1)
        
    # 2. 左侧边缘绘制高亮线程指示条 (宽度 24px)
    bar_w = 24
    for r in range(height):
        t = r % num_threads
        color = THREAD_COLORS[t % len(THREAD_COLORS)] + (255,)
        draw_overlay.line([(0, r), (bar_w, r)], fill=color, width=1)
    draw_overlay.rectangle([0, 0, bar_w - 1, height - 1], outline=(255, 255, 255, 255), width=1)

    res = Image.alpha_composite(img_out, overlay)
    
    # 3. 绘制局部放大框（Zoom Callout），解决全图状态下交错细线密集的问题
    if draw_zoom:
        zoom_factor = 10  
        
        crop_h = min(num_threads * 4, height // 6)
        crop_w = min(100, width // 5)
        
        cx, cy = width // 2, height // 2
        crop_box = (cx, cy, cx + crop_w, cy + crop_h)
        
        cropped = res.crop(crop_box)
        zoomed = cropped.resize((crop_w * zoom_factor, crop_h * zoom_factor), resample=Image.NEAREST)
        
        zoom_w, zoom_h = zoomed.size
        draw_zoom_img = ImageDraw.Draw(zoomed)
        draw_zoom_img.rectangle([0, 0, zoom_w - 1, zoom_h - 1], outline=(255, 255, 255, 255), width=4)
        
        zoom_font = load_font(22)
        
        tag_w, tag_h = 260, 36
        draw_zoom_img.rectangle([8, 8, 8 + tag_w, 8 + tag_h], fill=(0, 0, 0, 220), outline=(255, 255, 255, 255), width=1)
        draw_zoom_img.text((16, 12), "Zoom: Round-Robin", fill=(255, 255, 255, 255), font=zoom_font)
        
        pos_x = width - zoom_w - 20
        pos_y = height - zoom_h - 20
        res.paste(zoomed, (pos_x, pos_y))
        
        draw_res = ImageDraw.Draw(res)
        draw_res.rectangle(crop_box, outline=(255, 255, 0, 255), width=3)
        draw_res.line([(cx + crop_w, cy + crop_h), (pos_x, pos_y)], fill=(255, 255, 0, 200), width=2)

    return res

def main():
    parser = argparse.ArgumentParser(description="Mandelbrot 多线程任务划分可视化工具 (.ppm)")
    parser.add_argument("-i", "--input", default="mandelbrot-thread.ppm", help="输入 .ppm 文件路径")
    parser.add_argument("-o", "--output", default="plot/work-assignment.ppm", help="输出 .ppm 文件路径")
    parser.add_argument("-n", "--num_threads", type=int, default=4, help="线程数量 (默认: 4)")
    parser.add_argument("-m", "--mode", choices=["block", "round-robin", "both"], default="block", 
                        help="可视化划分模式: block (分块), round-robin (交错), both (生成两个文件)")
    parser.add_argument("-a", "--alpha", type=int, default=60, help="透明度 0-255 (默认: 60)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误: 找不到输入文件 {args.input}")
        sys.exit(1)

    print(f"正在读取 {args.input} ...")
    img = Image.open(args.input).convert("RGBA")

    if args.mode in ["block", "both"]:
        out_path = args.output if args.mode == "block" else args.output.replace(".ppm", "_block.ppm")
        print(f"生成 Block 划分可视化 ({args.num_threads} 线程) -> {out_path}")
        res_block = visualize_block(img, args.num_threads, alpha=args.alpha)
        res_block.convert("RGB").save(out_path)

    if args.mode in ["round-robin", "both"]:
        out_path = args.output if args.mode == "round-robin" else args.output.replace(".ppm", "_rr.ppm")
        print(f"生成 Round-Robin 划分可视化 ({args.num_threads} 线程) -> {out_path}")
        res_rr = visualize_round_robin(img, args.num_threads, alpha=args.alpha)
        res_rr.convert("RGB").save(out_path)

    print("处理完成！")

if __name__ == "__main__":
    main()
