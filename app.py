from flask import Flask, render_template, request, jsonify, make_response
import os
import logging
from functools import lru_cache
import time
from dotenv import load_dotenv
import openai
from duckduckgo_search import DDGS

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 设置代理环境变量（如果需要）
if os.getenv('HTTPS_PROXY'):
    os.environ['OPENAI_PROXY'] = os.getenv('HTTPS_PROXY')

app = Flask(__name__)

def search_suburb_info(suburb_name):
    """搜索区域信息"""
    try:
        with DDGS() as ddgs:
            keywords = f"{suburb_name} melbourne suburb profile property market"
            results = list(ddgs.text(keywords, max_results=5))
            
        # 提取搜索结果的文本
        search_texts = []
        for result in results:
            search_texts.append(f"标题: {result['title']}\n摘要: {result['body']}\n来源: {result['link']}\n")
            
        return "\n".join(search_texts)
    except Exception as e:
        logger.error(f"搜索过程出错: {str(e)}")
        return f"搜索失败: {str(e)}"

@lru_cache(maxsize=100)
def generate_suburb_analysis(suburb_name, timestamp):
    """生成区域分析报告"""
    try:
        logger.info("开始生成分析报告...")
        
        # 搜索区域信息
        search_results = search_suburb_info(suburb_name)
        
        # 创建 OpenAI 客户端
        client = openai.OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url="https://api.openai.com/v1"
        )
        
        # 构建系统提示信息
        system_prompt = """你是一个专业的澳大利亚房地产分析师，擅长分析墨尔本房地产市场。
请根据提供的信息，生成一个详细的区域分析报告，包括以下方面：
1. 公共设施与政府基建（近10年）
2. 教育资源
3. 医疗资源
4. 房价趋势与推动因素
5. 总结与建议

使用中文回答，保持专业性和客观性。"""
        
        # 构建用户提示信息
        user_prompt = f"""请分析以下关于 {suburb_name} 的信息，生成一个详细的房地产市场分析报告：

搜索结果：
{search_results}

请从以下几个方面进行分析：
1. 公共设施与政府基建（2013-2023）：
   - 关键项目与拨款
   - 交通升级
   - 社区设施
   - 公园与环保
   - 未来规划

2. 教育资源：
   - 公立学校
   - 私立学校
   - 教会学校
   - 教育资源优劣势

3. 医疗资源：
   - 公立医院
   - 私立医疗机构
   - 医疗资源优劣势

4. 房价趋势与推动因素（2013-2023）：
   - 房价增长数据
   - 增长推动因素
   - 风险提示

5. 总结：
   - 优势和劣势对比
   - 购房建议
   - 参考信息来源

请用中文回答，并保持专业性。对于无法获取的具体数据，可以提供合理的估计或范围。"""
        
        # 调用 OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # 获取生成的报告
        report = response.choices[0].message.content
        
        return report
        
    except Exception as e:
        logger.error(f"分析过程中出现错误: {str(e)}")
        return f"生成报告时出错: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        if not request.is_json:
            return make_response(jsonify({'error': '请求必须是JSON格式'}), 400)

        data = request.get_json()
        suburb = data.get('suburb', '').lower().strip()
        
        if not suburb:
            return make_response(jsonify({'error': '请输入区域名称'}), 400)
            
        # 标准化输入
        if suburb == '3030':
            suburb = 'point cook'
        
        logger.info(f"搜索区域: {suburb}")
        
        # 使用缓存的分析结果
        timestamp = int(time.time() / (12 * 3600))  # 12小时更新一次
        analysis = generate_suburb_analysis(suburb, timestamp)
        
        return make_response(jsonify({'analysis': analysis}), 200)
            
    except Exception as e:
        logger.error(f"处理请求时出错: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/test_api', methods=['GET'])
def test_api():
    """测试OpenAI API连接"""
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, this is a test."}
            ],
            max_tokens=10
        )
        return make_response(jsonify({
            'status': 'success',
            'message': 'API连接正常',
            'response': response.choices[0].message.content
        }), 200)
    except Exception as e:
        logger.error(f"API测试失败: {str(e)}")
        return make_response(jsonify({
            'status': 'error',
            'message': f'API连接失败: {str(e)}'
        }), 500)

if __name__ == '__main__':
    logger.info("正在启动应用，端口: 8080")
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True) 