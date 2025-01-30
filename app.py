from flask import Flask, render_template, request, jsonify, send_from_directory
from search_engine import PropertySearchEngine
import os
import openai
from functools import lru_cache
import time
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
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__, static_url_path='', static_folder='static')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

search_engine = PropertySearchEngine()

def analyze_with_openai(search_results):
    """使用OpenAI分析搜索结果"""
    try:
        max_input_length = 4000  # 增加长度限制，确保能获取更多内容
        truncated_results = str(search_results)[:max_input_length] + "..."
        
        system_prompt = """你是一个专业的墨尔本房地产分析师。我会提供一些搜索结果，这些结果包含了区域的教育、医疗和治安信息。请仔细阅读这些信息，并用中文总结分析。

分析要求：
1. 仔细阅读提供的搜索结果中的英文内容
2. 将重要信息翻译成中文
3. 按时间顺序组织信息
4. 提供具体的数据支持
5. 标注信息来源年份

请按以下格式进行分析：

1. 教育资源分析：
   - 主要公立学校和私立学校
   - 学校的排名和评级（如果数据中提供）
   - 教学特色和优势
   - 师资力量评估

2. 医疗资源分析：
   - 主要医疗机构名称和位置
   - 医院规模和等级
   - 专科特色
   - 急诊服务情况
   - 社区医疗设施

3. 治安状况分析：
   按时间顺序分析以下方面：
   - 总体犯罪率趋势（近几年的变化）
   - 主要犯罪类型及其占比
   - 与墨尔本其他区域的对比
   - 警力配置和响应时间
   - 社区安全措施
   - 需要特别注意的安全隐患

注意事项：
1. 如果搜索结果中包含具体数据，请在分析中明确引用
2. 信息按时间顺序组织，新的信息放在前面
3. 每个要点都要尽可能提供具体的数据支持
4. 如果某项信息缺失，请明确标注"数据缺失"

最后，请在分析报告末尾添加"参考来源"部分，列出所有引用的链接。"""

        logger.info("开始生成分析报告...")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"这是搜索结果，请仔细分析其中的英文内容并用中文总结：{truncated_results}"}
            ],
            temperature=0.7,
            max_tokens=1500,  # 增加token数以获取更详细的分析
            top_p=0.9
        )
        
        logger.info("分析报告生成完成")
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"分析过程中出现错误: {str(e)}")
        return f"分析过程中出现错误: {str(e)}"

# 使用缓存装饰器，缓存12小时
@lru_cache(maxsize=1000)
def cached_analysis(suburb, timestamp):
    """缓存分析结果，每12小时更新一次"""
    return analyze_with_openai(suburb)

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
        
        # 标准化输入
        suburb = suburb.lower().strip()
        if suburb == '3030':
            suburb = 'point cook'
        
        logger.info(f"搜索区域: {suburb}")
        
        # 获取搜索结果
        results = search_engine.search_suburb(suburb)
        logger.info("搜索完成，开始分析")
        
        # 使用缓存的分析结果
        timestamp = int(time.time() / (12 * 3600))  # 12小时更新一次
        analysis = cached_analysis(str(results), timestamp)
        
        return jsonify({
            'raw_results': results,
            'analysis': analysis
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