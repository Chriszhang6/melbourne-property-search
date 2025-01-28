from flask import Flask, render_template, request, jsonify
from search_engine import PropertySearchEngine
import os
from gpt4all import GPT4All
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
search_engine = PropertySearchEngine()

# 初始化模型
MODEL_PATH = "models/ggml-gpt4all-j-v1.3-groovy.bin"
model = None

def load_model():
    global model
    if model is None:
        # 如果模型文件不存在，先下载
        if not os.path.exists(MODEL_PATH):
            os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
            print("请先运行download_model.py下载模型文件")
            
        model = GPT4All(MODEL_PATH)

def analyze_with_gpt4all(search_results):
    """使用GPT4All-J分析搜索结果"""
    if model is None:
        load_model()
    
    prompt = f"""作为一个专业的墨尔本房地产分析师，请分析以下墨尔本房产信息，并提供一个详细的市场分析报告：

搜索结果：{search_results}

请包含以下方面：
1. 房产价格趋势
2. 区域特点分析
3. 投资建议
4. 需要注意的风险

请用中文回答，并保持专业性和客观性。"""
    
    try:
        # 使用流式生成获得更好的性能
        response = ""
        for token in model.generate(prompt, max_tokens=512, temp=0.7, top_p=0.9, streaming=True):
            response += token
            
        return response.strip()
    except Exception as e:
        return f"分析过程中出现错误: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    suburb = data.get('suburb', '')
    
    if not suburb:
        return jsonify({'error': '请输入区域名称或邮编'}), 400
    
    # 标准化输入
    suburb = suburb.lower().strip()
    if suburb == '3030':
        suburb = 'point cook'
    
    try:
        # 获取搜索结果
        results = search_engine.search_suburb(suburb)
        
        # 使用GPT4All-J分析结果
        analysis = analyze_with_gpt4all(results)
        
        return jsonify({
            'raw_results': results,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 预加载模型
    load_model()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 