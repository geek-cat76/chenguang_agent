import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { App as AntdApp, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './auth/AuthContext'
import { queryClient } from './queryClient'
import './styles/global.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#e89a1d',
          colorInfo: '#e89a1d',
          colorTextBase: '#23302b',
          colorBgLayout: '#f6f7f3',
          borderRadius: 10,
          fontFamily:
            "Inter, 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif",
        },
        components: {
          Button: { controlHeight: 38, borderRadius: 9 },
          Input: { controlHeight: 40 },
          Table: { headerBg: '#fafaf7', headerColor: '#68716d' },
          Card: { borderRadiusLG: 16 },
          Modal: { borderRadiusLG: 18 },
        },
      }}
    >
      <AntdApp>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <BrowserRouter>
              <App />
            </BrowserRouter>
          </AuthProvider>
        </QueryClientProvider>
      </AntdApp>
    </ConfigProvider>
  </React.StrictMode>,
)
