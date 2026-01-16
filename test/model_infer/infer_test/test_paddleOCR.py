from paddleocr import PaddleOCR
from paddleocr import PPStructureV3
from PIL import Image, ImageOps
import numpy
import json
# 读取第一个样本
with open('test/dataset_transform/labels/tabelLabel2OmniDocBench.json', 'r') as f:
    samples = json.load(f)
sample = samples[0]
img_name = sample['page_info']['image_path'].split('/')[-1]
img_path = f'E:/work/图纸解析/模型评测数据集/2960_1664/tables_and_graphes/{img_name}'
img = Image.open(img_path)
# 获取第一个文本块
for anno in sample['layout_dets']:
    print(anno)
    if not anno.get('html'):
        continue
    print(f"原始文本: {anno['html']}")
    # 裁剪图像
    # poly = anno['poly']
    # L, U, R, D = poly[0], poly[1], poly[2], poly[5]
    # L, R = min(L, R), max(L, R)
    # U, D = min(U, D), max(U, D)
    # cropped = img.crop((L, U, R, D)).convert('RGB')
    # cropped.show()
    # img_with_border = ImageOps.expand(cropped, border=50, fill=(255, 255, 255))
    # img_with_border.show()
    # img_ndarray = numpy.array(img_with_border)
    # ========== OCR识别 ==========
    # ocr = PaddleOCR(use_textline_orientation=True, lang='ch')
    # img_ndarray = numpy.array(img)
    # img.show()
    # result = ocr.predict(img_ndarray)
    # ========== table识别 ==========
    pipeline = PPStructureV3(use_doc_orientation_classify=False,use_doc_unwarping=False)
    img_ndarray = numpy.array(img)
    result = pipeline.predict(img_ndarray)
    print(f"\n返回类型: {type(result)}")
    print(f"返回内容: {result}")
    if isinstance(result, dict):
        print(f"字典键: {result.keys()}")
    # for res in result:
    #     # res.print()
    #     res.save_to_json(save_path="test/model_outputs/ppocr_table.json")
    if isinstance(result, list) and len(result) > 0:
        first_item = result[0]
        if isinstance(first_item, dict) and 'parsing_res_list' in first_item:
            # 新版本格式：result[0]['rec_texts'] 是文本列表
            for t in first_item['parsing_res_list']:
                print(f"t的类型：{type(t)}")
                print(t.content)
    break