from flask import Flask, render_template, request, jsonify
from search_engine import PropertySearchEngine
import os
import requests
from functools import lru_cache
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
search_engine = PropertySearchEngine()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def analyze_with_deepseek(search_results):
    """使用DeepSeek分析搜索结果"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """你是一个专业的墨尔本房地产分析师，擅长分析房产市场趋势和提供投资建议。
请用专业且客观的中文回答，注重数据分析和市场洞察。
在分析时，请特别关注：
1. 价格趋势和市场周期
2. 区域发展潜力
3. 投资回报率
4. 风险因素评估"""

    prompt = f"""请分析以下墨尔本房产信息，并提供一个详细的市场分析报告：

搜索结果：{search_results}

请包含以下方面：
1. 房产价格趋势：
   - 近期价格变动
   - 未来走势预测
   - 与周边区域对比

2. 区域特点分析：
   - 交通便利性
   - 教育资源
   - 生活配套
   - 发展规划

3. 投资建议：
   - 投资时机
   - 预期回报
   - 租金收益分析
   - 最佳投资策略

4. 风险提示：
   - 市场风险
   - 政策风险
   - 特殊注意事项
   - 防范建议"""

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 1500
            }
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"API请求失败: {response.status_code} - {response.text}"
    except Exception as e:
        return f"分析过程中出现错误: {str(e)}"

# 使用缓存装饰器，缓存12小时
@lru_cache(maxsize=1000)
def cached_analysis(suburb, timestamp):
    """缓存分析结果，每12小时更新一次"""
    return analyze_with_deepseek(suburb)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    suburb = data.get('suburb', '')
    
    if not suburb:
        return jsonify({'error': '请输入区域名称或邮编'}), 400
    
    # 标准化输入
    suburb = suburb.lower().strip()
    if suburb == '3030':
        suburb = 'point cook'
    
    try:
        # 获取搜索结果
        results = search_engine.search_suburb(suburb)
        
        # 使用缓存的分析结果
        timestamp = int(time.time() / (12 * 3600))  # 12小时更新一次
        analysis = cached_analysis(str(results), timestamp)
        
        return jsonify({
            'raw_results': results,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 