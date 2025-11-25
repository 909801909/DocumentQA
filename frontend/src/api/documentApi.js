import apiClient from './apiClient';
import axios from 'axios';

// 添加请求拦截器以提供更多调试信息
apiClient.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.baseURL, config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// 添加响应拦截器以提供更多调试信息
apiClient.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config?.url, response.data);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response || error.message);
    return Promise.reject(error);
  }
);

// 获取文档列表
export const getDocuments = (params) => {
  return apiClient.get('/documents/');
};

// 获取单个文档
export const getDocument = (id) => {
  return apiClient.get(`/documents/${id}/`);
};

// 上传文档
export const uploadDocument = (formData) => {
  // 使用axios直接发送请求，避免apiClient的默认配置影响文件上传
  return axios.post('/api/documents/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }).then(response => response.data);
};

// 删除文档
export const deleteDocument = (id) => {
  return apiClient.delete(`/documents/${id}/`);
};