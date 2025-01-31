from flask import Flask, render_template, request, jsonify, send_from_directory
from search_engine import PropertySearchEngine
import os
from openai import OpenAI
import time
import re
from dotenv import load_dotenv
import logging
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 配置OpenAI API
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

app = Flask(__name__)
# 确保JSON输出中文不被转义
app.config['JSON_AS_ASCII'] = False

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# 暂时注释掉未使用的search_engine
# search_engine = PropertySearchEngine()

def standardize_suburb(suburb):
    """标准化区域名称，处理包含邮编的情况"""
    # 移除多余空格并转小写
    suburb = suburb.lower().strip()
    
    # 处理包含3030邮编的情况
    if '3030' in suburb:
        return 'point cook'
        
    # 如果输入就是3030
    if suburb == '3030':
        return 'point cook'
        
    return suburb

def analyze_with_openai(suburb):
    """使用OpenAI分析区域信息"""
    try:
        start_time = time.time()
        
        # 构建提示词
        prompt = f"""请对墨尔本{suburb}区域进行详细分析，包括以下方面：
1. 区域概况
2. 公共设施与政府基建
3. 教育资源
4. 医疗资源
5. 交通情况
6. 房价趋势
7. 总结（包括优势和劣势）

请使用Markdown格式输出，使用#和##作为标题标记。对于投资金额，请标注具体数字（如有）。
"""

        # 调用OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一个专业的房地产分析师，擅长分析墨尔本各个区域。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
            top_p=0.95
        )
        
        # 记录API调用时间和token使用情况
        end_time = time.time()
        logger.info(f"OpenAI API调用耗时: {end_time - start_time:.2f}秒")
        logger.info(f"使用的tokens: {response.usage.total_tokens}")
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API调用失败: {str(e)}")
        raise Exception("生成分析报告时出错，请稍后重试")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        if data is None:
            logger.error("无效的JSON数据")
            return jsonify({'error': '请求格式错误'}), 400
            
        suburb = data.get('suburb', '')
        
        if not suburb:
            logger.error("未提供区域名称")
            return jsonify({'error': '请输入区域名称或邮编'}), 400
        
        # 使用新的标准化函数处理输入
        suburb = standardize_suburb(suburb)
        logger.info(f"分析区域: {suburb}")
        
        # 直接使用OpenAI分析
        analysis = analyze_with_openai(suburb)
        
        return jsonify({
            'analysis': analysis,
            'disclaimer': '注意：本报告中的数据仅供参考，具体信息请以官方发布为准。'
        })
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test_api', methods=['GET'])
def test_api():
    """测试OpenAI API连接"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, this is a test."}
            ],
            max_tokens=10,
            temperature=0.2
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

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"服务器内部错误: {error}")
    return jsonify({'error': '服务器内部错误，请稍后重试'}), 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"页面未找到: {error}")
    return jsonify({'error': '请求的页面不存在'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 