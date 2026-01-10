from paddleocr import PaddleOCR
from PIL import Image, ImageOps
import numpy
import json
# 读取第一个样本
with open('demo_data/omnidocbench_demo/OmniDocBench_demo.json', 'r') as f:
    samples = json.load(f)
sample = samples[0]
img_name = sample['page_info']['image_path'].split('/')[-1]
img_path = f'demo_data/omnidocbench_demo/images/{img_name}'
img = Image.open(img_path)
# 获取第一个文本块
for anno in sample['layout_dets']:
    if not anno.get('text'):
        continue
    print(f"原始文本: {anno['text']}")
    # 裁剪图像
    poly = anno['poly']
    L, U, R, D = poly[0], poly[1], poly[2], poly[5]
    L, R = min(L, R), max(L, R)
    U, D = min(U, D), max(U, D)
    cropped = img.crop((L, U, R, D)).convert('RGB')
    img_with_border = ImageOps.expand(cropped, border=50, fill=(255, 255, 255))
    img_ndarray = numpy.array(img_with_border)
    # OCR识别
    ocr = PaddleOCR(use_textline_orientation=True, lang='en')
    result = ocr.predict(img_ndarray)
    print(f"\n返回类型: {type(result)}")
    print(f"返回内容: {result}")
    if isinstance(result, dict):
        print(f"字典键: {result.keys()}")
    break