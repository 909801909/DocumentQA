import React, { useState, useEffect } from 'react';
import { Card, Button, message, Spin, Select, Space, Typography } from 'antd';
import ReactECharts from 'echarts-for-react';
import { buildKnowledgeGraph } from '../api/knowledgeGraphApi';
import { getDocuments } from '../api/documentApi';

const { Option } = Select;
const { Text } = Typography;

const KnowledgeGraph = () => {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (error) {
      message.error('加载文档列表失败');
    }
  };

  const handleGenerateGraph = async () => {
    if (!selectedDocId) {
      message.warning('请先选择一个文档');
      return;
    }
    try {
      setLoading(true);
      const data = await buildKnowledgeGraph(selectedDocId);
      if (data && data.nodes.length > 0) {
        setGraphData(data);
      } else {
        message.info('未能从该文档中提取有效的知识图谱。请尝试其他文档。');
        setGraphData(null);
      }
    } catch (error) {
      message.error('生成知识图谱失败: ' + error.message);
      setGraphData(null);
    } finally {
      setLoading(false);
    }
  };

  const getOption = () => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) return {};

    const nodes = graphData.nodes.map(node => ({
      id: node.id,
      name: node.label,
      symbolSize: Math.max(node.size, 15), // 调整节点大小逻辑
      itemStyle: {
        color: '#5470C6'
      },
      label: {
        show: node.size > 20, // 只有较大的节点才常驻显示标签
        position: 'right',
        formatter: '{b}'
      },
    }));

    const links = graphData.edges.map(edge => ({
      source: edge.source,
      target: edge.target,
      label: {
        show: true, // 直接在边上显示关系
        formatter: edge.label,
        fontSize: 10,
        color: '#333'
      },
      lineStyle: {
        color: '#999',
        curveness: 0.1
      }
    }));

    return {
      title: {
        text: '文档关系图谱',
        subtext: documents.find(d => d.id === selectedDocId)?.filename || '',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: params => {
          if (params.dataType === 'node') {
            return `<b>实体: ${params.name}</b>`;
          }
          if (params.dataType === 'edge') {
            return `关系: ${params.data.source} -[${params.data.label.formatter}]-> ${params.data.target}`;
          }
          return '';
        }
      },
      series: [
        {
          type: 'graph',
          layout: 'force',
          roam: true,
          data: nodes,
          links: links,
          force: {
            repulsion: 600, // 进一步增加斥力
            edgeLength: 200,
            friction: 0.6,
            gravity: 0.1
          },
          edgeSymbol: ['none', 'arrow'], // 使用箭头表示有向关系
          edgeSymbolSize: [4, 10],
          edgeLabel: {
            show: true,
            position: 'middle',
            fontSize: 10,
            formatter: (params) => params.data.label.formatter,
          },
          label: {
            show: true,
            position: 'top',
          },
          emphasis: {
            focus: 'adjacency',
            label: {
              show: true
            },
            lineStyle: {
              width: 4
            }
          }
        }
      ]
    };
  };

  return (
    <Card 
      title="知识图谱生成"
      extra={
        <Space>
          <Select
            showSearch
            style={{ width: 250 }}
            placeholder="请选择一个文档"
            optionFilterProp="children"
            onChange={value => {
              setSelectedDocId(value);
              setGraphData(null);
            }}
            value={selectedDocId}
            allowClear
          >
            {documents.map(doc => (
              <Option key={doc.id} value={doc.id}>{doc.filename}</Option>
            ))}
          </Select>
          <Button onClick={handleGenerateGraph} loading={loading} type="primary">
            生成图谱
          </Button>
        </Space>
      }
      style={{ height: '100%' }}
    >
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <Spin tip="正在深入分析文档，构建关系中..." size="large" />
        </div>
      ) : graphData ? (
        <ReactECharts option={getOption()} style={{ height: 'calc(100vh - 250px)' }} notMerge={true} lazyUpdate={true} />
      ) : (
        <div style={{ textAlign: 'center', paddingTop: '50px' }}>
          <Text type="secondary">请选择一个文档，然后点击“生成图谱”按钮</Text>
        </div>
      )}
    </Card>
  );
};

export default KnowledgeGraph;