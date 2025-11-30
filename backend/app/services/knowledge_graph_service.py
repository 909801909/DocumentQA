import networkx as nx
from sqlalchemy.orm import Session
import re
from typing import List, Dict, Optional
import jieba.posseg as pseg
from collections import defaultdict

from app.models.document import Document

class KnowledgeGraphService:
    """
    知识图谱构建服务
    使用动词短语作为关系，并移除孤立节点，以构建更清晰的知识图谱。
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.graph = nx.DiGraph()  # 使用有向图以更好地表示主谓宾关系
        self.stop_words = self._load_stop_words()

    def _load_stop_words(self):
        return {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}

    def build_knowledge_graph(self, document_id: Optional[int] = None) -> Dict:
        """
        构建知识图谱。
        如果提供了 document_id，则只为该文档构建图谱。
        """
        self.graph.clear()

        if document_id:
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}
            self._extract_entities_and_relations(document)
        else:
            # 支持对所有文档进行分析
            documents = self.db.query(Document).all()
            for doc in documents:
                self._extract_entities_and_relations(doc)

        if not self.graph.nodes:
            return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

        # 移除孤立节点，除非它是高频词
        node_counts = nx.get_node_attributes(self.graph, 'count')
        isolates = list(nx.isolates(self.graph))
        for node in isolates:
            # 保留出现次数超过阈值（例如2次）的孤立节点，它们可能是重要的独立概念
            if node_counts.get(node, 1) < 2:
                self.graph.remove_node(node)

        # 计算度中心性来决定节点大小
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
            relation = data.get('relation', '相关')
            edges.append({
                "source": source,
                "target": target,
                "label": relation
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }

    def _extract_entities_and_relations(self, document: Document):
        content = re.sub(r'\s+', ' ', document.content)
        sentences = re.split(r'[.!?。！？\n]', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5:
                continue
            
            # 使用jieba进行词性标注
            words = list(pseg.cut(sentence))
            
            # 提取实体并添加节点
            entities = self._extract_entities(words)
            for entity in entities:
                if self.graph.has_node(entity):
                    self.graph.nodes[entity]['count'] += 1
                else:
                    self.graph.add_node(entity, count=1)

            # 提取关系 (主-谓-宾)
            self._extract_verb_relations(words)

    def _extract_entities(self, words) -> List[str]:
        """从标注好的词语列表中提取实体"""
        allowed_pos = {'n', 'nr', 'ns', 'nt', 'nz', 'eng'}
        entities = [word for word, flag in words if flag in allowed_pos and len(word) > 1 and word not in self.stop_words]
        return list(dict.fromkeys(entities))

    def _extract_verb_relations(self, words):
        """
        提取句子中的 "实体-动词-实体" 关系
        这是一个简化的实现，寻找相邻的 名词-动词-名词 结构
        """
        for i in range(len(words) - 2):
            w1, f1 = words[i]
            w2, f2 = words[i+1]
            w3, f3 = words[i+2]

            # 规则1: 名词 + 动词 + 名词
            if self._is_entity(w1, f1) and self._is_verb(w2, f2) and self._is_entity(w3, f3):
                self._add_relation(w1, w3, w2)

            # 规则2: 名词 + "的" + 名词 (表示所属关系)
            if self._is_entity(w1, f1) and w2 == '的' and self._is_entity(w3, f3):
                self._add_relation(w1, w3, '拥有')

    def _is_entity(self, word, flag):
        allowed_pos = {'n', 'nr', 'ns', 'nt', 'nz', 'eng'}
        return flag in allowed_pos and len(word) > 1 and word not in self.stop_words

    def _is_verb(self, word, flag):
        return flag.startswith('v') and len(word) > 0

    def _add_relation(self, entity1, entity2, verb):
        """添加或更新图中的关系"""
        if self.graph.has_edge(entity1, entity2):
            # 如果关系已存在，可以增加权重或更新标签
            self.graph[entity1][entity2]['weight'] += 1
        else:
            # 否则，创建新关系
            self.graph.add_edge(entity1, entity2, relation=verb, weight=1)
