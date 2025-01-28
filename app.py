from flask import Flask, render_template, request, jsonify
from search_engine import PropertySearchEngine
import os

app = Flask(__name__)
search_engine = PropertySearchEngine()

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
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 