import apiClient from './apiClient';

// 单文档问答
export const singleDocumentQA = (documentId, question) => {
  return apiClient.post('/qa/single-document', null, {
    params: { document_id: documentId, question }
  });
};

// 知识库问答
export const knowledgeBaseQA = (question) => {
  return apiClient.post('/qa/knowledge-base', null, {
    params: { question }
  });
};

// 多文档对比
export const multiDocumentComparison = (documentIds) => {
  return apiClient.post('/qa/multi-document-comparison', null, {
    params: { document_ids: documentIds }
  });
};