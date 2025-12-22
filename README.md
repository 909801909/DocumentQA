# 智能文档问答系统

## 项目简介

智能文档问答系统是一个基于大语言模型（LLM）的综合性AI应用，能够处理文档的深度问答、关系挖掘和报告自动化。系统旨在将非结构化的文档内容转化为结构化的知识和洞察。

## 功能特性

1.  **智能问答**
    *   **单文档问答**：用户可上传文档，并针对单一文档内容进行深入提问，系统基于文档上下文给出精准答案。
    *   **知识库问答**：支持在整个文档库范围内进行跨文档的综合提问，系统整合所有相关信息后给出全面回答。
    *   **多文档对比**：支持选择两篇或多篇文档，智能分析它们在核心观点、数据细节和叙述结构上的异同。

2.  **知识图谱构建**
    *   **单文档图谱生成**：用户可选择任一文档，系统将自动提取文档中的核心实体（名词、地名、机构名等）。
    *   **关系挖掘**：通过分析实体间的动词和上下文，智能构建实体间的关系网络（如“拥有”、“影响”、“发布”等）。
    *   **可视化展示**：将提取的实体和关系渲染成清晰、直观的可视化知识图谱，核心概念会通过节点大小突出显示。

3.  **报告自动生成**
    *   **动态内容摘要**：利用大语言模型，为用户选择的一篇或多篇文档自动生成一段高质量、连贯的核心内容摘要。
    *   **图文并茂**：报告中会自动插入根据文档内容生成的知识图谱图片，提供直观的分析视角。
    *   **多格式导出**：支持将整合了摘要和图谱的分析报告导出为 **Word (.docx)** 和 **PDF** 两种常用格式。

## 技术栈

### 后端
-   **框架**: FastAPI
-   **数据库**: SQLite
-   **AI / NLP**:
    -   LangChain (LLM应用框架)
    -   Transformers, Sentence-Transformers (模型加载与嵌入)
    -   FAISS (高效向量检索)
    -   Jieba (中文分词与词性标注)
    -   DashScope (阿里云通义千问)
    -   LangChain-OpenAI (兼容OpenAI及各类开源模型接口)
-   **数据处理与可视化**:
    -   NetworkX (图论与复杂网络)
    -   Matplotlib (知识图谱图像生成)
-   **报告生成**:
    -   `python-docx` (Word文档创建)
    -   `reportlab` (PDF文档创建)

### 前端
-   **框架**: React 18+
-   **构建工具**: Vite
-   **UI组件库**: Ant Design 5.x
-   **可视化**: ECharts for React
-   **API请求**: Axios
-   **Markdown渲染**: React-Markdown

## 项目结构

```
project/
├── backend/
│   ├── app/
│   │   ├── api/             # API 路由 (qa.py, reports.py, etc.)
│   │   ├── core/            # 核心配置 (config.py, database.py)
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   ├── schemas/         # Pydantic 数据模型
│   │   └── services/        # 业务逻辑 (qa_service.py, report_service.py, etc.)
│   ├── app.db               # SQLite 数据库文件
│   ├── main.py              # 应用入口
│   └── requirements.txt     # Python 依赖
└── frontend/
    ├── src/
    │   ├── api/             # API 调用封装
    │   ├── assets/          # 静态资源
    │   └── components/      # React 组件
    ├── index.html           # 入口 HTML
    └── package.json         # Node.js 依赖
```

## 安装和运行

**先决条件:**
*   已安装 [Conda](https://docs.conda.io/en/latest/miniconda.html) 并创建了名为 `DocumentQA` 的虚拟环境。
*   已安装 [Node.js](https://nodejs.org/) (v18+)。

### 后端启动

```powershell
# 1. 进入后端目录
cd backend

# 2. 激活 Conda 虚拟环境
conda activate DocumentQA

# 3. 启动 FastAPI 服务
uvicorn app.main:app --reload
```

### 前端启动

```powershell
# 1. 进入前端目录
cd frontend

# 2. 激活 Conda 虚拟环境 (确保环境中的 Node.js 可用)
conda activate DocumentQA

# (可选) 如果 npm 命令不识别，尝试重新加载系统环境变量
# $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 4. 启动开发服务器
npm run dev

# 3. 安装依赖 (首次运行时需要)
npm install
```



## 大语言模型（LLM）集成

本系统通过 `langchain` 框架灵活支持多种大语言模型，并拥有自动回退机制。

### 模型优先级与配置

系统会按照以下顺序检查并使用配置好的大语言模型：

1.  **OpenAI 兼容模型 (推荐)**
    *   **适用范围**: 支持 OpenAI 官方 API，以及任何提供 OpenAI 兼容接口的本地模型或云服务（如 DeepSeek, LocalAI, Moonshot 等）。
    *   **配置**: 在项目根目录创建 `.env` 文件，并添加以下变量：
        ```env
        # 必填: 你的 API Key
        OPENAI_API_KEY="your_api_key_here"

        # 必填: 使用的模型名称
        OPENAI_MODEL_NAME="deepseek-chat"

        # 可选: 如果使用非官方接口，请提供 Base URL
        OPENAI_API_BASE="https://api.deepseek.com/v1"
        ```

2.  **通义千问 (Qwen)**
    *   **适用范围**: 阿里云通义千问系列模型。
    *   **配置**: 如果未配置 OpenAI，系统会检查 `.env` 文件中的通义千问配置：
        ```env
        # 你的阿里云 DashScope API Key
        QWEN_API_KEY="your_dashscope_api_key_here"
        ```

### 回退机制
如果上述大语言模型均未配置或调用失败，系统将自动回退到基于 `jieba` 分词和关键词匹配的简单问答模式，以保证基础功能的可用性。
