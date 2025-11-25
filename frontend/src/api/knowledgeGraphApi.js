import apiClient from './apiClient';

// 构建知识图谱
export const buildKnowledgeGraph = () => {
  return apiClient.post('/knowledge-graph/build');
};

// 获取知识图谱可视化
export const getKnowledgeGraphVisualization = () => {
  return apiClient.get('/knowledge-graph/visualize');
};