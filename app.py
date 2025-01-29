from flask import Flask, request, jsonify, render_template
import logging
from datetime import datetime
import os
from data_sources import DataManager
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 获取API密钥
domain_api_key = os.getenv('DOMAIN_API_KEY')
if domain_api_key:
    logger.info(f"Loaded API key ending with: {domain_api_key[-2:]}")
else:
    logger.error("No Domain API key found in environment variables")
    raise ValueError("Missing DOMAIN_API_KEY environment variable")

app = Flask(__name__)
data_manager = DataManager(domain_api_key)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        suburb = data.get('suburb')
        force_refresh = data.get('force_refresh', False)
        
        if not suburb:
            return jsonify({'error': '请输入区域名称'}), 400
            
        logger.info(f"搜索区域: {suburb}, 强制刷新: {force_refresh}")
        
        # 获取区域数据
        results = data_manager.get_suburb_data(suburb)
        
        if not results:
            return jsonify({'error': '未找到相关数据'}), 404
            
        return jsonify({
            'data': results,
            'source': 'api',
            'last_updated': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test_api', methods=['GET'])
def test_api():
    """测试OpenAI API连接"""
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, this is a test."}
            ],
            max_tokens=10
        )
        return jsonify({
            'status': 'success',
            'message': 'API连接正常',
            'response': response.choices[0].message.content
        })
    except Exception as e:
        logger.error(f"API测试失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'API连接失败: {str(e)}'
        }), 500

@app.route('/clear_cache/<suburb>', methods=['POST'])
def clear_cache(suburb):
    """手动清除指定区域的缓存"""
    try:
        cache_manager.clear_cache(suburb)
        return jsonify({
            'status': 'success',
            'message': f'已清除{suburb}的缓存'
        })
    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {error}")
    return jsonify({'error': '服务器内部错误，请稍后重试'}), 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"页面未找到: {error}")
    return jsonify({'error': '请求的页面不存在'}), 404

if __name__ == '__main__':
    logger.info("Starting application...")
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)