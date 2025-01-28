import os
import requests
from tqdm import tqdm

def download_file(url, filename):
    """下载文件并显示进度条"""
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
    # GPT4All-J量化模型下载地址
    model_url = "https://gpt4all.io/models/ggml-gpt4all-j-v1.3-groovy.bin"
    model_path = "models/ggml-gpt4all-j-v1.3-groovy.bin"
    
    print("开始下载GPT4All-J模型...")
    download_file(model_url, model_path)
    print("模型下载完成！")

if __name__ == "__main__":
    main() 