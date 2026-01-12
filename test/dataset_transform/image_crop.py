"""
图像裁剪脚本
支持:
- 指定多个ROI区域进行裁剪
- 批量处理文件夹中的所有图片
- 自定义输入/输出文件夹
"""

import argparse
from pathlib import Path
from PIL import Image
from typing import List, Tuple


def parse_roi(roi_str: str) -> Tuple[int, int, int, int]:
    """
    解析ROI字符串为坐标元组
    格式: x1,y1,x2,y2 (左上角x, 左上角y, 右下角x, 右下角y)
    """
    try:
        coords = [int(x.strip()) for x in roi_str.split(',')]
        if len(coords) != 4:
            raise ValueError("ROI必须包含4个坐标值")
        return tuple(coords)
    except Exception as e:
        raise ValueError(f"无效的ROI格式 '{roi_str}': {e}")


def crop_image(image_path: Path, rois: List[Tuple[int, int, int, int]], 
               output_dir: Path) -> List[Path]:
    """
    裁剪单张图片的多个ROI区域
    
    Args:
        image_path: 输入图片路径
        rois: ROI区域列表，每个ROI为(x1, y1, x2, y2)
        output_dir: 输出目录
    
    Returns:
        保存的图片路径列表
    """
    saved_paths = []
    
    try:
        with Image.open(image_path) as img:
            img_width, img_height = img.size
            
            for idx, roi in enumerate(rois):
                x1, y1, x2, y2 = roi
                
                # 验证ROI边界
                if x1 < 0 or y1 < 0 or x2 > img_width or y2 > img_height:
                    print(f"警告: ROI {roi} 超出图片边界 ({img_width}x{img_height})，将自动调整")
                    x1 = max(0, x1)
                    y1 = max(0, y1)
                    x2 = min(img_width, x2)
                    y2 = min(img_height, y2)
                
                if x1 >= x2 or y1 >= y2:
                    print(f"警告: 跳过无效ROI {roi}")
                    continue
                
                # 裁剪图片
                cropped = img.crop((x1, y1, x2, y2))
                
                # 构建输出路径
                stem = image_path.stem
                suffix = image_path.suffix
                
                output_dir.mkdir(parents=True, exist_ok=True)
                
                if len(rois) > 1:
                    output_name = f"{stem}_roi{idx+1}{suffix}"
                else:
                    output_name = f"{stem}_cropped{suffix}"
                
                output_path = output_dir / output_name
                cropped.save(output_path)
                saved_paths.append(output_path)
                print(f"已保存: {output_path}")
                
    except Exception as e:
        print(f"处理图片 {image_path} 时出错: {e}")
    
    return saved_paths


def get_image_files(input_dir: Path) -> List[Path]:
    """
    获取目录中的所有图片文件
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(input_dir.glob(f"*{ext}"))
        image_files.extend(input_dir.glob(f"*{ext.upper()}"))
    
    return sorted(set(image_files))


def batch_crop(input_dir: Path, output_dir: Path, 
               rois: List[Tuple[int, int, int, int]]) -> None:
    """
    批量裁剪文件夹中的所有图片
    """
    image_files = get_image_files(input_dir)
    
    if not image_files:
        print(f"在 {input_dir} 中未找到图片文件")
        return
    
    print(f"找到 {len(image_files)} 个图片文件")
    print(f"将应用 {len(rois)} 个ROI区域")
    print("-" * 50)
    
    total_saved = 0
    for image_path in image_files:
        saved = crop_image(image_path, rois, output_dir)
        total_saved += len(saved)
    
    print("-" * 50)
    print(f"处理完成! 共保存 {total_saved} 个裁剪图片")


def interactive_mode():
    """
    交互式模式
    """
    print("=" * 50)
    print("图像裁剪工具 - 交互式模式")
    print("=" * 50)
    
    # 获取输入目录
    input_dir = input("请输入图片所在文件夹路径: ").strip().strip('"')
    input_dir = Path(input_dir)
    if not input_dir.exists():
        print(f"错误: 目录 {input_dir} 不存在")
        return
    
    # 获取输出目录
    output_dir = input("请输入输出文件夹路径: ").strip().strip('"')
    output_dir = Path(output_dir)
    
    # 获取ROI
    print("\n请输入ROI区域 (格式: x1,y1,x2,y2)")
    print("输入多个ROI时，每行输入一个，输入空行结束")
    
    rois = []
    while True:
        roi_input = input(f"ROI {len(rois)+1}: ").strip()
        if not roi_input:
            if rois:
                break
            else:
                print("至少需要输入一个ROI")
                continue
        try:
            roi = parse_roi(roi_input)
            rois.append(roi)
            print(f"  已添加: ({roi[0]}, {roi[1]}) -> ({roi[2]}, {roi[3]})")
        except ValueError as e:
            print(f"  错误: {e}")
    
    print("\n开始处理...")
    batch_crop(input_dir, output_dir, rois)


def main():
    parser = argparse.ArgumentParser(
        description="图像裁剪工具 - 支持多ROI区域批量处理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单个ROI
  python image_crop.py -i ./images -o ./output -r 100,100,500,500
  
  # 多个ROI
  python image_crop.py -i ./images -o ./output -r 0,0,200,200 -r 200,200,400,400
  
  # 交互式模式
  python image_crop.py --interactive
        """
    )
    
    parser.add_argument('-i', '--input', type=str, help='输入图片文件夹路径')
    parser.add_argument('-o', '--output', type=str, help='输出文件夹路径')
    parser.add_argument('-r', '--roi', type=str, action='append',
                        help='ROI区域，格式: x1,y1,x2,y2 (可指定多个)')
    parser.add_argument('--interactive', action='store_true',
                        help='使用交互式模式')
    
    args = parser.parse_args()
    
    # 交互式模式
    if args.interactive or (not args.input and not args.output and not args.roi):
        interactive_mode()
        return
    
    # 命令行模式验证
    if not args.input:
        parser.error("请指定输入文件夹 (-i)")
    if not args.output:
        parser.error("请指定输出文件夹 (-o)")
    if not args.roi:
        parser.error("请至少指定一个ROI区域 (-r)")
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    
    if not input_dir.exists():
        print(f"错误: 输入目录 {input_dir} 不存在")
        return
    
    # 解析所有ROI
    rois = []
    for roi_str in args.roi:
        try:
            rois.append(parse_roi(roi_str))
        except ValueError as e:
            print(f"错误: {e}")
            return
    
    batch_crop(input_dir, output_dir, rois)


if __name__ == "__main__":
    main()