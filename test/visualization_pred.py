from PIL import Image, ImageDraw, ImageFont
import random
import os
import json
import argparse

def poly2bbox(poly):
    """将多边形坐标转换为边界框"""
    L = poly[0]
    U = poly[1]
    R = poly[2]
    D = poly[5]
    L, R = min(L, R), max(L, R)
    U, D = min(U, D), max(U, D)
    bbox = [L, U, R, D]
    return bbox

def get_color():
    """生成随机颜色"""
    red = random.randint(0, 255)
    green = random.randint(0, 255)
    blue = random.randint(0, 255)
    return (blue, green, red)

# 颜色映射：根据不同类别使用不同颜色
color_map = {
    'table': 'orange',
    'figure': 'green',
    'text_block': 'blue',
    'text_span': '#07689f',
    'equation_inline': '#590d82',
    'equation_ignore': '#769fcd'
}

def visualize_predictions(json_path, img_folder, output_folder, max_samples=None):
    """
    可视化预测结果

    Args:
        json_path: 预测结果JSON文件路径
        img_folder: 图片文件夹路径
        output_folder: 输出文件夹路径
        max_samples: 最大可视化样本数，None表示全部
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        samples = json.load(f)

    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)

    processed_count = 0

    for i, sample in enumerate(samples):
        if max_samples and processed_count >= max_samples:
            break

        img_path = sample['page_info']['image_path']
        full_img_path = os.path.join(img_folder, img_path)

        # 检查图片是否存在
        if not os.path.exists(full_img_path):
            print(f'图片不存在: {full_img_path}')
            continue

        print(f'处理: {img_path}')

        # 打开图片
        img = Image.open(full_img_path)
        draw = ImageDraw.Draw(img)

        # 尝试加载中文字体，如果失败则使用默认字体
        try:
            # Windows 中文字体路径
            font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 20)
            font_small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 14)
        except:
            try:
                # Linux 中文字体路径
                font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 20)
                font_small = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 14)
            except:
                font = None
                font_small = None

        for anno in sample['layout_dets']:
            # 跳过不需要可视化的类别
            if 'mask' in anno['category_type'] or anno['category_type'] == 'abandon':
                continue
            if anno['category_type'] == 'table' and anno['attribute'].get('include_photo'):
                continue

            bbox = poly2bbox(anno['poly'])

            # 获取或生成颜色
            if not color_map.get(anno['category_type']):
                color = get_color()
                color_map[anno['category_type']] = color
            color = color_map[anno['category_type']]

            # 绘制检测框
            draw.rectangle(bbox, outline=color, width=3)

            # 显示预测文本（如果有pred字段）
            if 'pred' in anno and anno['pred'] != -1:
                pred_text = str(anno['pred'])
                # 在框上方显示预测文本
                text_height = 20
                text_y = max(0, bbox[1] - text_height)
                text_bottom = min(text_y + text_height, bbox[1])
                # 确保矩形坐标有效 (y1 >= y0)
                if text_bottom > text_y:
                    draw.rectangle([bbox[0], text_y, bbox[0] + len(pred_text) * 12, text_bottom],
                                 fill=color, outline=color)
                    draw.text((bbox[0] + 2, text_y), pred_text, fill='white', font=font_small)

            # 显示真实文本（如果有text字段）
            if 'text' in anno and anno['text'] != -1:
                text = str(anno['text'])
                # 在框下方显示真实文本
                text_y = bbox[3] + 2
                draw.text((bbox[0], text_y), f'GT: {text}', fill='red', font=font_small)

            # 处理line_with_spans（文本片段）
            if anno.get('line_with_spans') and anno['line_with_spans'] != -1:
                for span in anno['line_with_spans']:
                    bbox = poly2bbox(span['poly'])
                    if not color_map.get(span['category_type']):
                        color = get_color()
                        color_map[span['category_type']] = color
                    draw.rectangle(bbox, outline=color_map[span['category_type']], width=3)

        # 保存可视化结果
        img_name = os.path.splitext(os.path.basename(img_path))[0] + '_vis.jpg'
        output_path = os.path.join(output_folder, img_name)
        img.convert('RGB').save(output_path)
        print(f'已保存: {output_path}')

        processed_count += 1

    print(f'完成! 共处理 {processed_count} 张图片')
    print(f'输出目录: {output_folder}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='可视化OCR预测结果')
    parser.add_argument('--json', '-j', type=str,
                       default='test/model_outputs/drawings_text_ocr.json',
                       help='预测结果JSON文件路径')
    parser.add_argument('--img_folder', '-i', type=str,
                       default='E:/work/图纸解析/test',
                       help='图片文件夹路径')
    parser.add_argument('--output', '-o', type=str,
                       default='test/visualization_output',
                       help='输出文件夹路径')
    parser.add_argument('--max_samples', '-m', type=int, default=None,
                       help='最大可视化样本数')

    args = parser.parse_args()

    visualize_predictions(args.json, args.img_folder, args.output, args.max_samples)