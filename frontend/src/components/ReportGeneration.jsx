import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, Radio, message, Space, Select } from 'antd';
import { generateReport } from '../api/reportApi';
import { getDocuments } from '../api/documentApi';

const { Option } = Select;

const ReportGeneration = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);

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

  const handleGenerateReport = async (values) => {
    try {
      setLoading(true);
      const response = await generateReport(values.format, values.title, values.document_ids);
      
      const blob = new Blob([response], { type: values.format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      // 使用标题作为文件名
      link.download = `${values.title.replace(' ', '_')}.${values.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success('报告已成功生成并开始下载');
    } catch (error) {
      message.error('报告生成失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="自定义分析报告生成" style={{ height: '100%' }}>
      <Form
        form={form}
        onFinish={handleGenerateReport}
        layout="vertical"
        initialValues={{ format: 'pdf', title: '智能文档分析报告' }}
        style={{ maxWidth: 600, margin: '0 auto' }}
      >
        <Form.Item
          name="document_ids"
          label="选择分析文档"
          rules={[{ required: true, message: '请至少选择一个文档' }]}
        >
          <Select
            mode="multiple"
            allowClear
            placeholder="请选择要分析的文档"
            optionFilterProp="children"
          >
            {documents.map(doc => (
              <Option key={doc.id} value={doc.id}>{doc.filename}</Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="title"
          label="报告标题"
          rules={[{ required: true, message: '请输入报告标题' }]}
        >
          <Input placeholder="例如：关于XX项目的技术分析报告" />
        </Form.Item>
        
        <Form.Item
          name="format"
          label="报告格式"
          rules={[{ required: true, message: '请选择报告格式' }]}
        >
          <Radio.Group>
            <Radio value="pdf">PDF</Radio>
            <Radio value="word">Word</Radio>
          </Radio.Group>
        </Form.Item>
        
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              {loading ? '正在生成...' : '生成报告'}
            </Button>
            <Button htmlType="button" onClick={() => form.resetFields()}>
              重置表单
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ReportGeneration;