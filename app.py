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
        
        system_prompt = """你是一个专业的墨尔本房地产分析师。我会提供一些搜索结果，包含了区域的各方面信息。请仔细阅读这些英文内容，并按以下要求进行深度分析：

分析要求：
1. 仔细阅读每条搜索结果的英文内容
2. 提取关键数据和重要信息
3. 将信息翻译成中文并按主题整理
4. 注意信息的时效性，优先使用最新数据
5. 对数据进行交叉验证和对比分析

请按以下格式进行分析：

1. 教育资源分析：
   - 列出所有主要学校（公立/私立）及其等级
   - NAPLAN考试成绩和排名
   - VCE成绩（如果有）
   - 特色课程和项目
   - 师生比例和教学质量评估
   - 学校设施和特色项目

2. 医疗资源分析：
   - 主要医疗机构的具体位置和规模
   - 各医院的专科特色和服务范围
   - 急诊服务的响应时间和质量
   - 社区医疗中心的分布
   - 专科诊所的类型和数量
   - 医疗资源的可及性评估

3. 基础设施发展：
   - 最近完成的重大项目
   - 正在进行的发展计划
   - 政府投资金额和用途
   - 社区设施升级计划
   - 交通设施改善项目
   - 未来发展规划

4. 治安状况分析：
   - 按年份列出犯罪率变化
   - 主要犯罪类型的具体数据
   - 与周边区域的对比分析
   - 警力配置和反应时间
   - 社区安全措施
   - 高发案件区域和时段
   - 改善趋势和预防措施

5. 房产市场分析：
   - 最新房价中位数及变化趋势
   - 不同类型房产的价格区间
   - 租金回报率数据
   - 市场供需状况
   - 投资潜力评估
   - 未来增长预测

注意事项：
1. 每个分析点都需要具体数据支持
2. 标注数据的来源年份
3. 指出数据的可靠性和局限性
4. 突出异常值和重要趋势
5. 对矛盾数据进行说明和分析

最后，请在分析报告末尾添加"参考来源"部分，按类别列出所有引用的链接。"""

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