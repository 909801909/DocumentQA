import React, { useState, useEffect, useRef } from 'react';
import { Layout, Card, Input, Button, Select, List, Avatar, Spin, message, Typography, Space, Tag, Tooltip, Row, Col } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, ClearOutlined, FileTextOutlined, DatabaseOutlined, DiffOutlined, AppstoreOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { singleDocumentQA, knowledgeBaseQA, multiDocumentComparison, multiModelQA } from '../api/qaApi';
import { getDocuments } from '../api/documentApi';

const { Sider, Content } = Layout;
const { Option } = Select;
const { TextArea } = Input;
const { Text, Title } = Typography;

const QuestionAnswering = () => {
  const [documents, setDocuments] = useState([]);
  const [mode, setMode] = useState('single'); // single, kb, compare, arena
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [selectedCompareIds, setSelectedCompareIds] = useState([]);

  const [chatHistory, setChatHistory] = useState([
    { role: 'assistant', content: '你好！我是智能文档助手。请在左侧选择模式和文档，然后开始提问。' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);

  // 竞技场模式的专用状态
  const [arenaResults, setArenaResults] = useState(null);

  const chatListRef = useRef(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  useEffect(() => {
    if (chatListRef.current) {
      chatListRef.current.scrollTop = chatListRef.current.scrollHeight;
    }
  }, [chatHistory, arenaResults]);

  const loadDocuments = async () => {
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (error) {
      message.error('加载文档列表失败');
    }
  };

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    if ((mode === 'single' || mode === 'arena') && !selectedDocId) {
      message.warning('请先选择一个文档');
      return;
    }
    if (mode === 'compare' && selectedCompareIds.length < 2) {
      message.warning('请至少选择两个文档进行对比');
      return;
    }

    const question = inputValue;
    setInputValue('');
    setLoading(true);

    // 竞技场模式特殊处理
    if (mode === 'arena') {
      setArenaResults(null); // 清空上次结果
      try {
        const result = await multiModelQA(selectedDocId, question);
        setArenaResults(result.answers);
      } catch (error) {
        message.error(`竞技场模式出错: ${error.message}`);
      } finally {
        setLoading(false);
      }
      return;
    }

    // 普通模式处理
    const newHistory = [...chatHistory, { role: 'user', content: question }];
    setChatHistory(newHistory);

    try {
      let result;
      const contextHistory = newHistory
        .filter(msg => msg.role !== 'system')
        .slice(-6)
        .map(msg => ({ role: msg.role, content: msg.content }));

      if (mode === 'single') {
        result = await singleDocumentQA(selectedDocId, question, contextHistory);
      } else if (mode === 'kb') {
        result = await knowledgeBaseQA(question, contextHistory);
      } else if (mode === 'compare') {
        result = await multiDocumentComparison(selectedCompareIds, question);
      }

      let answerContent = '';
      if (mode === 'compare') {
        answerContent = `**文档对比分析：**\n\n${result.ai_analysis}\n\n**统计数据：**\n* 文档总数: ${result.documents.length}\n* 总字数: ${result.comparison.length_comparison.total_length}`;
      } else {
        answerContent = result.answer;
      }

      setChatHistory(prev => [...prev, { role: 'assistant', content: answerContent }]);
    } catch (error) {
      setChatHistory(prev => [...prev, { role: 'assistant', content: `❌ 发生错误: ${error.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setChatHistory([{ role: 'assistant', content: '对话已清空。我们可以重新开始了。' }]);
    setArenaResults(null);
  };

  const renderMessage = (item) => {
    const isUser = item.role === 'user';
    return (
      <div style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 20,
        padding: '0 10px'
      }}>
        {!isUser && <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff', marginRight: 10 }} />}
        <div style={{
          maxWidth: '70%',
          backgroundColor: isUser ? '#e6f7ff' : '#f5f5f5',
          border: isUser ? '1px solid #91d5ff' : '1px solid #d9d9d9',
          borderRadius: 8,
          padding: '12px 16px',
          boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
        }}>
          <div style={{ wordWrap: 'break-word', lineHeight: '1.6' }}>
             <ReactMarkdown>{item.content}</ReactMarkdown>
          </div>
        </div>
        {isUser && <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#87d068', marginLeft: 10 }} />}
      </div>
    );
  };

  // 渲染竞技场四宫格
  const renderArena = () => {
    if (!arenaResults && !loading) {
      return (
        <div style={{ textAlign: 'center', marginTop: 100, color: '#999' }}>
          <AppstoreOutlined style={{ fontSize: 48, marginBottom: 20 }} />
          <p>请在下方输入问题，4个大模型将同时为您解答</p>
        </div>
      );
    }

    return (
      <div style={{ padding: 20, height: '100%', overflowY: 'auto' }}>
        {loading && (
          <div style={{ textAlign: 'center', marginBottom: 20 }}>
            <Spin tip="4位选手正在激烈思考中..." size="large" />
          </div>
        )}
        
        {arenaResults && (
          <Row gutter={[16, 16]}>
            {Object.entries(arenaResults).map(([modelName, answer], index) => (
              <Col span={12} key={modelName}>
                <Card 
                  title={<><RobotOutlined /> {modelName}</>} 
                  bordered={true}
                  headStyle={{ backgroundColor: '#fafafa' }}
                  style={{ height: '100%', minHeight: 300 }}
                  extra={<Tag color="blue">选手 {index + 1}</Tag>}
                >
                  <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                    <ReactMarkdown>{answer}</ReactMarkdown>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </div>
    );
  };

  return (
    <Layout style={{ height: 'calc(100vh - 120px)', background: '#fff' }}>
      <Sider width={300} theme="light" style={{ borderRight: '1px solid #f0f0f0', padding: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Text strong>问答模式</Text>
            <Select
              value={mode}
              onChange={setMode}
              style={{ width: '100%', marginTop: 8 }}
            >
              <Option value="single"><FileTextOutlined /> 单文档问答</Option>
              <Option value="kb"><DatabaseOutlined /> 知识库问答</Option>
              <Option value="compare"><DiffOutlined /> 多文档对比</Option>
              <Option value="arena"><AppstoreOutlined /> 多模型竞技场</Option>
            </Select>
          </div>

          {(mode === 'single' || mode === 'arena') && (
            <div>
              <Text strong>选择文档</Text>
              <Select
                showSearch
                style={{ width: '100%', marginTop: 8 }}
                placeholder="请选择一个文档"
                optionFilterProp="children"
                onChange={setSelectedDocId}
                value={selectedDocId}
              >
                {documents.map(doc => (
                  <Option key={doc.id} value={doc.id}>{doc.filename}</Option>
                ))}
              </Select>
            </div>
          )}

          {mode === 'compare' && (
            <div>
              <Text strong>选择对比文档 (多选)</Text>
              <Select
                mode="multiple"
                style={{ width: '100%', marginTop: 8 }}
                placeholder="选择至少两个文档"
                onChange={setSelectedCompareIds}
                value={selectedCompareIds}
              >
                {documents.map(doc => (
                  <Option key={doc.id} value={doc.id}>{doc.filename}</Option>
                ))}
              </Select>
            </div>
          )}

          <Button icon={<ClearOutlined />} onClick={clearChat} block>
            清空对话
          </Button>

          <div style={{ marginTop: 20, fontSize: 12, color: '#999' }}>
            <p>提示：</p>
            <ul>
              <li>单文档：针对特定文件深入提问。</li>
              <li>知识库：综合所有文档内容回答。</li>
              <li>对比：智能分析多个文档的异同。</li>
              <li>竞技场：4个模型同台竞技，优劣立判。</li>
            </ul>
          </div>
        </Space>
      </Sider>

      <Content style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* 内容区域：根据模式切换显示 */}
        <div
          ref={chatListRef}
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '0',
            scrollBehavior: 'smooth',
            backgroundColor: mode === 'arena' ? '#f0f2f5' : '#fff'
          }}
        >
          {mode === 'arena' ? renderArena() : (
            <div style={{ padding: '20px' }}>
              {chatHistory.map((item, index) => (
                <div key={index}>{renderMessage(item)}</div>
              ))}
              {loading && (
                <div style={{ display: 'flex', justifyContent: 'flex-start', padding: '0 10px', marginBottom: 20 }}>
                   <Avatar icon={<RobotOutlined />} style={{ backgroundColor: '#1890ff', marginRight: 10 }} />
                   <Spin tip="思考中..." />
                </div>
              )}
            </div>
          )}
        </div>

        {/* 输入区域 */}
        <div style={{
          padding: '20px',
          borderTop: '1px solid #f0f0f0',
          backgroundColor: '#fff'
        }}>
          <div style={{ display: 'flex', gap: 10 }}>
            <TextArea
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              placeholder={mode === 'compare' ? "请输入对比的具体关注点（可选）" : "输入您的问题..."}
              autoSize={{ minRows: 1, maxRows: 4 }}
              onPressEnter={(e) => {
                if (!e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={loading}
              style={{ resize: 'none' }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              loading={loading}
              style={{ height: 'auto' }}
            >
              发送
            </Button>
          </div>
          <Text type="secondary" style={{ fontSize: 12, marginTop: 5, display: 'block', textAlign: 'center' }}>
            AI 生成的内容可能不准确，请核对重要信息。
          </Text>
        </div>
      </Content>
    </Layout>
  );
};

export default QuestionAnswering;