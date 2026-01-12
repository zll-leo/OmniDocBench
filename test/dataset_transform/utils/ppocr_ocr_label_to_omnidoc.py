import json

input_path = 'test/dataset_transform/Label.txt'
output_path = 'test/dataset_transform/Label2OmniDocBench.json'

def convert_ocr_label_to_omnidocbench(input_path, output_path):
    results = []
    with open(input_path, 'r', encoding='utf-8') as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            # 分割图片路径和标注内容
            try:
                img_path, ann_str = line.split('\t', 1)
            except ValueError:
                continue
            anns = json.loads(ann_str)
            layout_dets = []
            for idx, ann in enumerate(anns):
                points = ann.get('points', -1)
                poly = [coord for point in points for coord in point]
                layout_dets.append({
                    'category_type': 'text_block',
                    'poly': poly,
                    'ignore': False,
                    'order': -1,
                    'anno_id': idx,
                    'text': ann.get('transcription', -1),
                    'line_with_spans': -1,
                    'attribute': -1,
                    'pred': -1
                })
            page_info = {
                'image_path': img_path,
                'page_no': -1,
                'width': -1,
                'height': -1
            }
            extra = {'relation': -1}
            results.append({
                'layout_dets': layout_dets,
                'page_info': page_info,
                'extra': extra
            })
    with open(output_path, 'w', encoding='utf-8') as fout:
        json.dump(results, fout, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    convert_ocr_label_to_omnidocbench(input_path, output_path)
