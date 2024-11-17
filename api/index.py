import os
import uuid
from flask import Flask, request, jsonify, render_template
import vercel_blob

app = Flask(__name__)

# 设置允许上传的内容类型
ALLOWED_CONTENT_TYPE = 'application/json'

# 自动换行逻辑函数
def add_line_breaks_to_svg(svg_string, max_chars_per_line=30):
    """
    对 SVG 内容中的文本段落进行换行处理，限制每行的字符数。
    """
    # 查找所有 <text> 标签中的内容并添加换行
    import re
    pattern = r"<text([^>]*)>(.*?)</text>"
    matches = re.findall(pattern, svg_string)

    updated_svg = svg_string
    for match in matches:
        attributes, content = match
        words = content.split()  # 按空格分隔
        lines = []
        current_line = []

        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > max_chars_per_line:
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        # 构造带 <tspan> 的新内容
        new_content = ''.join([f'<tspan x="0" dy="{20 * i}">{line}</tspan>' for i, line in enumerate(lines)])
        updated_svg = updated_svg.replace(f"<text{attributes}>{content}</text>", f"<text{attributes}>{new_content}</text>")

    return updated_svg

# 首页路由，显示静态页面
@app.route('/')
def home():
    return render_template('index.html')  # 渲染 templates/index.html

@app.route('/convert', methods=['POST'])
def convert_svg_to_html():
    if request.content_type != ALLOWED_CONTENT_TYPE:
        return jsonify({"error": "Invalid content type. Please send application/json."}), 400

    try:
        # 获取请求体中的 JSON 数据
        data = request.get_json()

        # 从 JSON 中获取 SVG 字符串
        svg_string = data.get('svg')
        if not svg_string:
            return jsonify({"error": "No SVG content found in request"}), 400

        # 替换未转义的 '&' 为 '&amp;'
        svg_string = svg_string.replace("&", "&amp;")

        # 动态处理 SVG：添加换行
        updated_svg = add_line_breaks_to_svg(svg_string)

        # 使用 UUID 生成唯一的 SVG 文件名
        svg_filename = f"{uuid.uuid4()}.svg"

        # 将 SVG 内容上传到 Vercel Blob
        svg_blob = vercel_blob.put(svg_filename, updated_svg.encode('utf-8'), {
            "contentType": "image/svg+xml",
            "access": "public"
        })

        # 创建 HTML 内容，包含 SVG 文件链接
        html_content = f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SVG Preview</title>
            <style>
                /* 全局样式 */
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                    font-family: 'Noto Sans SC', sans-serif;
                }}
                body {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #ffffff; /* 纯白背景 */
                    color: #34495e;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SVG Preview</h1>
                <img src="{svg_blob['url']}" alt="SVG Image" />
            </div>
        </body>
        </html>
        '''

        # 使用 UUID 生成唯一的 HTML 文件名
        html_filename = f"{uuid.uuid4()}.html"

        # 将 HTML 内容上传到 Vercel Blob
        html_blob = vercel_blob.put(html_filename, html_content.encode('utf-8'), {
            "contentType": "text/html",
            "access": "public"
        })

        # 返回 HTML 和 SVG 文件的 URL
        return jsonify({"html_url": html_blob['url'], "svg_url": svg_blob['url']}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
