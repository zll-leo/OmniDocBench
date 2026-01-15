"""
HTML Table Viewer

渲染 JSON 文件中的 HTML 表格，在浏览器中查看。
"""

import json
import webbrowser
import os
from pathlib import Path


def load_json(json_path: str) -> list:
    """加载 JSON 文件"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_html(data: list, total_tables: int) -> str:
    """生成可视化 HTML 页面"""

    html_parts = [
        """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>表格查看器 - OmniDocBench</title>
    <style>
        * """
        + "{" + """
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        """ + "}" + """

        body """
        + "{" + """
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        """ + "}" + """

        .container """
        + "{" + """
            max-width: 1400px;
            margin: 0 auto;
        """ + "}" + """

        h1 """
        + "{" + """
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        """ + "}" + """

        .summary """
        + "{" + """
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        """ + "}" + """

        .summary p """
        + "{" + """
            margin: 5px 0;
            color: #333;
        """ + "}" + """

        .table-card """
        + "{" + """
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        """ + "}" + """

        .table-card:hover """
        + "{" + """
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        """ + "}" + """

        .table-header """
        + "{" + """
            border-bottom: 2px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 20px;
        """ + "}" + """

        .table-title """
        + "{" + """
            font-size: 1.5em;
            color: #667eea;
            margin-bottom: 10px;
            font-weight: bold;
        """ + "}" + """

        .table-meta """
        + "{" + """
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 10px;
        """ + "}" + """

        .meta-item """
        + "{" + """
            background: #f0f4ff;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        """ + "}" + """

        .meta-label """
        + "{" + """
            font-weight: bold;
            color: #667eea;
        """ + "}" + """

        .meta-value """
        + "{" + """
            color: #333;
        """ + "}" + """

        .image-path """
        + "{" + """
            color: #764ba2;
            font-family: monospace;
            background: #f5f5f5;
            padding: 8px 15px;
            border-radius: 5px;
            margin-top: 10px;
        """ + "}" + """

        .table-wrapper """
        + "{" + """
            overflow-x: auto;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            background: #fafafa;
        """ + "}" + """

        .table-wrapper table """
        + "{" + """
            border-collapse: collapse;
            width: 100%;
            background: white;
        """ + "}" + """

        .table-wrapper table td """
        + "{" + """
            border: 1px solid #ddd;
            padding: 12px 15px;
            text-align: left;
            min-width: 50px;
        """ + "}" + """

        .table-wrapper table tr:nth-child(even) """
        + "{" + """
            background-color: #f9f9f9;
        """ + "}" + """

        .table-wrapper table tr:hover """
        + "{" + """
            background-color: #e8f4ff;
        """ + "}" + """

        .table-wrapper table td:empty::before """
        + "{" + """
            content: "";
            display: inline-block;
        """ + "}" + """

        .attribute-badge """
        + "{" + """
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 5px;
            margin-bottom: 5px;
        """ + "}" + """

        .badge-success """
        + "{" + """ background: #d4edda; color: #155724; """ + "}" + """
        .badge-info """
        + "{" + """ background: #d1ecf1; color: #0c5460; """ + "}" + """
        .badge-warning """
        + "{" + """ background: #fff3cd; color: #856404; """ + "}" + """
        .badge-danger """
        + "{" + """ background: #f8d7da; color: #721c24; """ + "}" + """

        .html-preview """
        + "{" + """
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            font-family: "Consolas", "Monaco", monospace;
            font-size: 0.85em;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        """ + "}" + """

        .html-preview-label """
        + "{" + """
            color: #a6a6a6;
            margin-bottom: 10px;
            font-weight: bold;
        """ + "}" + """
    </style>
</head>
<body>
    <div class="container">
        <h1>表格查看器 - OmniDocBench</h1>
        <div class="summary">
            <p><strong>总表格数:</strong> """ + str(total_tables) + """</p>
        </div>
"""
    ]

    for idx, item in enumerate(data, 1):
        for table_idx, det in enumerate(item.get('layout_dets', []), 1):
            if det.get('category_type') != 'table':
                continue

            html = det.get('html', '')
            attrs = det.get('attribute', {})
            page_info = item.get('page_info', {})
            image_path = page_info.get('image_path', 'N/A')

            # 提取 table 标签内容（去掉 html 和 body 标签）
            table_html = html
            if '<table>' in html:
                start = html.find('<table>')
                end = html.rfind('</table>') + 8
                table_html = html[start:end]

            table_title = f"表格 #{idx}{'.' + str(table_idx) if len(item.get('layout_dets', [])) > 1 else ''}"

            html_parts.append(f"""
        <div class="table-card">
            <div class="table-header">
                <div class="table-title">{table_title}</div>
                <div class="table-meta">
                    <div class="meta-item">
                        <span class="meta-label">布局:</span>
                        <span class="meta-value">{attrs.get('table_layout', 'N/A')}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">合并单元格:</span>
                        <span class="meta-value">{'是' if attrs.get('with_span') else '否'}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">线条:</span>
                        <span class="meta-value">{attrs.get('line', 'N/A')}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">语言:</span>
                        <span class="meta-value">{attrs.get('language', 'N/A').replace('table_', '')}</span>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">状态:</span>
                        <span class="meta-value">{det.get('table_edit_status', 'N/A')}</span>
                    </div>
                </div>
                <div class="image-path">图片: {image_path}</div>
            </div>

            <div class="table-wrapper">
                {table_html}
            </div>

            <div class="html-preview">
                <div class="html-preview-label">HTML 源码:</div>
                {html}
            </div>
        </div>
""")

    html_parts.append("""
    </div>
</body>
</html>
""")

    return ''.join(html_parts)


def main():
    # 文件路径
    script_dir = Path(__file__).parent
    json_path = script_dir / 'dataset_transform' / 'labels' / 'tabelLabel2OmniDocBench.json'
    output_path = script_dir / 'view_tables_output.html'

    # 加载数据
    print(f"正在读取: {json_path}")
    data = load_json(str(json_path))

    # 统计表格数量
    table_count = sum(
        len([d for d in item.get('layout_dets', []) if d.get('category_type') == 'table'])
        for item in data
    )
    print(f"找到 {table_count} 个表格")

    # 生成 HTML
    html = generate_html(data, table_count)

    # 保存文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"已生成: {output_path}")

    # 在浏览器中打开
    webbrowser.open(str(output_path.absolute()))
    print("已在浏览器中打开")


if __name__ == '__main__':
    main()