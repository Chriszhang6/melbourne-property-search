import os
import requests
from tqdm import tqdm

def download_file(url, filename):
    """
    从给定URL下载文件并显示进度条
    """
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'wb') as f, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            pbar.update(size)

def main():
    """
    主函数：下载模型文件
    """
    model_url = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    model_path = "models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
    
    if os.path.exists(model_path):
        print(f"模型文件已存在于 {model_path}")
        return
    
    print("开始下载TinyLlama模型...")
    download_file(model_url, model_path)
    print("模型下载完成！")

if __name__ == "__main__":
    main() 