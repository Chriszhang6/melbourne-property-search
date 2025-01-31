# 墨尔本房产信息搜索

这是一个基于Flask的Web应用，可以搜索墨尔本特定区域的房产相关信息，包括基础设施发展、安全统计和房价走势。

## 功能特点

- 支持区域名称和邮编搜索
- 实时获取最新信息
- 分类展示搜索结果
- 响应式设计，支持移动端
- API使用量跟踪
- 费用预警系统

## 技术栈

- 后端：Flask
- 前端：Bootstrap 5
- API：OpenAI GPT-3.5
- 部署：Heroku

## 安装说明

1. 克隆仓库：
```bash
git clone https://github.com/Chriszhang6/melbourne-property-search.git
cd melbourne-property-search
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 设置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，设置你的 OpenAI API 密钥
```

5. 运行应用：
```bash
python app.py
```

## 使用方法

1. 访问网站
2. 在搜索框中输入区域名称（如：Toorak）或邮编（如：3142）
3. 点击搜索按钮或按回车键
4. 查看分类展示的搜索结果

## API使用量

- 月度预算：$5.00
- 每次搜索成本：约$0.0046
- 每月可用次数：约1000次
- 费用预警系统（颜色提示）

## 部署说明

1. 创建Heroku应用：
```bash
heroku create your-app-name
```

2. 设置环境变量：
```bash
heroku config:set OPENAI_API_KEY=your-api-key-here
```

3. 推送代码：
```bash
git push heroku main
```

## 注意事项

- 搜索结果基于公开信息
- 建议配合其他数据源使用
- 定期检查API使用量
- 不要在代码中硬编码API密钥

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 许可证

MIT License 