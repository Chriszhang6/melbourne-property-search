from flask import Flask, render_template, request, jsonify, send_from_directory
from search_engine import PropertySearchEngine
import os
from openai import OpenAI
import time
import re
from dotenv import load_dotenv
import logging
import sys
from datetime import datetime, timedelta
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 检查 OpenAI API key
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    logger.error("未找到 OPENAI_API_KEY 环境变量")
    raise ValueError("未找到 OPENAI_API_KEY 环境变量")

# 配置OpenAI API
client = OpenAI(api_key=api_key)

# API使用量跟踪
MONTHLY_BUDGET = 5.0  # 每月预算（美元）
COST_PER_1K_INPUT_TOKENS = 0.0015  # GPT-3.5-turbo 输入价格
COST_PER_1K_OUTPUT_TOKENS = 0.002   # GPT-3.5-turbo 输出价格

class APIUsageTracker:
    def __init__(self, budget_limit=MONTHLY_BUDGET):
        self.budget_limit = budget_limit
        self.usage_file = 'demo_api_usage.json'  # 改为演示版本专用的文件
        self.load_usage()

    def load_usage(self):
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    self.usage_data = json.load(f)
            else:
                self.reset_usage_data()
        except Exception as e:
            logger.error(f"加载使用量数据失败: {str(e)}")
            self.reset_usage_data()

    def reset_usage_data(self):
        """重置使用量数据"""
        self.usage_data = {
            'current_month': datetime.now().strftime('%Y-%m'),
            'total_cost': 0.0,
            'requests': [],
            'api_key_last_4': api_key[-4:]  # 记录API key的最后4位以便识别
        }

    def save_usage(self):
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            logger.error(f"保存使用量数据失败: {str(e)}")

    def calculate_cost(self, input_tokens, output_tokens):
        input_cost = (input_tokens / 1000) * COST_PER_1K_INPUT_TOKENS
        output_cost = (output_tokens / 1000) * COST_PER_1K_OUTPUT_TOKENS
        return input_cost + output_cost

    def check_and_update_month(self):
        current_month = datetime.now().strftime('%Y-%m')
        if self.usage_data['current_month'] != current_month:
            self.usage_data = {
                'current_month': current_month,
                'total_cost': 0.0,
                'requests': []
            }
            self.save_usage()

    def can_make_request(self):
        self.check_and_update_month()
        return self.usage_data['total_cost'] < self.budget_limit

    def track_request(self, input_tokens, output_tokens, suburb):
        cost = self.calculate_cost(input_tokens, output_tokens)
        self.usage_data['total_cost'] += cost
        self.usage_data['requests'].append({
            'timestamp': datetime.now().isoformat(),
            'suburb': suburb,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': cost
        })
        self.save_usage()
        return cost

# 创建API使用量跟踪器
usage_tracker = APIUsageTracker()

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
        
        system_prompt = """你是一个专业的澳大利亚房地产分析师。请针对用户提供的区域，提供详细的购房因素分析报告。

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
[列举本地和邻近教会学校，属于什么宗教]
[举例提供学费范围]

## 短板
[指出本地学校的不足之处，参考没有10-12年级，或者没有公立高中，或者没有教会学校，或者没有私立学校]

# 医疗资源
## 公立医院
[列举本地和邻近公立医院]
[说明车程时间和主要科室]

## 私立医疗机构
[列举私立医院和诊所]
[说明提供的服务]

## 短板
[指出该区域的不足之处]

# 治安状况
## 犯罪数据
[列出最近3年的犯罪率统计]
[与该州平均水平对比]

## 警力配置
[说明当地警局位置和规模]
[列举周边警力资源]

## 社区安全
[分析社区安全措施]
[说明邻里守望计划]

## 重点关注
[列举需要特别注意的安全隐患]
[提供安全建议]

# 房价趋势与推动因素
## 单元房(Unit)
[列出过去10年的中位价]
[计算年均增长率]

## 独立屋(House)
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

[列出数据来源网站]

范例答案：
以下是针对澳大利亚Point Cook地区的购房因素分析，涵盖公共设施、教育资源、医疗资源和房价趋势，结合过去10年的发展与数据：

# 公共设施与政府基建
## 关键项目与拨款:

交通升级：
- Point Cook Road扩建：2016年完成车道拓宽，缓解交通拥堵。
- Williams Landing火车站（2013年启用）：连接墨尔本CBD的V/Line和地铁服务，提升通勤便利性。

社区设施：
- Saltwater社区中心（2018年）：政府拨款$1500万澳元，含图书馆、游泳池和体育场。
- Sanctuary Lakes购物中心扩建（2020年）：新增超市和零售设施。

公园与环保：
- Cheetham湿地保护计划：州政府持续拨款维护生态保护区。
- 多个新公园建设：如Featherbrook社区公园（2021年）。

## 未来规划:

- Werribee地铁线延伸提案（规划中）：可能进一步改善西南区轨道交通。
- Altona North物流中心建设（邻近区）：预计带动就业和区域经济。

# 教育资源
## 公立学校:

- 3所P-9学校（Point Cook College、Saltwater、Featherbrook），均配备现代化设施，学位紧张需提前申请。

## 私立学校:

- 邻近的Westbourne Grammar（车程10分钟）是首选，年学费约2万-3万澳元。

## 教会学校:

- Stella Maris Catholic小学（口碑良好），中学依赖邻近的Thomas Carr College（Tarneit）。

## 短板:

- 本地缺乏公立高中（10-12年级），需跨区就读Werribee或Tarneit

# 医疗资源
# ## 公立医院:

- Werribee Mercy Hospital（车程15分钟）：提供急诊、产科和基础专科服务。
- Sunshine Hospital（车程25分钟）：大型综合医院，含儿科和重症监护。

## 私立医疗机构:

- Point Cook Medical Centre：全科诊所和专科门诊。
- Sanctuary Lakes私立门诊：提供牙科、理疗等服务。

## 短板:

- 区域内无大型私立医院，复杂手术需前往墨尔本市中心或Geelong。

# 房价趋势与推动因素
## 单元房（Unit）:

- 过去10年的中位价变化
- 年均增长率分析

## 独立屋（House）:

- 过去10年的中位价变化
- 年均增长率分析

## 增长推动因素:

- 人口激增：10年内居民数量翻倍（现超6万人），年轻家庭占比高。
- 基建投资：交通和学校建设提升宜居性。
- 可负担性：相比墨尔本东区，房价较低吸引首购族和投资者。
- 土地开发：大量新住宅区（如Saltwater Coast）推高需求。

## 风险提示:

- 供应过剩：部分新区开发可能导致短期房价波动。
- 通勤依赖：80%居民需驾车或乘火车前往CBD（约40分钟车程）。

# 总结

- 优势：交通便利，基础设施完善，自然环境优美，发展潜力大
- 劣势：教育资源有限，医疗机构相对不足，房价增长速度相对缓慢

# 建议

- 优先选择成熟社区：如Point Cook Town Centre周边，配套更完善。
- 关注学区房：靠近Point Cook College或Saltwater P-9的房产溢价率较高。
- 长期持有：人口增长和基建升级支撑中长期房价上涨潜力。

# 参考来源

- 房价查询：Domain 或 CoreLogic
- 政府规划：Wyndham City Council
"""

        logger.info("开始生成分析报告...")
        
        # 调用OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请分析{suburb}区域的购房因素"}
            ],
            temperature=0.2,  # 降低创造性，提高稳定性
            max_tokens=2000,
            top_p=0.8
        )
        
        # 记录API调用时间和token使用情况
        end_time = time.time()
        logger.info(f"分析报告生成完成，用时: {end_time - start_time:.2f}秒，使用tokens: {response.usage.total_tokens}")
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API调用失败: {str(e)}")
        raise Exception("生成分析报告时出错，请稍后重试")

