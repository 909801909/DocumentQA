import React from 'react';
import { Layout, Menu, theme } from 'antd';
import {
  UploadOutlined,
  FileSearchOutlined,
  ClusterOutlined,
  FilePdfOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import './App.css';

import DocumentManagement from './components/DocumentManagement';
import QuestionAnswering from './components/QuestionAnswering';
import KnowledgeGraph from './components/KnowledgeGraph';
import ReportGeneration from './components/ReportGeneration';
import UsageStatistics from './components/UsageStatistics';

const { Header, Content, Footer, Sider } = Layout;

const App = () => {
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  const [current, setCurrent] = React.useState('document');

  const onClick = (e) => {
    setCurrent(e.key);
  };

  const renderContent = () => {
    switch (current) {
      case 'document':
        return <DocumentManagement />;
      case 'qa':
        return <QuestionAnswering />;
      case 'knowledge':
        return <KnowledgeGraph />;
      case 'report':
        return <ReportGeneration />;
      case 'stats':
        return <UsageStatistics />;
      default:
        return <DocumentManagement />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible>
        <div className="demo-logo-vertical" />
        <Menu 
          theme="dark" 
          mode="inline" 
          selectedKeys={[current]} 
          onClick={onClick}
          items={[
            {
              key: 'document',
              icon: <UploadOutlined />,
              label: '文档管理',
            },
            {
              key: 'qa',
              icon: <FileSearchOutlined />,
              label: '智能问答',
            },
            {
              key: 'knowledge',
              icon: <ClusterOutlined />,
              label: '知识图谱',
            },
            {
              key: 'report',
              icon: <FilePdfOutlined />,
              label: '报告生成',
            },
            {
              key: 'stats',
              icon: <BarChartOutlined />,
              label: '使用统计',
            },
          ]}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: colorBgContainer }} />
        <Content style={{ margin: '16px' }}>
          <div style={{ padding: 24, minHeight: 360, background: colorBgContainer }}>
            {renderContent()}
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          智能文档问答系统 ©2025 Created by AI Team
        </Footer>
      </Layout>
    </Layout>
  );
};

export default App;