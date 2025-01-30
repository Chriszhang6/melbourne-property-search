from flask import Flask, render_template, request, jsonify
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

app = Flask(__name__)
search_engine = PropertySearchEngine()

def analyze_with_openai(search_results):
    """使用OpenAI分析搜索结果"""
    try:
        max_input_length = 4000
        truncated_results = str(search_results)[:max_input_length] + "..."
        
        system_prompt = """你是一个专业的墨尔本房地产分析师。我会提供一些搜索结果，包含了区域的各方面信息。请仔细阅读这些英文内容，并按以下格式进行分析：

【公立学校】
- 列出主要公立学校，包括：
  * 学校全名（年级范围）
  * 一句话描述特色/优势
  * 如果是邻近区域的学校，标注"邻近区"

【私立学校】
- 列出主要私立学校，包括：
  * 学校全名（年级范围）
  * 一句话描述特色/优势
  * 如果是邻近区域的学校，标注"邻近"
  * 费用范围（如有）

【教会学校】
- 列出主要教会学校，包括：
  * 学校全名（年级范围）
  * 宗教背景
  * 一句话描述特色/优势
  * 如果是邻近区域的学校，标注位置

【教育资源】
社区支持：列出主要的社区教育设施（科技中心/图书馆/学习中心等）
课外资源：列出主要的课外教育资源（体育/艺术/补习等）

优势总结（用✅标记）
- 总结3-4个该区域教育资源的主要优势
- 每个优势用简短的词组描述

注意事项：
- 如果学校位于邻近区域，必须标注
- 重点关注最新建成或在建的教育设施
- 标注任何需要特别注意的信息（如学区划分）

分析要求：
1. 信息必须准确，每个学校信息都要有具体来源支持
2. 优先展示最新信息
3. 重点突出特色项目和设施
4. 保持描述简洁精炼

最后，请在分析报告末尾添加"参考来源"部分，列出所有引用的链接。"""

        logger.info("开始生成分析报告...")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"这是搜索结果，请仔细分析其中的英文内容并用中文总结：{truncated_results}"}
            ],
            temperature=0.7,
            max_tokens=2000,  # 增加token数以获取更详细的分析
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