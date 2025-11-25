import apiClient from './apiClient';

// 生成报告
export const generateReport = (format = 'pdf', title = '智能文档分析报告') => {
  return apiClient.post('/reports/generate', null, {
    params: { format, title },
    responseType: 'blob' // 重要：处理文件下载
  });
};