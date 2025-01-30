import os
import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_openai_api():
    """测试 OpenAI API 连接"""
    try:
        # 验证环境变量
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("未设置 OPENAI_API_KEY 环境变量")
            
        print(f"API Key 格式验证: {api_key[:12]}...")
        print(f"API Key 长度: {len(api_key)}")
        
        # 创建 OpenAI 客户端
        client = openai.OpenAI()
        
        print("客户端创建成功")
        
        # 测试简单请求
        print("开始发送测试请求...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, this is a test."}
            ],
            max_tokens=10
        )
        
        print("API 调用成功!")
        print("响应:", response.choices[0].message.content)
        return True
        
    except Exception as e:
        print(f"错误: {str(e)}")
        print("错误类型:", type(e))
        import traceback
        print("错误堆栈:", traceback.format_exc())
        return False

if __name__ == "__main__":
    test_openai_api() 