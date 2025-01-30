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
2. 提取具体的数据、名称和重要信息
3. 将信息翻译成中文并按主题整理
4. 注意信息的时效性，标注信息的具体日期
5. 对数据进行交叉验证和可信度分析

请按以下格式进行分析：

1. 教育资源分析：
   A. 公立学校：
      - 列出每所公立学校的具体名称
      - 最新的NAPLAN成绩和排名
      - 学校规模（学生人数）
      - 特色项目和设施
      - 最新的重大新闻（如有）
   
   B. 私立学校：
      - 列出每所私立学校的具体名称
      - 学费范围（如有）
      - VCE成绩和排名（如有）
      - 特色课程和设施
      - 最新的发展计划
   
   C. 教会学校：
      - 列出每所教会学校的具体名称
      - 宗教背景
      - 教学特色
      - 设施情况
   
   D. 幼儿教育：
      - 主要的托儿所和幼儿园名称
      - 评分和评价
      - 收费标准（如有）

2. 医疗资源分析：
   A. 医院：
      - 医院具体名称和位置
      - 最新扩建或升级新闻
      - 特色科室和服务
      - 急诊等待时间（如有）
      - 病床数量（如有）
   
   B. 社区医疗中心：
      - 中心名称和位置
      - 提供的主要服务
      - 最新的服务更新
   
   C. 专科诊所：
      - 主要专科诊所名称
      - 专科类型
      - 新增服务或设施

3. 基础设施发展：
   A. 已完成项目：
      - 项目具体名称
      - 完工时间
      - 具体投资金额
      - 项目规模和影响
   
   B. 在建项目：
      - 项目名称和位置
      - 预算金额
      - 预计完工时间
      - 项目详细内容
   
   C. 规划中项目：
      - 项目名称
      - 预估投资
      - 预期影响
      - 时间表

注意事项：
1. 每个信息点都需要标注具体数据来源
2. 标注信息的具体日期
3. 对信息可靠性进行评估
4. 说明数据的局限性
5. 突出重要的最新发展

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