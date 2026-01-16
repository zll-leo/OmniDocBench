"""
HTML Table Viewer

渲染 JSON 文件中的 HTML 表格，在浏览器中查看。
"""

import json
import webbrowser
import os
import html
import argparse
from pathlib import Path


def load_json(json_path: str) -> list:
    """加载 JSON 文件"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_tables(data: list, html_field: str = 'html') -> list:
    """从原始 JSON 数据中提取表格信息

    Args:
        data: 原始 JSON 数据
        html_field: HTML 字段名称，'html' 为真值，'pred' 为预测值
    """
    tables = []

    for idx, item in enumerate(data, 1):
        layout_dets = item.get('layout_dets', [])
        image_path = item.get('page_info', {}).get('image_path', 'N/A')

        for table_idx, det in enumerate(layout_dets, 1):
            if det.get('category_type') != 'table':
                continue

            raw_html = det.get(html_field, '')
            print(raw_html)
            # 提取 table 标签内容（去掉 html 和 body 标签）
            table_html = raw_html
            if '<table>' in raw_html:
                start = raw_html.find('<table>')
                end = raw_html.rfind('</table>') + 8
                table_html = raw_html[start:end]
            tables.append({
                'idx': idx,
                'sub_idx': table_idx,
                'has_multiple': len(layout_dets) > 1,
                'html': table_html,
                'raw_html': raw_html,
                'attrs': det.get('attribute', {}),
                'image_path': image_path,
                'status': det.get('table_edit_status', 'N/A')
            })

    return tables


def _get_css_styles() -> str:
    """获取 CSS 样式"""
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .summary {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .summary p {
            margin: 5px 0;
            color: #333;
        }

        .data-source-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-left: 10px;
        }

        .data-source-gt {
            background: #d4edda;
            color: #155724;
        }

        .data-source-pred {
            background: #fff3cd;
            color: #856404;
        }

        .table-card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }

        .table-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }

        .table-card.hidden {
            display: none;
        }

        .table-header {
            border-bottom: 2px solid #667eea;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }

        .table-title {
            font-size: 1.5em;
            color: #667eea;
            margin-bottom: 10px;
            font-weight: bold;
        }

        .table-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 10px;
        }

        .meta-item {
            background: #f0f4ff;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }

        .meta-label {
            font-weight: bold;
            color: #667eea;
        }

        .meta-value {
            color: #333;
        }

        .image-path {
            color: #764ba2;
            font-family: monospace;
            background: #f5f5f5;
            padding: 8px 15px;
            border-radius: 5px;
            margin-top: 10px;
        }

        .table-wrapper {
            overflow-x: auto;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            background: #fafafa;
        }

        .table-wrapper table {
            border-collapse: collapse;
            width: 100%;
            background: white;
        }

        .table-wrapper table td {
            border: 1px solid #ddd;
            padding: 12px 15px;
            text-align: left;
            min-width: 50px;
        }

        .table-wrapper table tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        .table-wrapper table tr:hover {
            background-color: #e8f4ff;
        }

        .table-wrapper table td:empty::before {
            content: "";
            display: inline-block;
        }

        .attribute-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 5px;
            margin-bottom: 5px;
        }

        .badge-success { background: #d4edda; color: #155724; }
        .badge-info { background: #d1ecf1; color: #0c5460; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .badge-danger { background: #f8d7da; color: #721c24; }

        .html-preview {
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
        }

        .html-preview-label {
            color: #a6a6a6;
            margin-bottom: 10px;
            font-weight: bold;
        }

        .pagination {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        .pagination-left {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .pagination-right {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .pagination-info {
            color: #333;
            font-size: 0.95em;
        }

        .pagination-select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: white;
            color: #333;
            font-size: 0.9em;
            cursor: pointer;
        }

        .pagination-btn {
            padding: 8px 16px;
            border: 1px solid #667eea;
            border-radius: 6px;
            background: white;
            color: #667eea;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .pagination-btn:hover:not(:disabled) {
            background: #667eea;
            color: white;
        }

        .pagination-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
            border-color: #ccc;
            color: #ccc;
        }

        .pagination-input {
            width: 60px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 6px;
            text-align: center;
            font-size: 0.9em;
        }

        .pagination-input:focus {
            outline: none;
            border-color: #667eea;
        }
"""


