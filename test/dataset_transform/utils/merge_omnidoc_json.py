#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并两个OmniDocBench格式的JSON文件
将表格标注和OCR文本标注的JSON文件合并为一个
"""

import json
import argparse
from typing import List, Dict, Any


def load_json_file(file_path: str) -> List[Dict]:
    """
    加载JSON文件

    Args:
        file_path: JSON文件路径

    Returns:
        JSON数据列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except FileNotFoundError:
        print(f"错误: 文件不存在 - {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"错误: JSON解析失败 - {file_path}: {e}")
        return []


def merge_json_files(file1: str, file2: str, output: str) -> None:
    """
    合并两个JSON文件

    Args:
        file1: 第一个JSON文件路径
        file2: 第二个JSON文件路径
        output: 输出文件路径
    """
    # 加载两个JSON文件
    data1 = load_json_file(file1)
    data2 = load_json_file(file2)

    # 合并数据
    merged_data = data1 + data2

    # 写入输出文件
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)

    print(f"合并完成！")
    print(f"  文件1: {file1} ({len(data1)} 条记录)")
    print(f"  文件2: {file2} ({len(data2)} 条记录)")
    print(f"  输出: {output} ({len(merged_data)} 条记录)")


def main():
    parser = argparse.ArgumentParser(
        description='合并两个OmniDocBench格式的JSON文件'
    )
    parser.add_argument(
        '-f1', '--file1',
        default='./test/dataset_transform/labels/tabelLabel2OmniDocBench.json',
        help='第一个JSON文件路径 (表格标注)'
    )
    parser.add_argument(
        '-f2', '--file2',
        default='./test/dataset_transform/labels/OCRLabel2OmniDocBench.json',
        help='第二个JSON文件路径 (OCR文本标注)'
    )
    parser.add_argument(
        '-o', '--output',
        default='./test/dataset_transform/labels/OmniDocBench_merged.json',
        help='输出文件路径'
    )

    args = parser.parse_args()

    merge_json_files(args.file1, args.file2, args.output)


if __name__ == '__main__':
    main()