import os
import uuid
import requests
from flask import Flask, request, jsonify

# 创建Flask应用
app = Flask(__name__)

# 配置Vercel Blob的API访问令牌
VERCEL_BLOB_API_URL = "https://api.vercel.com/v2/blob"
VERCEL_ACCESS_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN")  # 从环境变量获取访问令牌

# 配置允许的内容类型
ALLOWED_CONTENT_TYPE = "application/json"

# 获取Blob上传的签名URL
def get_blob_upload_url():
    headers = {
        "Authorization": f"Bearer {VERCEL_ACCESS_TOKEN}"
    }
    payload = {
        "expiresIn": 3600  # 设置签名 URL 的有效期，单位为秒
    }
    response = requests.post(f"{VERCEL_BLOB_API_URL}/upload", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["url"]  # 返回签名的上传 URL
    else:
        raise Exception(f"Failed to get blob upload URL: {response.json()}")


# 上传文件到Vercel Blob
def upload_file_to_blob(file_content, file_type):
    upload_url = get_blob_upload_url()
    headers = {"Content-Type": file_type}
    response = requests.put(upload_url, headers=headers, data=file_content)
    if response.status_code == 200:
        return response.url  # 返回存储在Blob中的文件URL
    else:
        raise Exception(f"Failed to upload file: {response.json()}")

# 接收并生成包含SVG的HTML文件的API
@app.route("/convert", methods=["POST"])
def convert_svg_to_html():
    if request.content_type != ALLOWED_CONTENT_TYPE:
        return jsonify({"error": "Invalid content type. Please send application/json."}), 400

    try:
        # 获取请求体中的JSON数据
        data = request.get_json()

        # 从JSON中获取SVG字符串
        svg_string = data.get("svg")
        if not svg_string:
            return jsonify({"error": "No SVG content found in request"}), 400

        # 替换未转义的 '&' 为 '&amp;'
        svg_string = svg_string.replace("&", "&amp;")

        # 生成SVG文件名
        svg_filename = str(uuid.uuid4()) + ".svg"

        # 上传SVG文件到Vercel Blob
        svg_url = upload_file_to_blob(svg_string.encode("utf-8"), "image/svg+xml")

        # 创建HTML内容，包含SVG文件链接
        html_filename = str(uuid.uuid4()) + ".html"
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
                <img src="{svg_url}" alt="SVG Image" />
            </div>
        </body>
        </html>
        '''

        # 上传HTML文件到Vercel Blob
        html_url = upload_file_to_blob(html_content.encode("utf-8"), "text/html")

        # 返回SVG和HTML文件的URL
        return jsonify({"html_url": html_url, "svg_url": svg_url}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 启动Flask应用
if __name__ == "__main__":
    app.run(debug=True)
