import os
from flask import Flask, request, jsonify, send_from_directory
import cairosvg
import uuid
from io import BytesIO

# 创建Flask应用
app = Flask(__name__)

# 定义保存图片的文件夹
OUTPUT_FOLDER = './output_images'

# 创建文件夹（如果不存在）
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 配置Flask
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 设置允许上传的内容类型
ALLOWED_CONTENT_TYPE = 'application/json'


# 接收并转换SVG字符串的API
@app.route('/convert', methods=['POST'])
def convert_svg_to_image():
    if request.content_type != ALLOWED_CONTENT_TYPE:
        return jsonify({"error": "Invalid content type. Please send application/json."}), 400

    try:
        # 获取请求体中的JSON数据
        data = request.get_json()

        # 从JSON中获取SVG字符串
        svg_string = data.get('svg')
        if not svg_string:
            return jsonify({"error": "No SVG content found in request"}), 400

        # svg_string = svg_string.replace(
        #     "@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&display=swap');",
        #     "font-family: 'Noto Sans SC', sans-serif;"
        # )
        # 使用UUID生成一个唯一的文件名
        output_filename = str(uuid.uuid4()) + '.png'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        # 将SVG字符串转换为PNG并保存到文件
        cairosvg.svg2png(bytestring=svg_string.encode('utf-8'), write_to=output_path)

        # 构造图片URL并返回
        image_url = f'./output/{output_filename}'
        return jsonify({"image_url": image_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 提供生成的图片文件
@app.route('/output/<filename>')
def serve_image(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


# 启动Flask应用
if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5000)

