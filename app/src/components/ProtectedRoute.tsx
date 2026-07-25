import { Button, Result, Spin } from 'antd'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export function ProtectedRoute() {
  const { token, user, isLoading, error, retry, logout } = useAuth()
  const location = useLocation()

  if (!token) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  if (isLoading) {
    return (
      <div className="screen-loading">
        <Spin size="large" />
        <span>正在确认登录状态…</span>
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className="screen-result">
        <Result
          status="warning"
          title="暂时无法获取账户信息"
          subTitle={error?.message || '请检查后端服务后重试'}
          extra={[
            <Button type="primary" key="retry" onClick={retry}>
              重新连接
            </Button>,
            <Button key="logout" onClick={logout}>
              返回登录
            </Button>,
          ]}
        />
      </div>
    )
  }

  return <Outlet />
}
