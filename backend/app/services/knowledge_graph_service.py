import networkx as nx
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from sqlalchemy.orm import Session
import re
from typing import List, Dict

from app.models.document import Document


class KnowledgeGraphService:
    """
    知识图谱构建服务
    从文档中提取实体和关系，构建知识图谱
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.graph = nx.Graph()
    
    def build_knowledge_graph(self) -> Dict:
        """
        构建知识图谱
        
        Returns:
            包含节点、边和图可视化信息的字典
        """
        # 获取所有文档
        documents = self.db.query(Document).all()
        
        # 从所有文档中提取实体和关系
        for doc in documents:
            self._extract_entities_and_relations(doc)
        
        # 准备返回数据
        nodes = []
        edges = []
        
        # 获取节点和边的信息
        for node in self.graph.nodes(data=True):
            nodes.append({
                "id": node[0],
                "label": node[0],
                "size": node[1].get("count", 1) * 10
            })
        
        for edge in self.graph.edges(data=True):
            edges.append({
                "source": edge[0],
                "target": edge[1],
                "label": edge[2].get("relation", "")
            })
        
        # 生成图的可视化
        graph_image = self._generate_graph_image()
        
        return {
            "nodes": nodes,
            "edges": edges,
            "graph_image": graph_image,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }
    
    def _extract_entities_and_relations(self, document: Document):
        """
        从文档中提取实体和关系
        
        Args:
            document: 文档对象
        """
        # 这里是简化的实体和关系提取逻辑
        # 在实际应用中，可以使用NER（命名实体识别）等技术
        
        # 提取可能的实体（名词短语）
        entities = self._extract_entities(document.content)
        
        # 添加实体到图中
        for entity in entities:
            if self.graph.has_node(entity):
                # 如果节点已存在，增加计数
                self.graph.nodes[entity]['count'] = self.graph.nodes[entity].get('count', 1) + 1
            else:
                # 添加新节点
                self.graph.add_node(entity, count=1)
        
        # 提取可能的关系（简化方法：在同一句子中的实体可能存在关系）
        sentences = re.split(r'[.!?。！？]', document.content)
        for sentence in sentences:
            sentence_entities = [e for e in entities if e in sentence]
            # 在同一句子中的实体之间添加边
            for i in range(len(sentence_entities)):
                for j in range(i+1, len(sentence_entities)):
                    entity1 = sentence_entities[i]
                    entity2 = sentence_entities[j]
                    if self.graph.has_edge(entity1, entity2):
                        # 如果边已存在，增加权重
                        self.graph[entity1][entity2]['weight'] = self.graph[entity1][entity2].get('weight', 1) + 1
                    else:
                        # 添加新边
                        self.graph.add_edge(entity1, entity2, weight=1)
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        从文本中提取实体（简化版）
        
        Args:
            text: 输入文本
            
        Returns:
            实体列表
        """
        # 移除标点符号并分割单词
        words = re.findall(r'\b\w+\b', text.lower())
        
        # 过滤掉常见停用词，保留可能的实体词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        
        # 简化处理：将连续的词语组合作为潜在实体
        entities = []
        for i in range(len(words)):
            # 单个词
            if len(words[i]) > 1 and words[i] not in stop_words:
                entities.append(words[i].capitalize())
            
            # 双词组合
            if i < len(words) - 1:
                two_word = f"{words[i]} {words[i+1]}"
                if len(two_word.replace(' ', '')) > 2 and not any(sw in two_word for sw in stop_words):
                    entities.append(two_word.capitalize())
        
        # 去重并限制数量
        return list(set(entities))[:50]  # 最多返回50个实体
    
    def _generate_graph_image(self) -> str:
        """
        生成知识图谱的图像表示
        
        Returns:
            base64编码的图像字符串
        """
        if len(self.graph.nodes()) == 0:
            return ""
        
        # 创建图形
        plt.figure(figsize=(12, 8))
        
        # 计算节点布局
        pos = nx.spring_layout(self.graph, k=1, iterations=50)
        
        # 获取节点大小
        node_sizes = [self.graph.nodes[node].get('count', 1) * 300 for node in self.graph.nodes()]
        
        # 绘制节点和边
        nx.draw_networkx_nodes(self.graph, pos, node_size=node_sizes, node_color='lightblue', alpha=0.7)
        nx.draw_networkx_edges(self.graph, pos, edge_color='gray', alpha=0.5)
        nx.draw_networkx_labels(self.graph, pos, font_size=8)
        
        # 添加边标签
        edge_labels = nx.get_edge_attributes(self.graph, 'relation')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=6)
        
        plt.title("知识图谱")
        plt.axis('off')
        
        # 将图像转换为base64字符串
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()
        
        return image_base64