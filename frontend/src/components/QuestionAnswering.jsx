import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, Select, message, Collapse, List } from 'antd';
import { singleDocumentQA, knowledgeBaseQA, multiDocumentComparison } from '../api/qaApi';
import { getDocuments } from '../api/documentApi';

const { Panel } = Collapse;
const { Option } = Select;
const { TextArea } = Input;

const QuestionAnswering = () => {
  const [form] = Form.useForm();
  const [qaResult, setQaResult] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeKey, setActiveKey] = useState('1');
  const [documents, setDocuments] = useState([]);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (error) {
      console.error('加载文档列表失败:', error);
      message.error('加载文档列表失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleSingleDocumentQA = async (values) => {
    try {
      setLoading(true);
      const result = await singleDocumentQA(values.documentId, values.question);
      setQaResult(result);
      message.success('问答完成');
    } catch (error) {
      message.error('问答失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKnowledgeBaseQA = async (values) => {
    try {
      setLoading(true);
      const result = await knowledgeBaseQA(values.question);
      setQaResult(result);
      message.success('问答完成');
    } catch (error) {
      message.error('问答失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMultiDocumentComparison = async (values) => {
    try {
      setLoading(true);
      const documentIds = values.documentIds.map(id => parseInt(id));
      const result = await multiDocumentComparison(documentIds);
      setComparisonResult(result);
      message.success('对比完成');
    } catch (error) {
      message.error('对比失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="智能问答" style={{ height: '100%' }}>
      <Collapse activeKey={activeKey} onChange={setActiveKey}>
        <Panel header="单文档问答" key="1">
          <Form
            form={form}
            onFinish={handleSingleDocumentQA}
            layout="vertical"
          >
            <Form.Item
              name="documentId"
              label="选择文档"
              rules={[{ required: true, message: '请选择文档' }]}
            >
              <Select placeholder="请选择文档" loading={documents.length === 0}>
                {documents.map(doc => (
                  <Option key={doc.id} value={doc.id.toString()}>
                    {doc.filename}
                  </Option>
                ))}
              </Select>
            </Form.Item>
            
            <Form.Item
              name="question"
              label="问题"
              rules={[{ required: true, message: '请输入问题' }]}
            >
              <TextArea rows={4} placeholder="请输入您的问题" />
            </Form.Item>
            
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                提交问题
              </Button>
            </Form.Item>
          </Form>
          
          {qaResult && (
            <Card title="问答结果" size="small" style={{ marginTop: 16 }}>
              <p><strong>问题:</strong> {qaResult.question}</p>
              <p><strong>答案:</strong> {qaResult.answer}</p>
            </Card>
          )}
        </Panel>
        
        <Panel header="知识库问答" key="2">
          <Form
            form={form}
            onFinish={handleKnowledgeBaseQA}
            layout="vertical"
          >
            <Form.Item
              name="question"
              label="问题"
              rules={[{ required: true, message: '请输入问题' }]}
            >
              <TextArea rows={4} placeholder="请输入您的问题" />
            </Form.Item>
            
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                提交问题
              </Button>
            </Form.Item>
          </Form>
          
          {qaResult && (
            <Card title="问答结果" size="small" style={{ marginTop: 16 }}>
              <p><strong>问题:</strong> {qaResult.question}</p>
              <p><strong>答案:</strong> {qaResult.answer}</p>
            </Card>
          )}
        </Panel>
        
        <Panel header="多文档对比" key="3">
          <Form
            onFinish={handleMultiDocumentComparison}
            layout="vertical"
          >
            <Form.Item
              name="documentIds"
              label="选择文档（至少两个）"
              rules={[{ required: true, message: '请选择至少两个文档' }]}
            >
              <Select mode="multiple" placeholder="请选择文档" loading={documents.length === 0}>
                {documents.map(doc => (
                  <Option key={doc.id} value={doc.id.toString()}>
                    {doc.filename}
                  </Option>
                ))}
              </Select>
            </Form.Item>
            
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                开始对比
              </Button>
            </Form.Item>
          </Form>
          
          {comparisonResult && (
            <Card title="对比结果" size="small" style={{ marginTop: 16 }}>
              <h3>文档列表</h3>
              <List
                dataSource={comparisonResult.documents}
                renderItem={item => (
                  <List.Item>
                    ID: {item.id} - {item.title}
                  </List.Item>
                )}
              />
              
              <h3>长度对比</h3>
              <p>文档长度: {comparisonResult.comparison?.length_comparison?.document_lengths?.join(', ')}</p>
              <p>总长度: {comparisonResult.comparison?.length_comparison?.total_length}</p>
            </Card>
          )}
        </Panel>
      </Collapse>
    </Card>
  );
};

export default QuestionAnswering;