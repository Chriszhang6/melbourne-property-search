from flask import Flask, render_template, request, jsonify, send_from_directory
from search_engine import PropertySearchEngine
import os
import openai
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
openai.api_key = os.getenv('OPENAI_API_KEY')

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
        system_prompt = """你是一个专业的墨尔本房地产分析师。请针对用户提供的区域，提供详细的购房因素分析报告。

分析要求：
1. 分析内容必须基于真实数据
2. 所有数据要标注年份
3. 数据要尽可能具体，包括具体金额、百分比等
4. 分析要客观公正，既要指出优势也要指出劣势
5. 对于缺失的数据要明确标注"数据缺失"
6. 对于政府投资项目，必须标注具体投资金额，如果无法获取则标注"投资金额未公开"

请按以下模板格式进行分析：

以下是针对[区域名]地区的购房因素分析，涵盖公共设施、教育资源、医疗资源和房价趋势，结合过去10年的发展与数据：

# 公共设施与政府基建
## 关键项目与拨款

交通升级：
[列举主要道路升级项目，包括完工时间和具体投资金额]
[列举公共交通项目，如火车站、巴士路线等，标注投资金额]

社区设施：
[列举社区中心、图书馆等项目，标注具体投资金额]
[列举购物中心和商业设施的发展，标注投资规模]

公园与环保：
[列举环保项目和公园建设，标注投资金额]
[说明政府年度维护投入]

## 未来规划
[列举已确认的未来发展项目，标注预算金额]
[分析对区域发展的潜在影响]

# 教育资源
## 公立学校
[列举本地公立学校，包括等级和评级]
[说明学位情况和申请建议]

## 私立学校
[列举本地和邻近私立学校]
[提供学费范围]

## 教会学校
[列举教会学校选择]
[说明特色和评价]

## 短板
[指出教育资源的不足之处]

# 医疗资源
## 公立医院
[列举本地和邻近公立医院]
[说明车程时间和主要科室]

## 私立医疗机构
[列举私立医院和诊所]
[说明提供的服务]

## 短板
[指出医疗资源的不足之处]

# 房价趋势与推动因素
## 单元房（Unit）
[列出过去10年的中位价]
[计算年均增长率]

## 独立屋（House）
[列出过去10年的中位价]
[计算年均增长率]

## 增长推动因素
[分析人口变化]
[分析基建影响]
[分析可负担性]
[分析土地开发情况]

## 风险提示
[指出潜在风险因素]
[分析通勤情况]

# 总结
优势：[列出主要优势，用逗号分隔]
劣势：[列出主要劣势，用逗号分隔]

# 建议
[针对不同购房需求提供具体建议]
[提供选址建议]
[提供投资建议]

# 参考来源
[列出数据来源网站]"""

        logger.info("开始生成分析报告...")
        
        # 使用新版本的API调用方式
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析{suburb}区域的购房因素"}
            ],
            temperature=0.2,  # 降低创造性，提高稳定性
            max_tokens=2000,
            top_p=0.8
        )

        end_time = time.time()
        duration = end_time - start_time
        tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 'unknown'
        
        logger.info(f"分析报告生成完成，用时: {duration:.2f}秒，使用tokens: {tokens_used}")
        return response.choices[0].message.content

    except Exception as e:
        logger.error(f"分析过程中出现错误: {str(e)}")
        return f"分析过程中出现错误: {str(e)}"

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
        response = openai.ChatCompletion.create(
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