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
        system_prompt = """你是一个专业的墨尔本房地产分析师。请针对用户提供的区域，提供详细的购房因素分析报告。

分析要求：
1. 分析内容必须基于真实数据
2. 所有数据要标注年份
3. 数据要尽可能具体，包括具体金额、百分比等
4. 分析要客观公正，既要指出优势也要指出劣势
5. 对于缺失的数据要明确标注"数据缺失"

请按以下模板格式进行分析：

以下是针对[区域名]地区的购房因素分析，涵盖公共设施、教育资源、医疗资源和房价趋势，结合过去10年的发展与数据：

1. 公共设施与政府基建 
关键项目与拨款：

交通升级：
[列举主要道路升级项目，包括完工时间和投资金额]
[列举公共交通项目，如火车站、巴士路线等]

社区设施：
[列举社区中心、图书馆等项目，包括投资金额]
[列举购物中心和商业设施的发展]

公园与环保：
[列举环保项目和公园建设]
[说明政府投入]

未来规划：
[列举已确认的未来发展项目]
[分析对区域发展的潜在影响]

2. 教育资源
公立学校：
[列举本地公立学校，包括等级和评级]
[说明学位情况和申请建议]

私立学校：
[列举本地和邻近私立学校]
[提供学费范围]

教会学校：
[列举教会学校选择]
[说明特色和评价]

短板：
[指出教育资源的不足之处]

3. 医疗资源
公立医院：
[列举本地和邻近公立医院]
[说明车程时间和主要科室]

私立医疗机构：
[列举私立医院和诊所]
[说明提供的服务]

短板：
[指出医疗资源的不足之处]

4. 房价趋势与推动因素
增长数据：

独立屋（House）：
[列出2013年和2023年的中位价]
[计算年均增长率]

单元房（Unit）：
[列出过去10年的中位价]
[计算年均增长率]

增长推动因素：
[分析人口变化]
[分析基建影响]
[分析可负担性]
[分析土地开发情况]

风险提示：
[指出潜在风险因素]
[分析通勤情况]

5. 总结：[区域名]购房优劣势
[制作优劣势对比表格]

6. 建议：
[针对不同购房需求提供具体建议]
[提供选址建议]
[提供投资建议]

参考来源：
[列出数据来源网站]

范例答案：
以下是针对澳大利亚Point Cook地区的购房因素分析，涵盖公共设施、教育资源、医疗资源和房价趋势，结合过去10年的发展与数据：

1. 公共设施与政府基建
1.1 关键项目与拨款：

交通升级：
- Point Cook Road扩建：2016年完成车道拓宽，缓解交通拥堵。
- Williams Landing火车站（2013年启用）：连接墨尔本CBD的V/Line和地铁服务，提升通勤便利性。

社区设施：
- Saltwater社区中心（2018年）：政府拨款$1500万澳元，含图书馆、游泳池和体育场。
- Sanctuary Lakes购物中心扩建（2020年）：新增超市和零售设施。

公园与环保：
- Cheetham湿地保护计划：州政府持续拨款维护生态保护区。
- 多个新公园建设：如Featherbrook社区公园（2021年）。

1.2未来规划：
- Werribee地铁线延伸提案（规划中）：可能进一步改善西南区轨道交通。
- Altona North物流中心建设（邻近区）：预计带动就业和区域经济。

2. 教育资源
2.1 公立学校：
- 3所P-9学校（Point Cook College、Saltwater、Featherbrook），均配备现代化设施，学位紧张需提前申请。

2.2 私立学校：
- 邻近的Westbourne Grammar（车程10分钟）是首选，年学费约2万-3万澳元。

2.3 教会学校：
- Stella Maris Catholic小学（口碑良好），中学依赖邻近的Thomas Carr College（Tarneit）。

2.4 短板：
- 本地缺乏公立高中（10-12年级），需跨区就读Werribee或Tarneit。

3. 医疗资源
3.1 公立医院：
- Werribee Mercy Hospital（车程15分钟）：提供急诊、产科和基础专科服务。
- Sunshine Hospital（车程25分钟）：大型综合医院，含儿科和重症监护。

3.2 私立医疗机构：
- Point Cook Medical Centre：全科诊所和专科门诊。
- Sanctuary Lakes私立门诊：提供牙科、理疗等服务。

3.3 短板：
- 区域内无大型私立医院，复杂手术需前往墨尔本市中心或Geelong。

4. 房价趋势与推动因素
4.1增长数据：

独立屋（House）：
- 2013年中位价：$42万澳元
- 2023年中位价：$85万澳元（年均增长率约7.5%）

单元房（Unit）：
- 2013年中位价：$35万澳元
- 2023年中位价：$62万澳元（年均增长率约6%）

4.2 增长推动因素：
- 人口激增：10年内居民数量翻倍（现超6万人），年轻家庭占比高。
- 基建投资：交通和学校建设提升宜居性。
- 可负担性：相比墨尔本东区，房价较低吸引首购族和投资者。
- 土地开发：大量新住宅区（如Saltwater Coast）推高需求。

4.3 风险提示：
- 供应过剩：部分新区开发可能导致短期房价波动。
- 通勤依赖：80%居民需驾车或乘火车前往CBD（约40分钟车程）。

5. 总结：Point Cook购房优劣势 （用表格的形式总结，一栏是优势，一栏是劣势）

6. 建议：
- 优先选择成熟社区：如Point Cook Town Centre周边，配套更完善。
- 关注学区房：靠近Point Cook College或Saltwater P-9的房产溢价率较高。
- 长期持有：人口增长和基建升级支撑中长期房价上涨潜力。

7. 参考来源：
- 房价查询：Domain 或 CoreLogic
- 政府规划：Wyndham City Council"""

        logger.info("开始生成分析报告...")
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析{suburb}区域的购房因素"}
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