def _render_table_card(table: dict, table_idx: int) -> str:
    """渲染单个表格卡片

    Args:
        table: 表格数据字典
        table_idx: 表格索引

    Returns:
        HTML 字符串
    """
    # 生成表格标题
    table_title = f"表格 #{table['idx']}"
    if table['has_multiple']:
        table_title += f".{table['sub_idx']}"

    attrs = table['attrs']

    return f"""
        <div class="table-card" data-index="{table_idx}">
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
                        <span class="meta-value">{table['status']}</span>
                    </div>
                </div>
                <div class="image-path">图片: {table['image_path']}</div>
            </div>

            <div class="table-wrapper">
                {table['html']}
            </div>

            <div class="html-preview">
                <div class="html-preview-label">HTML 源码:</div>
                {html.escape(table['raw_html'])}
            </div>
        </div>
"""


def _render_pagination(per_page: int, total_pages: int) -> str:
    """渲染分页控件

    Args:
        per_page: 每页显示数量
        total_pages: 总页数

    Returns:
        HTML 字符串
    """
    return f"""
        <div class="pagination">
            <div class="pagination-left">
                <span class="pagination-info">每页显示:</span>
                <select class="pagination-select" id="perPageSelect">
                    <option value="10" {'selected' if per_page == 10 else ''}>10 条</option>
                    <option value="20" {'selected' if per_page == 20 else ''}>20 条</option>
                    <option value="50" {'selected' if per_page == 50 else ''}>50 条</option>
                    <option value="100" {'selected' if per_page == 100 else ''}>100 条</option>
                </select>
            </div>
            <div class="pagination-right">
                <button class="pagination-btn" id="firstPageBtn">首页</button>
                <button class="pagination-btn" id="prevPageBtn">上一页</button>
                <span class="pagination-info">
                    第 <input type="number" class="pagination-input" id="pageInput" min="1" value="1" max="{total_pages}"> 页 / 共 {total_pages} 页
                </span>
                <button class="pagination-btn" id="nextPageBtn">下一页</button>
                <button class="pagination-btn" id="lastPageBtn">末页</button>
            </div>
        </div>
"""


def _get_pagination_script(total_tables: int, per_page: int, total_pages: int) -> str:
    """获取分页 JavaScript 代码

    Args:
        total_tables: 总表格数
        per_page: 每页显示数量
        total_pages: 总页数

    Returns:
        JavaScript 字符串
    """
    return f"""
    <script>
        const totalTables = {total_tables};
        const defaultPerPage = {per_page};
        let currentPage = 1;
        let perPage = defaultPerPage;

        const tableCards = document.querySelectorAll('.table-card');
        const firstPageBtn = document.getElementById('firstPageBtn');
        const prevPageBtn = document.getElementById('prevPageBtn');
        const nextPageBtn = document.getElementById('nextPageBtn');
        const lastPageBtn = document.getElementById('lastPageBtn');
        const pageInput = document.getElementById('pageInput');
        const perPageSelect = document.getElementById('perPageSelect');

        function getTotalPages() {{
            return Math.ceil(totalTables / perPage) || 1;
        }}

        function updatePagination() {{
            const totalPages = getTotalPages();
            const startIndex = (currentPage - 1) * perPage;
            const endIndex = Math.min(startIndex + perPage, totalTables);

            tableCards.forEach((card, index) => {{
                if (index >= startIndex && index < endIndex) {{
                    card.classList.remove('hidden');
                }} else {{
                    card.classList.add('hidden');
                }}
            }});

            pageInput.max = totalPages;
            pageInput.value = currentPage;

            firstPageBtn.disabled = currentPage === 1;
            prevPageBtn.disabled = currentPage === 1;
            nextPageBtn.disabled = currentPage === totalPages;
            lastPageBtn.disabled = currentPage === totalPages;
        }}

        firstPageBtn.addEventListener('click', () => {{
            currentPage = 1;
            updatePagination();
        }});

        prevPageBtn.addEventListener('click', () => {{
            if (currentPage > 1) {{
                currentPage--;
                updatePagination();
            }}
        }});

        nextPageBtn.addEventListener('click', () => {{
            if (currentPage < getTotalPages()) {{
                currentPage++;
                updatePagination();
            }}
        }});

        lastPageBtn.addEventListener('click', () => {{
            currentPage = getTotalPages();
            updatePagination();
        }});

        pageInput.addEventListener('change', () => {{
            let page = parseInt(pageInput.value);
            const totalPages = getTotalPages();
            if (page < 1) page = 1;
            if (page > totalPages) page = totalPages;
            currentPage = page;
            updatePagination();
        }});

        perPageSelect.addEventListener('change', () => {{
            perPage = parseInt(perPageSelect.value);
            currentPage = 1;
            updatePagination();
        }});

        // 初始化
        updatePagination();
    </script>
"""


