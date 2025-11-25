import React, { useState, useEffect } from 'react';
import { Table, Button, Upload, message, Popconfirm, Card, Space } from 'antd';
import { UploadOutlined, DeleteOutlined, DownloadOutlined } from '@ant-design/icons';
import { getDocuments, uploadDocument, deleteDocument } from '../api/documentApi';

const DocumentManagement = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await getDocuments();
      setDocuments(data);
    } catch (error) {
      console.error('Load documents error:', error);
      message.error('加载文档失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async ({ file, onSuccess, onError }) => {
    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);
      
      console.log('Uploading file:', file);
      
      const response = await uploadDocument(formData);
      console.log('Upload response:', response);
      
      message.success('文档上传成功');
      loadDocuments(); // 重新加载文档列表
      
      onSuccess(response);
    } catch (error) {
      console.error('Upload error:', error);
      // 显示更详细的错误信息
      const errorMessage = error.response?.data?.detail 
        ? (Array.isArray(error.response.data.detail) 
           ? error.response.data.detail.map(d => d.msg || d).join(', ')
           : error.response.data.detail)
        : error.message;
      message.error('文档上传失败: ' + errorMessage);
      onError(error);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteDocument(id);
      message.success('文档删除成功');
      loadDocuments(); // 重新加载文档列表
    } catch (error) {
      console.error('Delete error:', error);
      message.error('文档删除失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button icon={<DownloadOutlined />} onClick={() => message.info('下载功能待实现')}>下载</Button>
          <Popconfirm
            title="确认删除?"
            description="确定要删除这个文档吗?"
            onConfirm={() => handleDelete(record.id)}
            okText="确认"
            cancelText="取消"
          >
            <Button icon={<DeleteOutlined />} danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const uploadProps = {
    customRequest: handleUpload,
    showUploadList: true,
    maxCount: 1,
  };

  return (
    <Card title="文档管理" style={{ height: '100%' }}>
      <Upload {...uploadProps}>
        <Button icon={<UploadOutlined />} loading={uploading} disabled={uploading}>
          上传文档
        </Button>
      </Upload>
      
      <Table
        style={{ marginTop: '20px' }}
        columns={columns}
        dataSource={documents}
        loading={loading}
        rowKey="id"
        pagination={{
          pageSize: 10,
        }}
      />
    </Card>
  );
};

export default DocumentManagement;