import apiClient from './apiClient';

// 单文档问答 - 增加 history 参数
export const singleDocumentQA = (documentId, question, history = []) => {
  return apiClient.post('/qa/single-document', { // 改为 POST body 传参更合适，但为了兼容保持 query param 也可以，这里推荐用 body
    history: history
  }, {
    params: { document_id: documentId, question }
  });
};

// 知识库问答 - 增加 history 参数
export const knowledgeBaseQA = (question, history = []) => {
  return apiClient.post('/qa/knowledge-base', {
    history: history
  }, {
    params: { question }
  });
};

// 多文档对比 - 增加 question 参数（可选）
export const multiDocumentComparison = (documentIds, question = "") => {
  return apiClient.post('/qa/multi-document-comparison', { // 这里的 document_ids 以前在 params，如果数据量大建议放 body
    document_ids: documentIds,
    question: question
  });
};