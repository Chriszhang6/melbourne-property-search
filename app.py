from flask import Flask, render_template, request, jsonify
from search_engine import PropertySearchEngine
import os
from ctransformers import AutoModelForCausalLM
from functools import lru_cache
import time
from dotenv import load_dotenv
import tempfile
import logging
import sys
import gc

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

app = Flask(__name__)
search_engine = PropertySearchEngine()

# 在临时目录中创建模型路径
TEMP_DIR = tempfile.gettempdir()
MODEL_FILENAME = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
MODEL_PATH = os.path.join(TEMP_DIR, MODEL_FILENAME)

# 全局模型实例
_model = None

def download_model():
    """下载模型到临时目录"""
    if os.path.exists(MODEL_PATH):
        logger.info(f"模型文件已存在: {MODEL_PATH}")
        return True
        
    try:
        import requests
        from tqdm import tqdm
        
        model_url = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
        
        logger.info(f"开始下载模型到临时目录: {MODEL_PATH}")
        response = requests.get(model_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(MODEL_PATH, 'wb') as f, tqdm(
            desc=MODEL_PATH,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                pbar.update(size)
        
        logger.info("模型下载完成！")
        return True
    except Exception as e:
        logger.error(f"模型下载失败: {str(e)}")
        return False

def get_model():
    """获取模型实例（单例模式）"""
    global _model
    try:
        if _model is not None:
            return _model
            
        if not os.path.exists(MODEL_PATH):
            if not download_model():
                logger.error("无法下载模型文件")
                return None
                
        logger.info("正在加载模型...")
        # 强制垃圾回收
        gc.collect()
        
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            model_type="llama",
            max_new_tokens=256,  # 进一步减少token数量
            context_length=512,  # 进一步减少上下文长度
            temperature=0.7,
            gpu_layers=0,  # 禁用GPU
            batch_size=1,  # 最小批处理大小
            threads=1,  # 减少线程数
            low_cpu_mem_usage=True  # 启用低内存模式
        )
        logger.info("模型加载成功！")
        return _model
    except Exception as e:
        logger.error(f"模型加载失败: {str(e)}")
        _model = None
        return None

def analyze_with_tinyllama(search_results):
    """使用TinyLlama分析搜索结果"""
    try:
        model = get_model()
        if model is None:
            return "模型加载失败，请稍后重试"
        
        # 限制输入长度
        max_input_length = 500
        truncated_results = str(search_results)[:max_input_length] + "..."
        
        system_prompt = """你是一个专业的墨尔本房地产分析师。请简要分析以下房产信息：
1. 价格趋势
2. 区域特点
3. 投资建议
4. 风险提示"""

        prompt = f"""<|system|>{system_prompt}</s>
<|user|>分析结果：{truncated_results}</s>
<|assistant|>"""

        logger.info("开始生成分析报告...")
        response = model(prompt)
        logger.info("分析报告生成完成")
        
        # 强制垃圾回收
        gc.collect()
        
        return response
    except Exception as e:
        logger.error(f"分析过程中出现错误: {str(e)}")
        return f"分析过程中出现错误: {str(e)}"

# 使用缓存装饰器，缓存12小时
@lru_cache(maxsize=1000)
def cached_analysis(suburb, timestamp):
    """缓存分析结果，每12小时更新一次"""
    return analyze_with_tinyllama(suburb)

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