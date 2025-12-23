import networkx as nx
from sqlalchemy.orm import Session
import re
from typing import List, Dict, Optional, Any
import json
import logging
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from matplotlib import font_manager

# LangChain imports
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.models.document import Document
from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 条件导入不同平台的模块
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_community.llms import Tongyi
    QWEN_AVAILABLE = True
except ImportError:
    QWEN_AVAILABLE = False

# 改进的字体查找和注册逻辑
def get_chinese_font():
    font_paths = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    font_names = ['SimHei', 'Microsoft YaHei', 'DengXian', 'msyh']
    
    for font_path in font_paths:
        try:
            font_prop = font_manager.FontProperties(fname=font_path)
            if any(name in font_prop.get_name() for name in font_names):
                return font_prop
        except Exception:
            continue
    return None

CHINESE_FONT_PROP = get_chinese_font()

class KnowledgeGraphService:
    def __init__(self, db: Session):
        self.db = db
        self.graph = nx.DiGraph()

    def build_knowledge_graph(self, document_id: Optional[int] = None) -> Dict:
        self.graph.clear()
        
        documents = []
        if document_id:
            doc = self.db.query(Document).filter(Document.id == document_id).first()
            if doc:
                documents.append(doc)
        else:
            documents = self.db.query(Document).all()
            
        if not documents:
            return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

        # 使用 LLM 提取图谱数据
        for doc in documents:
            self._extract_graph_from_llm(doc)

        if not self.graph.nodes:
            return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

        # 移除孤立节点
        node_counts = nx.get_node_attributes(self.graph, 'count')
        isolates = list(nx.isolates(self.graph))
        for node in isolates:
            if node_counts.get(node, 1) < 2:
                self.graph.remove_node(node)

        # 计算中心性并生成返回数据
        centrality = nx.degree_centrality(self.graph)
        nodes = []
        for node, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node,
                "label": node,
                "size": (centrality.get(node, 0) * 50) + (data.get("count", 1) * 2)
            })
            
        edges = []
        for source, target, data in self.graph.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "label": data.get('relation', '相关')
            })

        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}

    def _extract_graph_from_llm(self, document: Document):
        text = document.content
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = text_splitter.split_text(text)
        
        max_chunks = 6
        chunks = chunks[:max_chunks]

        # --- 优化后的并行处理 ---
        # 降级并发数到 2，以保证稳定性
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for chunk in chunks:
                # 提交任务
                future = executor.submit(self._llm_call, chunk)
                futures.append(future)
                # 关键修改：错峰提交，避免瞬间拥堵
                time.sleep(0.5)
            
            # 获取结果
            for future in as_completed(futures):
                try:
                    result_json = future.result()
                    self._parse_and_add_to_graph(result_json)
                except Exception as e:
                    logger.error(f"Error extracting graph from chunk: {e}")
                    continue

    def _llm_call(self, text: str) -> Dict:
        prompt_template = """
        你是一位友好的数据分析师。请帮我从下面的文本中识别出关键的实体和它们之间的关系，并以JSON格式返回。

        JSON的结构应该包含两个键：
        - "entities": 一个包含所有实体名称的字符串列表。
        - "relations": 一个对象列表，每个对象包含 "source", "target", 和 "relation" 三个键。

        请确保你的回答只包含纯粹的JSON内容，不要有任何额外的解释或Markdown标记。

        这是文本：
        {text}
        """
        
        prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
        
        llm: Optional[Runnable] = None
        if OPENAI_AVAILABLE and settings.OPENAI_API_KEY:
            llm_kwargs = {
                "openai_api_key": settings.OPENAI_API_KEY,
                "model_name": settings.OPENAI_MODEL_NAME,
                "temperature": 0,
                "request_timeout": 60
            }
            if settings.OPENAI_API_BASE:
                llm_kwargs["openai_api_base"] = settings.OPENAI_API_BASE
            llm = ChatOpenAI(**llm_kwargs)
            
        elif QWEN_AVAILABLE and settings.QWEN_API_KEY:
            llm = Tongyi(
                model_name="qwen-turbo",
                dashscope_api_key=settings.QWEN_API_KEY,
                temperature=0,
                request_timeout=60
            )
            
        if not llm:
            logger.warning("No LLM available for knowledge graph extraction.")
            return {"entities": [], "relations": []}

        chain = prompt | llm | StrOutputParser()
        result_str = chain.invoke({"text": text})
        
        json_str = result_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
            
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from LLM response: {json_str}")
            return {"entities": [], "relations": []}

    def _parse_and_add_to_graph(self, data: Dict):
        entities = data.get("entities", [])
        relations = data.get("relations", [])
        
        for entity in entities:
            if not isinstance(entity, str): continue
            if self.graph.has_node(entity):
                self.graph.nodes[entity]['count'] += 1
            else:
                self.graph.add_node(entity, count=1)
                
        for rel in relations:
            source = rel.get("source")
            target = rel.get("target")
            relation = rel.get("relation")
            
            if source and target and relation:
                if not self.graph.has_node(source): self.graph.add_node(source, count=1)
                if not self.graph.has_node(target): self.graph.add_node(target, count=1)
                    
                if self.graph.has_edge(source, target):
                    self.graph[source][target]['weight'] += 1
                else:
                    self.graph.add_edge(source, target, relation=relation, weight=1)

    def generate_graph_image_base64(self) -> Optional[str]:
        if not self.graph.nodes:
            return None
        
        plt.figure(figsize=(16, 12), dpi=150)
        pos = nx.spring_layout(self.graph, k=0.8, iterations=50)
        
        centrality = nx.degree_centrality(self.graph)
        node_sizes = [(centrality.get(node, 0) * 2000) + 500 for node in self.graph.nodes()]

        font_family = CHINESE_FONT_PROP.get_name() if CHINESE_FONT_PROP else 'sans-serif'
        
        nx.draw_networkx_nodes(self.graph, pos, node_size=node_sizes, node_color='#5470C6', alpha=0.8)
        nx.draw_networkx_labels(self.graph, pos, font_size=10, font_color='white', font_family=font_family)
        
        nx.draw_networkx_edges(self.graph, pos, edge_color='gray', alpha=0.6, arrows=True)
        edge_labels = nx.get_edge_attributes(self.graph, 'relation')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=8, font_family=font_family)
        
        title_font_kwargs = {'fontproperties': CHINESE_FONT_PROP} if CHINESE_FONT_PROP else {}
        plt.title("文档知识图谱 (AI生成)", fontsize=20, **title_font_kwargs)
        plt.axis('off')
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()
        
        return image_base64
