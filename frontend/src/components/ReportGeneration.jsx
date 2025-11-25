import React, { useState } from 'react';
import { Card, Form, Input, Button, Radio, message, Space } from 'antd';
import { generateReport } from '../api/reportApi';

const ReportGeneration = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleGenerateReport = async (values) => {
    try {
      setLoading(true);
      const response = await generateReport(values.format, values.title);
      
      // 创建下载链接
      const blob = new Blob([response], { type: values.format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `report.${values.format}`;
      link.click();
      
      message.success('报告生成成功');
    } catch (error) {
      message.error('报告生成失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="报告生成" style={{ height: '100%' }}>
      <Form
        form={form}
        onFinish={handleGenerateReport}
        layout="vertical"
        initialValues={{ format: 'pdf' }}
      >
        <Form.Item
          name="title"
          label="报告标题"
          rules={[{ required: true, message: '请输入报告标题' }]}
        >
          <Input placeholder="请输入报告标题" />
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
              生成报告
            </Button>
            <Button htmlType="button" onClick={() => form.resetFields()}>
              重置
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ReportGeneration;