def generate_html(tables: list, total_tables: int, per_page: int = 20, html_field: str = 'html') -> str:
    """生成可视化 HTML 页面

    Args:
        tables: 表格数据列表
        total_tables: 总表格数
        per_page: 每页显示数量
        html_field: HTML 字段名称 ('html' 或 'pred')
    """
    # 计算总页数
    total_pages = (total_tables + per_page - 1) // per_page if total_tables > 0 else 1

    # HTML 头部
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>表格查看器 - OmniDocBench</title>
    <style>{_get_css_styles()}</style>
</head>
<body>
    <div class="container">
        <h1>表格查看器 - OmniDocBench</h1>
        <div class="summary">
            <p>
                <strong>总表格数:</strong> {total_tables}
                <span class="data-source-badge data-source-{'gt' if html_field == 'html' else 'pred'}">
                    {'Ground Truth (真值)' if html_field == 'html' else 'Prediction (预测值)'}
                </span>
            </p>
        </div>
"""

    # 渲染所有表格卡片
    for table_idx, table in enumerate(tables):
        html += _render_table_card(table, table_idx)

    # 分页控件
    html += _render_pagination(per_page, total_pages)

    # 结束标签和 JavaScript
    html += """
    </div>
"""

    html += _get_pagination_script(total_tables, per_page, total_pages)

    html += """
</body>
</html>
"""

    return html


def main(per_page: int = 20, html_field: str = 'html', json_path: str = None, output_path: str = None, no_browser: bool = False):
    """生成表格查看器 HTML

    Args:
        per_page: 每页显示的表格数量，默认 20
        html_field: HTML 字段名称，'html' 为真值，'pred' 为预测值，默认 'html'
        json_path: 输入 JSON 文件路径
        output_path: 输出 HTML 文件路径
        no_browser: 是否禁用浏览器自动打开
    """
    # 文件路径
    if json_path is None:
        json_path = "test/model_outputs/drawings_table.json"
    if output_path is None:
        output_path = "test/view_tables_output.html"

    # 加载数据
    print(f"正在读取: {json_path}")
    data = load_json(str(json_path))

    # 提取表格信息
    tables = extract_tables(data, html_field)
    print(f"找到 {len(tables)} 个表格 (数据源: {html_field})")

    # 生成 HTML
    html = generate_html(tables, len(tables), per_page, html_field)

    # 保存文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"已生成: {output_path}")

    # 在浏览器中打开
    if not no_browser:
        webbrowser.open(str(Path(output_path).absolute()))
        print("已在浏览器中打开")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='HTML 表格查看器 - 将 JSON 中的表格渲染为 HTML 页面',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
        # 指定输入输出文件，查看预测值（pred 字段），每页 50 条
        # python view_html_tables.py -i test/data.json -o output.html -f pred -p 50
        '''
    )

    parser.add_argument('-p', '--per-page', type=int, default=20, help='每页显示的表格数量 (默认: 20)')
    parser.add_argument('-f', '--html-field', type=str, default='html', choices=['html', 'pred'], help='HTML 字段名称: html=真值, pred=预测值 (默认: html)')
    parser.add_argument('-i', '--input', type=str, dest='json_path', default='test/model_outputs/drawings_table.json', help='输入 JSON 文件路径 (默认: test/model_outputs/drawings_table.json)')
    parser.add_argument('-o', '--output', type=str, dest='output_path', default='test/view_tables_output.html',help='输出 HTML 文件路径 (默认: test/view_tables_output.html)')
    parser.add_argument('--no-browser',action='store_true',help='生成后不自动打开浏览器')

    args = parser.parse_args()

    main(
        per_page=args.per_page,
        html_field=args.html_field,
        json_path=args.json_path,
        output_path=args.output_path,
        no_browser=args.no_browser
    )