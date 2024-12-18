import os
from flask import Flask, request, jsonify, send_from_directory
import uuid

# 创建Flask应用
app = Flask(__name__)

# 定义保存HTML文件的文件夹
OUTPUT_FOLDER = './output_html'

# 创建文件夹（如果不存在）
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 配置Flask
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 设置允许上传的内容类型
ALLOWED_CONTENT_TYPE = 'application/json'


# 接收并生成包含SVG的HTML文件的API
@app.route('/convert', methods=['POST'])
def convert_svg_to_html():
    if request.content_type != ALLOWED_CONTENT_TYPE:
        return jsonify({"error": "Invalid content type. Please send application/json."}), 400

    try:
        # 获取请求体中的JSON数据
        data = request.get_json()

        # 从JSON中获取SVG字符串
        svg_string = data.get('svg')
        if not svg_string:
            return jsonify({"error": "No SVG content found in request"}), 400

        # 使用UUID生成一个唯一的文件名
        output_filename = str(uuid.uuid4()) + '.html'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # 创建HTML内容，包含SVG
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
                {svg_string}  <!-- 直接插入SVG内容 -->
            </div>
        </body>
        </html>
        '''

        # 将HTML内容写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 构造HTML文件的URL并返回
        html_url = f'/output/{output_filename}'
        return jsonify({"html_url": html_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 提供生成的HTML文件
@app.route('/output/<filename>')
def serve_html(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


# 启动Flask应用
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