@app.route('/')
def home():
    return render_template('index.html')

# 系统提示词
SYSTEM_PROMPT = """你是一个专业的澳大利亚房地产分析师。请针对用户提供的区域，提供详细的购房因素分析报告。

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
[列举本地和邻近教会学校，属于什么宗教]
[举例提供学费范围]

## 短板
[指出本地学校的不足之处，参考没有10-12年级，或者没有公立高中，或者没有教会学校，或者没有私立学校]

# 医疗资源
## 公立医院
[列举本地和邻近公立医院]
[说明车程时间和主要科室]

## 私立医疗机构
[列举私立医院和诊所]
[说明提供的服务]

## 短板
[指出该区域的不足之处]

# 治安状况
## 犯罪数据
[列出最近3年的犯罪率统计]
[与该州平均水平对比]

## 警力配置
[说明当地警局位置和规模]
[列举周边警力资源]

## 社区安全
[分析社区安全措施]
[说明邻里守望计划]

## 重点关注
[列举需要特别注意的安全隐患]
[提供安全建议]

# 房价趋势与推动因素
## 单元房(Unit)
[列出过去10年的中位价]
[计算年均增长率]

## 独立屋(House)
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

@app.route('/search', methods=['POST'])
def search():
    try:
        # 检查是否超出预算
        if not usage_tracker.can_make_request():
            logger.error("已达到本月API使用限额")
            return jsonify({'error': '已达到本月使用限额，请下月再试'}), 429

        data = request.get_json()
        if data is None:
            logger.error("无效的JSON数据")
            return jsonify({'error': '请求格式错误'}), 400
            
        suburb = data.get('suburb', '')
        
        if not suburb:
            logger.error("未提供区域名称")
            return jsonify({'error': '请输入区域名称或邮编'}), 400
        
        suburb = standardize_suburb(suburb)
        logger.info(f"开始分析区域: {suburb}")
        
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"请分析{suburb}区域的购房因素"}
                ],
                temperature=0.2,
                max_tokens=2000,
                top_p=0.8
            )
            
            # 跟踪API使用量
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = usage_tracker.track_request(input_tokens, output_tokens, suburb)
            
            logger.info(f"API调用成功，成本: ${cost:.4f}")
            
            if not response.choices or not response.choices[0].message:
                logger.error("OpenAI返回了无效的响应")
                return jsonify({'error': '生成分析报告失败，请重试'}), 500
            
            analysis = response.choices[0].message.content
            return jsonify({
                'analysis': analysis,
                'disclaimer': '注意：本报告中的数据仅供参考，具体信息请以官方发布为准。'
            })
            
        except Exception as api_error:
            logger.error(f"OpenAI API调用失败: {str(api_error)}")
            return jsonify({'error': '生成分析报告时出错，请稍后重试'}), 500
            
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}")
        return jsonify({'error': '服务器内部错误，请稍后重试'}), 500

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

@app.route('/usage', methods=['GET'])
def get_usage():
    """获取API使用情况"""
    try:
        return jsonify({
            'current_month': usage_tracker.usage_data['current_month'],
            'total_cost': round(usage_tracker.usage_data['total_cost'], 4),
            'budget_limit': MONTHLY_BUDGET,
            'remaining_budget': round(MONTHLY_BUDGET - usage_tracker.usage_data['total_cost'], 4),
            'api_key_last_4': usage_tracker.usage_data.get('api_key_last_4', 'N/A'),  # 显示API key的最后4位
            'version': 'demo'  # 标识这是演示版本
        })
    except Exception as e:
        logger.error(f"获取使用情况失败: {str(e)}")
        return jsonify({'error': '获取使用情况失败'}), 500

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