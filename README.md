# 智能文档问答系统

## 项目简介

智能文档问答系统是一个能够处理文档问答、知识图谱构建、多文档比较和报告自动生成的综合性AI应用。

## 功能特性

1. 智能问答
   - 单文档问答：用户可就单一文档内容进行提问，系统基于文档内容给出精准答案
   - 知识库问答：用户可针对整个文档库进行跨文档的综合提问，系统整合所有相关信息后给出答案
   - 多文档对比：支持选择两篇或多篇文档，智能分析其在内容、观点、数据等方面的异同

2. 知识图谱构建
   - 自动从文档库中抽取实体并构建其关系网络，形成可视化的知识图谱

3. 报告自动生成
   - 根据模板或自定义需求，自动整合分析结果，生成结构化分析报告（支持Word/PDF格式）

4. 使用统计
   - 记录用户使用量、功能调用次数等数据，用于计费和系统优化

## 技术栈

### 后端
- Python 3.8+
- FastAPI - 现代、快速(高性能)的web框架
- SQLite - 轻量级数据库
- LangChain - 构建与大语言模型应用程序的框架
- Transformers - Hugging Face提供的自然语言处理工具包
- NetworkX - 创建和操作复杂网络结构的Python包

### 前端
- React 18+ - JavaScript库，用于构建用户界面
- Vite - 新一代前端构建工具
- Ant Design - React UI组件库
- ECharts - 开源可视化图表库

## 项目结构

```
├── backend/                 # 后端代码
│   ├── app/                 # 主应用目录
│   │   ├── api/             # API路由
│   │   ├── core/            # 核心配置
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic模型
│   │   ├── services/        # 业务逻辑层
│   │   ├── utils/           # 工具函数
│   │   └── main.py          # 应用入口
│   ├── tests/               # 测试文件
│   └── requirements.txt     # Python依赖
├── frontend/                # 前端代码
│   ├── public/              # 公共静态资源
│   └── src/                 # 主要源代码
└── README.md                # 项目说明文档
```

## 安装和运行

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 大语言模型集成

本系统支持集成大语言模型以提供更智能的问答服务。目前支持以下选项：

### OpenAI (GPT系列)
1. 在环境变量中设置 `OPENAI_API_KEY`：
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```
   
2. 或者在项目根目录创建 `.env` 文件并添加：
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. 重启后端服务，系统将自动使用OpenAI模型进行问答。

### 通义千问 (Qwen)
1. 在环境变量中设置 `QWEN_API_KEY`：
   ```bash
   export QWEN_API_KEY=your_api_key_here
   ```
   
2. 或者在项目根目录创建 `.env` 文件并添加：
   ```
   QWEN_API_KEY=your_api_key_here
   ```

3. 重启后端服务，系统将自动使用通义千问模型进行问答。

### 本地开源模型
系统默认使用HuggingFace的开源模型进行嵌入和问答。如果需要使用特定的本地模型，可以在 `qa_service.py` 中修改相关配置。

### 回退机制
如果大语言模型不可用或配置不正确，系统会自动回退到基于关键词匹配的简单问答模式。

## 免费大语言模型API

以下是一些提供免费额度或免费服务的大语言模型API平台：

### 国际平台
1. **OpenAI**
   - 新用户注册可获得$5的免费额度，有效期3个月
   - 访问地址：https://platform.openai.com/

2. **Hugging Face**
   - 提供免费的API访问，但有限制
   - 访问地址：https://huggingface.co/

3. **Google AI (Gemini)**
   - 提供免费额度：新用户可获得一定量的免费调用次数
   - 访问地址：https://ai.google.dev/

### 国内平台
1. **百度千帆大模型平台**
   - 提供免费额度
   - 支持ERNIE Bot等大模型
   - 访问地址：https://cloud.baidu.com/product/wenxinworkshop.html

2. **阿里云通义实验室**
   - 提供免费额度
   - 支持通义千问等大模型
   - 访问地址：https://dashscope.aliyun.com/

3. **腾讯云AI**
   - 提供免费额度
   - 支持混元等大模型
   - 访问地址：https://cloud.tencent.com/product/hunyuan

4. **零一万物**
   - 提供免费API额度
   - 访问地址：https://www.lingyiwanwu.com/

5. **智谱AI**
   - 提供免费额度
   - 支持ChatGLM等大模型
   - 访问地址：https://open.bigmodel.cn/