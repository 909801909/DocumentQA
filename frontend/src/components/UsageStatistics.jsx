import React, { useState, useEffect } from 'react';
import { Card, Button, message, Spin, Table } from 'antd';
import ReactECharts from 'echarts-for-react';
import { getStatistics } from '../api/usageStatsApi';

const UsageStatistics = () => {
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      setLoading(true);
      const data = await getStatistics();
      setStatistics(data);
    } catch (error) {
      message.error('加载统计数据失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getChartOption = () => {
    if (!statistics) return {};

    const features = Object.keys(statistics);
    const counts = Object.values(statistics);

    return {
      title: {
        text: '功能使用统计'
      },
      tooltip: {},
      xAxis: {
        type: 'category',
        data: features
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          type: 'bar',
          data: counts,
          itemStyle: {
            color: '#4CAF50'
          }
        }
      ]
    };
  };

  const columns = [
    {
      title: '功能',
      dataIndex: 'feature',
      key: 'feature',
    },
    {
      title: '使用次数',
      dataIndex: 'count',
      key: 'count',
    },
  ];

  const tableData = statistics ? Object.keys(statistics).map(key => ({
    key,
    feature: key,
    count: statistics[key]
  })) : [];

  return (
    <Card 
      title="使用统计" 
      extra={
        <Button onClick={loadStatistics} loading={loading}>
          刷新
        </Button>
      }
      style={{ height: '100%' }}
    >
      {loading ? (
        <Spin size="large" />
      ) : statistics ? (
        <>
          <ReactECharts option={getChartOption()} style={{ height: '400px' }} />
          <Table 
            columns={columns} 
            dataSource={tableData} 
            pagination={false}
            style={{ marginTop: '20px' }}
          />
        </>
      ) : (
        <p>暂无统计数据</p>
      )}
    </Card>
  );
};

export default UsageStatistics;