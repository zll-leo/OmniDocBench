#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将PPOCRLabel格式的表格标注转换为OmniDocBench格式
"""

import json
import re
import argparse
from typing import Dict, List, Any


def contains_chinese(text: str) -> bool:
    """检测文本是否包含中文字符"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def detect_language(cells: List[Dict]) -> str:
    """检测表格语言"""
    all_text = ""
    for cell in cells:
        if 'tokens' in cell:
            all_text += ''.join(cell['tokens'])

    if contains_chinese(all_text):
        return "table_simplified_chinese"
    else:
        return "table_en"


def has_merged_cells(gt_html: str) -> bool:
    """检测表格是否有合并单元格"""
    return 'colspan' in gt_html or 'rowspan' in gt_html


def calculate_table_bbox(cells: List[Dict]) -> List[float]:
    """
    计算表格的边界框（四边形）
    返回: [x1, y1, x2, y2, x3, y3, x4, y4]
    """
    if not cells:
        return [-1] * 8

    # 收集所有坐标点
    all_x = []
    all_y = []

    for cell in cells:
        if 'bbox' in cell and len(cell['bbox']) == 4:
            bbox = cell['bbox']
            # bbox 格式: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            all_x.extend([bbox[0][0], bbox[1][0], bbox[2][0], bbox[3][0]])
            all_y.extend([bbox[0][1], bbox[1][1], bbox[2][1], bbox[3][1]])

    if not all_x or not all_y:
        return [-1] * 8

    min_x = min(all_x)
    max_x = max(all_x)
    min_y = min(all_y)
    max_y = max(all_y)

    # 四边形坐标：左上 → 右上 → 右下 → 左下
    return [min_x, min_y, max_x, min_y, max_x, max_y, min_x, max_y]


def calculate_table_size(poly: List[float]) -> Dict[str, float]:
    """
    根据边界框计算表格尺寸
    返回: {"width": float, "height": float}
    """
    if len(poly) != 8 or poly == [-1] * 8:
        return {"width": -1, "height": -1}

    min_x, min_y, max_x, max_y = poly[0], poly[1], poly[4], poly[5]
    width = max_x - min_x
    height = max_y - min_y

    return {"width": width, "height": height}


def convert_single_item(ppocr_item: Dict) -> Dict:
    """
    转换单个PPOCRLabel标注项为OmniDocBench格式

    Args:
        ppocr_item: PPOCRLabel格式的单个标注项

    Returns:
        OmniDocBench格式的单个标注项
    """
    filename = ppocr_item.get('filename', '')
    cells = ppocr_item.get('html', {}).get('cells', [])
    gt_html = ppocr_item.get('gt', '')

    # 计算表格边界框
    poly = calculate_table_bbox(cells)

    # 计算表格尺寸
    size = calculate_table_size(poly)

    # 检测语言
    language = detect_language(cells)

    # 检测合并单元格
    with_span = has_merged_cells(gt_html)

    # 构建OmniDocBench格式
    omnidoc_item = {
        "layout_dets": [
            {
                "category_type": "table",
                "poly": poly,
                "html": gt_html,
                "latex": -1,  # 暂不支持，设为-1
                "attribute": {
                    "table_layout": "horizontal",
                    "with_span": with_span,
                    "line": "fewer_line",
                    "language": language,
                    "include_equation": False,
                    "include_photo": False,
                    "include_background": False,
                    "with_structured_text": False
                },
                "table_edit_status": "good"
            }
        ],
        "extra": {
            "relation": []
        },
        "page_info": {
            "page_attribute": {
                "data_source": -1,
                "language": -1,
                "layout": -1,
                "special_issue": []
            },
            "page_no": -1,
            "height": size["height"],
            "width": size["width"],
            "image_path": filename
        }
    }

    return omnidoc_item


def convert_ppocr_tabel_label_to_omnidoc(input_file: str, output_file: str) -> None:
    """
    将PPOCRLabel的table标注格式转换为OmniDocBench格式

    Args:
        input_file: PPOCRLabel格式的输入文件路径
        output_file: OmniDocBench格式的输出文件路径
    """
    results = []

    # 读取PPOCRLabel文件
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue

            try:
                ppocr_item = json.loads(line)
                omnidoc_item = convert_single_item(ppocr_item)
                results.append(omnidoc_item)
            except json.JSONDecodeError as e:
                print(f"警告: 第{line_num}行JSON解析失败: {e}")
                print(f"  内容: {line[:100]}...")
            except Exception as e:
                print(f"警告: 第{line_num}行转换失败: {e}")
                print(f"  内容: {line[:100]}...")

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"\n转换完成！")
    print(f"  输入文件: {input_file}")
    print(f"  输出文件: {output_file}")
    print(f"  成功转换: {len(results)} 条记录")


def main():
    parser = argparse.ArgumentParser(
        description='将PPOCRLabel格式的表格标注转换为OmniDocBench格式'
    )
    parser.add_argument(
        '-i', '--input',
        default='./test/dataset_transform/gt.txt',
        help='PPOCRLabel格式的输入文件路径 (默认: ./test/dataset_transform/gt.txt)'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='OmniDocBench格式的输出文件路径'
    )

    args = parser.parse_args()

    convert_ppocr_tabel_label_to_omnidoc(args.input, args.output)


if __name__ == '__main__':
    main()