from flask import Flask, jsonify
import os
from dotenv import load_dotenv, find_dotenv

# 初始化 Flask 应用
app = Flask(__name__)

# 打印当前工作目录
print(f"Current working directory: {os.getcwd()}")

# 查找 .env 文件
env_path = find_dotenv()
print(f"Found .env file at: {env_path}")

# 加载环境变量
load_dotenv(override=True)

@app.route('/')
def home():
    # 获取 API 密钥
    api_key = os.getenv('OPENAI_API_KEY', 'No key found')
    
    # 打印到控制台以便调试
    print(f"Current API key ends with: {api_key[-2:] if api_key != 'No key found' else 'NA'}")
    
    # 返回 JSON 响应
    return jsonify({
        'message': 'Server is running',
        'api_key_ends_with': api_key[-2:] if api_key != 'No key found' else 'NA',
        'env_file_location': env_path
    })

if __name__ == '__main__':
    # 启动时打印信息
    print("Starting server...")
    api_key = os.getenv('OPENAI_API_KEY', 'No key found')
    print(f"Initial API key ends with: {api_key[-2:] if api_key != 'No key found' else 'NA'}")
    
    # 启动服务器
    app.run(port=5001, debug=True)