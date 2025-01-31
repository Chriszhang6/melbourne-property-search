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

app = Flask(__name__)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

search_engine = PropertySearchEngine()

def analyze_with_openai(suburb):
    """使用OpenAI分析区域信息"""
    try:
        # System prompt
        system_prompt = """你是一个专业的澳大利亚房地产分析师。请针对用户提供的区域，提供详细的购房因素分析报告。

分析要求：
1. 分析内容必须基于真实数据，你可以使用网络搜索获取最新数据
2. 所有数据要标注年份，确保使用最近的数据
3. 数据要尽可能具体，包括具体金额、百分比等
4. 分析要客观公正，既要指出优势也要指出劣势
5. 对于缺失的数据要明确标注"数据缺失"
6. 房价趋势分析要基于过去10年的数据，如果有些数据较旧，请主动搜索更新
7. 总结部分要用表格形式展示优劣势对比"""

        # User prompt template
        user_prompt = """以下是针对[区域名]地区的购房因素分析，涵盖公共设施、教育资源、医疗资源和房价趋势，结合过去10年的发展与数据：

1. 公共设施与政府基建 
1.1 关键项目与拨款：

交通升级：
[列举主要道路升级项目，包括完工时间和投资金额]
[列举公共交通项目，如火车站、巴士路线等]

社区设施：
[列举社区中心、图书馆等项目，包括投资金额]
[列举购物中心和商业设施的发展]

公园与环保：
[列举环保项目和公园建设]
[说明政府投入]

1.2 未来规划：
[列举已确认的未来发展项目]
[分析对区域发展的潜在影响]

2. 教育资源
2.1 公立学校：
[列举本地公立学校，包括等级和评级]
[说明学位情况和申请建议]

2.2 私立学校：
[列举本地和邻近私立学校]
[提供学费范围]

2.3 教会学校：
[列举教会学校选择]
[说明特色和评价]

2.4 短板：
[指出教育资源的不足之处]

3. 医疗资源
3.1 公立医院：
[列举本地和邻近公立医院]
[说明车程时间和主要科室]

3.2 私立医疗机构：
[列举私立医院和诊所]
[说明提供的服务]

3.3 短板：
[指出医疗资源的不足之处]

4. 房价趋势与推动因素
4.1 增长数据：

独立屋（House）：
[列出过去10年的中位价变化]
[计算年均增长率]

4.2 单元房（Unit）：
[列出过去10年的中位价变化]
[计算年均增长率]

4.3 增长推动因素：
[分析人口变化]
[分析基建影响]
[分析可负担性]
[分析土地开发情况]

4.4 风险提示：
[指出潜在风险因素]
[分析通勤情况]

5. 总结：[区域名]购房优劣势

优势 | 劣势
--- | ---
[优势1] | [劣势1]
[优势2] | [劣势2]
[优势3] | [劣势3]

6. 建议：
[针对不同购房需求提供具体建议]
[提供选址建议]
[提供投资建议]

参考来源：
[列出数据来源网站]"""

        # 替换模板中的区域名
        user_prompt = user_prompt.replace("[区域名]", suburb)

        # 添加提醒使用最新数据
        current_data_reminder = f"请分析{suburb}区域的购房因素。请注意，现在是2024年，你可以使用网络搜索获取最新数据，尤其是房价趋势分析要基于最近10年（2014-2024）的数据。如果发现数据较旧，请主动搜索更新。请严格按照提供的模板格式回复，确保优劣势使用表格形式展示。"

        # 调用OpenAI API
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": current_data_reminder},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API调用失败: {str(e)}")
        raise Exception("分析生成失败，请稍后重试")

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
        
        logger.info(f"分析区域: {suburb}")
        
        # 直接使用OpenAI分析
        analysis = analyze_with_openai(suburb)
        
        return jsonify({
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