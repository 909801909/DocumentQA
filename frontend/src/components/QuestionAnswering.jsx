import React, { useState, useEffect, useRef } from 'react';
import { Layout, Card, Input, Button, Select, List, Avatar, Spin, message, Typography, Space, Tag, Tooltip } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, ClearOutlined, FileTextOutlined, DatabaseOutlined, DiffOutlined } from '@ant-design/icons';
import ReactMarkdown from 'react-markdown'; // 需要确保安装了 react-markdown，如果没有可以使用普通文本显示
import { singleDocumentQA, knowledgeBaseQA, multiDocumentComparison } from '../api/qaApi';
import { getDocuments } from '../api/documentApi';

const { Sider, Content } = Layout;
const { Option } = Select;
const { TextArea } = Input;
const { Text } = Typography;

const QuestionAnswering = () => {
  // 状态管理
  const [documents, setDocuments] = useState([]);
  const [mode, setMode] = useState('single'); // single, kb, compare
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [selectedCompareIds, setSelectedCompareIds] = useState([]);

  // 聊天记录 [{ role: 'user' | 'assistant', content: '...', type: 'text' | 'analysis' }]
  const [chatHistory, setChatHistory] = useState([
    { role: 'assistant', content: '你好！我是智能文档助手。请在左侧选择模式和文档，然后开始提问。' }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);

  const chatListRef = useRef(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  useEffect(() => {
    // 自动滚动到底部
    if (chatListRef.current) {
      chatListRef.current.scrollTop = chatListRef.current.scrollHeight;
    }
  }, [chatHistory]);

  const loadDocuments = async () => {
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (error) {
      message.error('加载文档列表失败');
    }
  };

  // 发送消息处理
  const handleSend = async () => {
    if (!inputValue.trim()) return;

    // 校验选择
    if (mode === 'single' && !selectedDocId) {
      message.warning('请先选择一个文档');
      return;
    }
    if (mode === 'compare' && selectedCompareIds.length < 2) {
      message.warning('请至少选择两个文档进行对比');
      return;
    }

    const question = inputValue;
    setInputValue('');

    // 添加用户消息
    const newHistory = [...chatHistory, { role: 'user', content: question }];
    setChatHistory(newHistory);
    setLoading(true);

    try {
      let result;
      // 提取纯文本历史用于发送给后端 (简化版，只发最近几轮)
      const contextHistory = newHistory
        .filter(msg => msg.role !== 'system')
        .slice(-6) // 保留最近6条
        .map(msg => ({ role: msg.role, content: msg.content }));

      if (mode === 'single') {
        result = await singleDocumentQA(selectedDocId, question, contextHistory);
      } else if (mode === 'kb') {
        result = await knowledgeBaseQA(question, contextHistory);
      } else if (mode === 'compare') {
        // 对比模式通常是直接生成报告，但也可以作为对话的一部分
        result = await multiDocumentComparison(selectedCompareIds, question); // 传递问题以便定向对比
      }

      // 处理返回结果
      let answerContent = '';
      if (mode === 'compare') {
        // 格式化对比结果
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
  };

  // 渲染消息气泡
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
          {/* 使用 ReactMarkdown 渲染 Markdown，如果未安装则直接显示文本 */}
          <div style={{ wordWrap: 'break-word', lineHeight: '1.6' }}>
             {/* 这里为了演示简单直接显示，实际建议用 ReactMarkdown */}
             <span dangerouslySetInnerHTML={{ __html: item.content.replace(/\n/g, '<br/>') }} />
          </div>
        </div>
        {isUser && <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#87d068', marginLeft: 10 }} />}
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
            </Select>
          </div>

          {mode === 'single' && (
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
            </ul>
          </div>
        </Space>
      </Sider>

      <Content style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* 聊天记录区域 */}
        <div
          ref={chatListRef}
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px',
            scrollBehavior: 'smooth'
          }}
        >
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