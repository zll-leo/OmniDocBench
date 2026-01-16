import os
import json
import numpy

from PIL import Image, ImageOps
from paddleocr import PaddleOCR, PPStructureV3
# from paddleocr.tools.infer import draw_ocr

# OCR模型缓存，避免重复加载
_ocr_models = {}

def get_ocr_model(lan: str):
    """获取OCR模型实例，使用缓存避免重复加载"""
    if lan not in _ocr_models:
        if lan == 'text_simplified_chinese':
            _ocr_models[lan] = PPStructureV3(use_textline_orientation=False, lang='ch')
        elif lan == 'text_english':
            _ocr_models[lan] = PPStructureV3(use_textline_orientation=False, lang='en')
        else:
            _ocr_models[lan] = PPStructureV3(use_textline_orientation=False)
    return _ocr_models[lan]

def test_paddle(img: Image, lan: str):
    pipeline = get_ocr_model(lan)

    img_add_border = add_white_border(img)
    img_ndarray = numpy.array(img_add_border)
    result = pipeline.predict(img_ndarray)
    text = ''

    # 新版本 API 返回格式：列表包含字典
    if isinstance(result, list) and len(result) > 0:
        first_item = result[0]
        if isinstance(first_item, dict) and 'parsing_res_list' in first_item:
            for t in first_item['parsing_res_list']:
                print(t.content)
                text += t.content
        elif isinstance(first_item, list):
            # 旧版本格式：嵌套列表
            for line in first_item:
                if line and len(line) > 1:
                    t = line[1][0]
                    print(t)
                    text += t
    return text

def add_white_border(img: Image):
    border_width = 50
    border_color = (255, 255, 255)  # 白色
    img_with_border = ImageOps.expand(img, border=border_width, fill=border_color)
    return img_with_border


def poly2bbox(poly):
    L = poly[0]
    U = poly[1]
    R = poly[2]
    D = poly[5]
    L, R = min(L, R), max(L, R)
    U, D = min(U, D), max(U, D)
    bbox = [L, U, R, D]
    return bbox

def main():
    with open('test/dataset_transform/labels/tabelLabel2OmniDocBench.json', 'r') as f:
        samples = json.load(f)

    results = []

    for sample in samples:
        img_name = os.path.basename(sample['page_info']['image_path'])
        img_path = os.path.join('E:/work/图纸解析/模型评测数据集/2960_1664/tables_and_graphes', img_name)
        img = Image.open(img_path)
        if not os.path.exists(img_path):
            print('No exist: ', img_name)
            continue
        for i, anno in enumerate(sample['layout_dets']):
            if not anno.get('category_type'):
                continue
            print(anno)
            lan = anno['attribute'].get('text_language', 'mixed')
            bbox = poly2bbox(anno['poly'])
            image = img.crop(bbox).convert('RGB') # crop text block
            outputs = test_paddle(image, lan)

            anno['pred'] = outputs
        results.append(sample)

    # 推理完成后，一次性写入文件
    with open('test/model_outputs/drawings_table.jsonl', 'w', encoding='utf-8') as f:
        f.truncate(0)
        for sample in results:
            json.dump(sample, f, ensure_ascii=False)
            f.write('\n')

def save_json():
    # 文本OCR质检：gpt-4o/internvl jsonl2json
    with open('test/model_outputs/drawings_table.jsonl', 'r') as f:
        lines = f.readlines()
    samples = [json.loads(line) for line in lines]
    with open('test/model_outputs/drawings_table.json', 'w', encoding='utf-8') as f:
        f.truncate(0)
        json.dump(samples, f, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    main()
    save_json()