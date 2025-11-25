import React, { useState, useEffect } from 'react';
import { Card, Button, message, Spin } from 'antd';
import ReactECharts from 'echarts-for-react';
import { buildKnowledgeGraph } from '../api/knowledgeGraphApi';

const KnowledgeGraph = () => {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadKnowledgeGraph();
  }, []);

  const loadKnowledgeGraph = async () => {
    try {
      setLoading(true);
      const data = await buildKnowledgeGraph();
      setGraphData(data);
    } catch (error) {
      message.error('加载知识图谱失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getOption = () => {
    if (!graphData) return {};

    // 转换节点数据
    const nodes = graphData.nodes.map(node => ({
      id: node.id,
      name: node.label,
      symbolSize: node.size,
      itemStyle: {
        color: '#87CEEB'
      }
    }));

    // 转换边数据
    const links = graphData.edges.map(edge => ({
      source: edge.source,
      target: edge.target,
      name: edge.label,
      lineStyle: {
        color: '#999'
      }
    }));

    return {
      title: {
        text: '知识图谱'
      },
      tooltip: {},
      animationDuration: 1500,
      animationEasingUpdate: 'quinticInOut',
      series: [
        {
          type: 'graph',
          layout: 'force',
          symbolSize: 50,
          roam: true,
          label: {
            show: true
          },
          edgeSymbol: ['circle', 'arrow'],
          edgeSymbolSize: [4, 10],
          edgeLabel: {
            fontSize: 20
          },
          data: nodes,
          links: links,
          lineStyle: {
            opacity: 0.9,
            width: 2,
            curveness: 0
          },
          force: {
            repulsion: 100
          }
        }
      ]
    };
  };

  return (
    <Card 
      title="知识图谱" 
      extra={
        <Button onClick={loadKnowledgeGraph} loading={loading}>
          刷新
        </Button>
      }
      style={{ height: '100%' }}
    >
      {loading ? (
        <Spin size="large" />
      ) : graphData ? (
        <ReactECharts option={getOption()} style={{ height: '600px' }} />
      ) : (
        <p>暂无数据，请先上传文档</p>
      )}
    </Card>
  );
};

export default KnowledgeGraph;