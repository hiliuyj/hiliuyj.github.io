#!/usr/bin/env python3
import markdown
import sys
import os

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def get_template(title):
    # 基于 OpenWRT-Restrict- access-network.html 的样式，但进行了一些调整
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #2c3e50 0%, #4a6491 100%);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .subtitle {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}

        .info-box {{
            background: white;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #3498db;
        }}

        .info-box.warning {{
            border-left-color: #e74c3c;
            background: #fff5f5;
        }}

        .info-box.success {{
            border-left-color: #2ecc71;
            background: #f0fff4;
        }}

        h2 {{
            color: #2c3e50;
            margin: 1.5rem 0 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #3498db;
        }}

        h3 {{
            color: #34495e;
            margin: 1rem 0 0.5rem;
        }}

        .content {{
            background: white;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .content h1, .content h2, .content h3, .content h4, .content h5, .content h6 {{
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
        }}

        .content p {{
            margin-bottom: 1rem;
        }}

        .content ul, .content ol {{
            margin-left: 2rem;
            margin-bottom: 1rem;
        }}

        .content li {{
            margin-bottom: 0.5rem;
        }}

        .code-block {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
        }}

        .code-block pre {{
            margin: 0;
        }}

        .highlight {{
            color: #e74c3c;
            font-weight: bold;
        }}

        .note {{
            background: #fff9e6;
            border-left: 4px solid #f39c12;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 0 5px 5px 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            background: white;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        th {{
            background: #3498db;
            color: white;
            padding: 0.75rem;
            text-align: left;
        }}

        td {{
            padding: 0.75rem;
            border-bottom: 1px solid #ddd;
        }}

        tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        .footer {{
            text-align: center;
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}

            h1 {{
                font-size: 2rem;
            }}

            .content {{
                padding: 1rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <p class="subtitle">CMSIS-DAP 技术方案与实现指南</p>
        </header>

        <div class="content">
            <!-- 动态插入转换后的 markdown 内容 -->
            !!!CONTENT!!!
        </div>

        <div class="footer">
            <p>© 2024 技术文档 | 基于 markdown 转换生成</p>
            <p>本文档为技术学习参考，请遵守相关开源协议</p>
        </div>
    </div>
</body>
</html>'''

def convert_md_to_html(md_file, html_file):
    md_content = read_file(md_file)
    # 使用 markdown 库转换为 HTML
    # 启用扩展以支持表格、代码块等
    html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])

    # 提取标题（第一个 h1）
    lines = md_content.strip().split('\n')
    title = 'CMSIS-DAP 技术方案与实现指南'
    for line in lines:
        if line.startswith('# '):
            title = line[2:].strip()
            break

    template = get_template(title)
    # 替换占位符
    final_html = template.replace('!!!CONTENT!!!', html_content)

    write_file(html_file, final_html)
    print(f'Successfully converted {md_file} to {html_file}')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python convert_md_to_html.py <input.md> <output.html>')
        sys.exit(1)
    md_file = sys.argv[1]
    html_file = sys.argv[2]
    convert_md_to_html(md_file, html_file)