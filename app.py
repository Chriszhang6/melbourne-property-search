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
        logger.info("开始生成分析报告...")
        
        # 调用OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"请分析{suburb}区域的购房因素"}
            ],
            temperature=0.2,  # 降低创造性，提高稳定性
            max_tokens=3000,
            top_p=0.8
        )
        
        # 记录API调用时间和token使用情况
        end_time = time.time()
        logger.info(f"分析报告生成完成，用时: {end_time - start_time:.2f}秒，使用tokens: {response.usage.total_tokens}")
        
        # 跟踪API使用量
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = usage_tracker.track_request(input_tokens, output_tokens, suburb)
        logger.info(f"API调用成本: ${cost:.4f}")
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI API调用失败: {str(e)}")
        raise Exception("生成分析报告时出错，请稍后重试")

@app.route('/')
def home():
    return render_template('index.html')

# 系统提示词
SYSTEM_PROMPT = """你是一个专业的澳大利亚房地产分析师。请针对用户提供的区域，提供详细的购房因素分析报告。

<你的任务>
分析要求：
1. 分析内容必须基于真实数据
2. 所有数据要标注年份
3. 数据要尽可能具体，包括具体金额、百分比等
4. 分析要客观公正，既要指出优势也要指出劣势
5. 对于缺失的数据要明确标注"数据缺失"
6. 对于政府投资项目，必须标注具体投资金额，如果无法获取则标注"投资金额未公开"
7. 房价趋势部分需要过去十年的数据，包括单元房和独立屋的中位价及增长率。推动因素可能包括地理位置、学区、基础设施等，风险因素可能涉及经济波动或政策变化。这里需要参考房产网站如Domain或CoreLogic的数据

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
[列举需要特别注意的安全问题]

# 房价趋势与推动因素
## 单元房(Unit)
[过去10年的中位价走势]
[年均增长率]

## 独立屋(House)
[过去10年的中位价走势]
[年均增长率]

## 增长推动因素
[分析推动房价变化的主要因素]

## 风险提示
[列举可能影响房价的风险因素]

# 总结
优势：[列举主要优势，用逗号分隔]
劣势：[列举主要劣势，用逗号分隔]

# 建议
[针对不同类型的购房者提供具体建议]

# 参考来源
[列举数据来源]
</你的任务>

<答案模版1>
下面是我提供的答案模版参考，以用户搜索Kew 3101 为例。
以下是针对澳大利亚墨尔本 Kew 3101 区的详细分析，涵盖公共设施、教育资源、医疗资源、治安状况和房价趋势：

# 公共设施与政府基建
## 关键项目与拨款

交通升级：
- Eastern Freeway升级（2023年完工）：投资$15亿澳元，新增智能交通管理系统，缓解Kew至CBD拥堵。
- Kew火车站升级（2021年）：州政府拨款$800万澳元，提升无障碍设施和候车区。
- 电车路线78路优化（2022年）：延长运营时间，加密班次（投资$300万澳元）。

社区设施：
- Kew社区中心（2019年翻新）：投资$500万澳元，新增健身房和老年人活动室。
- High Street购物区改造（2020年）：投资$2000万澳元，引入高端零售品牌和餐饮。

公园与环保：
- Studley Park生态修复（2022年）：州政府拨款$120万澳元，恢复雅拉河岸植被。
- Kew Billabong保护区：年度维护预算$50万澳元，提供步行道和野餐区。

## 未来规划
- Kew东区轻轨提案（2030年规划）：预算$3亿澳元，连接Kew至Doncaster，预计提升通勤便利性。
- Kew Civic Precinct开发（2025年启动）：拟建多功能文化中心（含图书馆和剧院），预算$1.2亿澳元。


# 教育资源
## 公立学校
- Kew Primary School（P-6，NAPLAN排名前10%）：学位紧张，需提前1年申请。
- Kew High School（7-12，2023年VCE排名第15%）：提供STEM精英班，本地生优先录取。

## 私立学校
- Xavier College（P-12，男校）：年学费35,000-45,000澳元，IB/VCE双轨制。
- Methodist Ladies' College（MLC）（P-12，女校）：年学费30,000-40,000澳元，艺术和体育项目突出。

## 教会学校
- Genazzano FCJ College（P-12，天主教女校）：年学费28,000-38,000澳元。
- Trinity Grammar School（P-12，圣公会男校）：年学费33,000-43,000澳元。

## 短板
- 缺乏非精英公立高中：仅Kew High School为公立，竞争激烈。
- 私立学校学费高昂：本地无中低价位私立学校。

# 医疗资源
## 公立医院
- St Vincent's Hospital（车程10分钟）：综合医院，以心外科和肿瘤科著称，24小时急诊。
- Royal Melbourne Hospital（车程15分钟）：维州顶级公立医院，提供重症监护和专科服务。

## 私立医疗机构
- Epworth Freemasons Hospital（车程8分钟）：提供手术、产科和康复服务。
- Kew Private Consulting Suites：专科门诊（骨科、皮肤科等）。

## 短板
- 无本地大型公立医院：依赖邻近区医院，紧急情况需10分钟以上车程。

# 治安状况
## 犯罪数据
- 2023年犯罪率：每千人6.2起（全州平均9.8起），财产犯罪占比60%。
- 主要犯罪类型：盗窃（40%）、车辆盗窃（25%）。

## 警力配置
- Kew Police Station（258 High Street）：配备20名警员，覆盖Kew及周边区域。
- 邻近资源：Richmond警局（5公里）提供快速支援。

## 社区安全
- 邻里守望计划：覆盖80%街道，定期举办安全讲座。
- 监控系统：High Street商业区安装智能摄像头（2022年升级）。

## 重点关注
- 夜间停车安全：建议安装车辆防盗装置。

# 房价趋势与推动因素
## 单元房(Unit)
过去10年的中位价走势（数据来源：CoreLogic，2015–2024）
- 2015 年：约 A$520,000
- 2016 年：约 A$525,000
- 2017 年：约 A$535,000
- 2018 年：约 A$545,000
- 2019 年：约 A$555,000
- 2020 年：约 A$565,000
- 2021 年：约 A$580,000
- 2022 年：约 A$595,000
- 2023 年：约 A$610,000
- 2024 年：约 A$625,000
年均增长率：约 2.3%（基于 2015 至 2024 年数据计算）

## 独立屋(House)
过去10年的中位价走势（数据来源：CoreLogic，2015–2024）

- 2015 年：约 A$1,800,000
- 2016 年：约 A$1,830,000
- 2017 年：约 A$1,860,000
- 2018 年：约 A$1,890,000
- 2019 年：约 A$1,920,000
- 2020 年：约 A$1,950,000
- 2021 年：约 A$1,980,000
- 2022 年：约 A$2,010,000
- 2023 年：约 A$2,040,000
- 2024 年：约 A$2,070,000
年均增长率：约 1.6%（基于 2015 至 2024 年数据计算）

## 增长推动因素
- 优质教育资源：Kew 拥有多所知名学校（例如 Xavier College 等），吸引了许多重视子女教育的家庭，进而对房产需求形成长期支撑。
- 低密度社区：历史建筑保护政策限制新房供应。
- 交通便利：10分钟至CBD，Eastern Freeway直达东区。

## 风险提示
- 利率敏感：高总价房产易受加息冲击。
- 开发限制：遗产保护区限制土地再开发。

# 总结
优势：优质教育资源，低犯罪率，交通便利，社区文化浓厚。
劣势：房价高昂，医疗依赖外区，缺乏平价住房。

# 建议
- 家庭购房者：优先学区房（近Kew High School或私立学校）。
- 投资者：关注遗产建筑翻新项目（长期增值潜力）。
- 退休人士：选择单元房（低维护成本，近社区中心）。

# 参考来源
- 房价数据：Domain Kew 3101
- 犯罪率统计：Crime Statistics Agency Victoria
- 学校排名：Better Education
- 政府规划：Boroondara City Council
</答案模版1>

<答案模版2>
下面是我提供的答案模版参考，以用户搜索Balwyn 3103 为例。
以下是针对澳大利亚墨尔本 Balwyn 3103 区的详细分析，涵盖公共设施、教育资源、医疗资源、治安状况和房价趋势：

# 公共设施与政府基建
## 关键项目与拨款

交通升级：
- Burke Road拓宽工程（2022年完工）：投资$1.2亿澳元，新增双向四车道，缓解Balwyn至CBD交通压力。
- 电车109路线优化（2021年）：升级信号灯系统，缩短高峰时段通勤时间（投资$500万澳元）。   
- Belmore Road巴士枢纽（2020年）：新增智能候车亭和实时信息屏（投资$200万澳元）。

社区设施：
- Balwyn社区中心（2018年翻新）：投资$800万澳元，新增多功能活动厅和儿童游乐区。
- Balwyn购物中心升级（2023年）：投资$1500万澳元，引入Coles Local和精品零售店。

公园与环保：
- Koonung Creek生态修复（2021年）：州政府拨款$90万澳元，重建湿地并增设步道。
- Balwyn Park年度维护：预算$30万澳元，维护网球场和野餐设施。

## 未来规划
- Balwyn地铁站提案（2035年规划）：预算$4亿澳元，拟连接Suburban Rail Loop东线。
- Whitehorse Road商业区开发（2026年启动）：拟建混合用途综合体（含办公和住宅），预算$2亿澳元。


# 教育资源
## 公立学校
- Balwyn High School（7-12，2023年VCE排名前5%）：维州顶尖公立中学，精英班竞争激烈，本地生需提前2年注册。
- Balwyn Primary School（P-6, NAPLAN排名前10%）：学位紧张，优先学区范围内居民。

## 私立学校
- Fintona Girls' School（P-12，女校）：年学费28,000-38,000澳元，以学术成绩和辩论项目闻名。
- Camberwell Grammar School（邻近区，男校）：年学费35,000−35,000−45,000澳元，提供IB课程。

## 教会学校
- St Bede's Primary School（P-6，天主教）：年学费8,000−8,000−12,000澳元，社区活动丰富。
- Carey Baptist Grammar School（邻近区，跨宗教）：年学费30,000−30,000−40,000澳元，K-12一贯制。

## 短板
- 公立小学学位不足：Balwyn Primary需提前排队，跨区申请难度高。
- 私立学校集中高价：缺乏中低价位选择。 

# 医疗资源
## 公立医院
- Box Hill Hospital（车程10分钟）：大型综合医院，以心血管科和急诊服务著称。
- Royal Melbourne Hospital（车程20分钟）：维州顶级公立医院，提供专科手术和重症监护。

## 私立医疗机构
- Epworth Cliveden Private Hospital（车程8分钟）：高端私立医院，擅长骨科和康复治疗。
- Balwyn Medical Centre：全科诊所和专科门诊（如皮肤科、儿科）。

## 短板
- 无本地急诊中心：紧急情况需依赖Box Hill或Royal Melbourne Hospital。

# 治安状况
## 犯罪数据
- 2023年犯罪率：每千人5.8起（全州平均9.8起），暴力犯罪占比15%。
- 主要犯罪类型：入室盗窃（35%）、车辆盗窃（20%）。

## 警力配置
- Balwyn Police Station（Whitehorse Road）：配备15名警员，覆盖Balwyn及Camberwell区域。
- 邻近资源：Box Hill警局（7公里）提供支援。

## 社区安全
- 邻里守望计划：覆盖70%社区，定期组织安全巡逻。
- 智能安防系统：2023年推广家庭联网报警装置（政府补贴50%费用）。

## 重点关注
- 节假日盗窃风险：建议安装防盗摄像头和警报系统。

# 房价趋势与推动因素
## 单元房(Unit)
过去10年的中位价走势（数据来源：CoreLogic，2015–2024）
- 2015 年： A$700,000
- 2016 年： A$710,000
- 2017 年： A$720,000
- 2018 年： A$735,000
- 2019 年： A$750,000
- 2020 年： A$765,000
- 2021 年： A$780,000
- 2022 年： A$795,000
- 2023 年： A$810,000
- 2024 年： A$825,000
年均增长率： 约 2.0%（基于 2015–2024 数据计算）

## 独立屋(House)
过去10年的中位价走势（数据来源：CoreLogic，2015–2024）
- 2015 年： A$2,500,000
- 2016 年： A$2,540,000
- 2017 年： A$2,580,000
- 2018 年： A$2,620,000
- 2019 年： A$2,660,000
- 2020 年： A$2,700,000
- 2021 年： A$2,740,000
- 2022 年： A$2,780,000
- 2023 年： A$2,820,000
- 2024 年： A$2,860,000
年均增长率： 约 1.9%（基于 2015–2024 数据计算）

## 增长推动因素
- 顶尖学区：Balwyn High School拉动房价溢价（学区房比非学区贵20%-30%）。
- 低密度住宅：80%为独立屋，土地稀缺性推高需求。
- 交通便利：15分钟至CBD，109路电车直达市中心。

## 风险提示
- 利率敏感：高杠杆买家可能受加息冲击。
- 遗产保护限制：部分区域禁止高层开发，限制新房供应。

# 总结
优势：顶尖公立学校，低犯罪率，社区环境宜居，交通便利。
劣势：房价高昂，医疗资源依赖外区，缺乏多元化住房选择。

# 建议
- 家庭购房者：优先Balwyn High School学区（如Buchanan Avenue周边）。
- 投资者：关注翻新潜力大的遗产住宅（如1930年代别墅）。
- 首购族：考虑单元房（如Whitehorse Road公寓，总价较低）。

# 参考来源
- 房价数据：CoreLogic 房价数据（2015–2024）
- 犯罪率统计：Crime Statistics Agency Victoria
- 学校排名：Better Education
- 政府规划：Boroondara City Council
</答案模版2>

"""

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
            # 直接使用OpenAI分析
            analysis = analyze_with_openai(suburb)
            
            if not analysis:
                logger.error("生成的分析报告为空")
                return jsonify({'error': '生成分析报告失败，请重试'}), 500
            
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