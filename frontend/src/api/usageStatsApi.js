import apiClient from './apiClient';

// 跟踪功能使用
export const trackFeature = (feature) => {
  return apiClient.post('/usage-stats/track-feature', null, {
    params: { feature }
  });
};

// 获取统计数据
export const getStatistics = () => {
  return apiClient.get('/usage-stats/statistics');
};