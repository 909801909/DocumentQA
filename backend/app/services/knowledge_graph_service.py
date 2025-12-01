import networkx as nx
from sqlalchemy.orm import Session
import re
from typing import List, Dict, Optional
import jieba.posseg as pseg
from collections import defaultdict
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import os
from matplotlib import font_manager

from app.models.document import Document

# 改进的字体查找和注册逻辑
def get_chinese_font():
    font_paths = font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
    font_names = ['SimHei', 'Microsoft YaHei', 'DengXian', 'msyh']
    
    for font_path in font_paths:
        try:
            font_prop = font_manager.FontProperties(fname=font_path)
            if any(name in font_prop.get_name() for name in font_names):
                print(f"Found suitable font: {font_prop.get_name()} at {font_path}")
                return font_prop
        except Exception:
            continue
            
    print("Warning: No suitable system Chinese font found for Matplotlib. Image generation may have garbled text.")
    return None

CHINESE_FONT_PROP = get_chinese_font()

class KnowledgeGraphService:
    def __init__(self, db: Session):
        self.db = db
        self.graph = nx.DiGraph()
        self.stop_words = self._load_stop_words()

    def _load_stop_words(self):
        return {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}

    def build_knowledge_graph(self, document_id: Optional[int] = None) -> Dict:
        self.graph.clear()
        if document_id:
            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}
            self._extract_entities_and_relations(document)
        else:
            documents = self.db.query(Document).all()
            for doc in documents:
                self._extract_entities_and_relations(doc)

        if not self.graph.nodes:
            return {"nodes": [], "edges": [], "node_count": 0, "edge_count": 0}

        node_counts = nx.get_node_attributes(self.graph, 'count')
        isolates = list(nx.isolates(self.graph))
        for node in isolates:
            if node_counts.get(node, 1) < 2:
                self.graph.remove_node(node)

        centrality = nx.degree_centrality(self.graph)
        nodes = [{"id": node, "label": node, "size": (centrality.get(node, 0) * 50) + (data.get("count", 1) * 2)} for node, data in self.graph.nodes(data=True)]
        edges = [{"source": source, "target": target, "label": data.get('relation', '相关')} for source, target, data in self.graph.edges(data=True)]

        return {"nodes": nodes, "edges": edges, "node_count": len(nodes), "edge_count": len(edges)}

    def _extract_entities_and_relations(self, document: Document):
        content = re.sub(r'\s+', ' ', document.content)
        sentences = re.split(r'[.!?。！？\n]', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 5: continue
            words = list(pseg.cut(sentence))
            entities = self._extract_entities(words)
            for entity in entities:
                if self.graph.has_node(entity): self.graph.nodes[entity]['count'] += 1
                else: self.graph.add_node(entity, count=1)
            self._extract_verb_relations(words)

    def _extract_entities(self, words) -> List[str]:
        allowed_pos = {'n', 'nr', 'ns', 'nt', 'nz', 'eng'}
        return list(dict.fromkeys([word for word, flag in words if flag in allowed_pos and len(word) > 1 and word not in self.stop_words]))

    def _extract_verb_relations(self, words):
        for i in range(len(words) - 2):
            w1, f1 = words[i]; w2, f2 = words[i+1]; w3, f3 = words[i+2]
            if self._is_entity(w1, f1) and self._is_verb(w2, f2) and self._is_entity(w3, f3): self._add_relation(w1, w3, w2)
            if self._is_entity(w1, f1) and w2 == '的' and self._is_entity(w3, f3): self._add_relation(w1, w3, '拥有')

    def _is_entity(self, word, flag):
        return flag in {'n', 'nr', 'ns', 'nt', 'nz', 'eng'} and len(word) > 1 and word not in self.stop_words

    def _is_verb(self, word, flag):
        return flag.startswith('v') and len(word) > 0

    def _add_relation(self, e1, e2, verb):
        if self.graph.has_edge(e1, e2): self.graph[e1][e2]['weight'] += 1
        else: self.graph.add_edge(e1, e2, relation=verb, weight=1)

    def generate_graph_image_base64(self) -> Optional[str]:
        if not self.graph.nodes:
            return None
        
        plt.figure(figsize=(16, 12), dpi=150)
        pos = nx.spring_layout(self.graph, k=0.8, iterations=50)
        
        centrality = nx.degree_centrality(self.graph)
        node_sizes = [(centrality.get(node, 0) * 2000) + 500 for node in self.graph.nodes()]

        # 修正：为 networkx 函数准备 font_family 参数
        font_family = CHINESE_FONT_PROP.get_name() if CHINESE_FONT_PROP else 'sans-serif'
        
        nx.draw_networkx_nodes(self.graph, pos, node_size=node_sizes, node_color='#5470C6', alpha=0.8)
        nx.draw_networkx_labels(self.graph, pos, font_size=10, font_color='white', font_family=font_family)
        
        nx.draw_networkx_edges(self.graph, pos, edge_color='gray', alpha=0.6, arrows=True)
        edge_labels = nx.get_edge_attributes(self.graph, 'relation')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_size=8, font_family=font_family)
        
        # 为 plt.title 准备 fontproperties 参数
        title_font_kwargs = {'fontproperties': CHINESE_FONT_PROP} if CHINESE_FONT_PROP else {}
        plt.title("文档知识图谱", fontsize=20, **title_font_kwargs)
        plt.axis('off')
        
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()
        
        return image_base64
