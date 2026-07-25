import {
  DashboardOutlined,
  KeyOutlined,
  LogoutOutlined,
  MenuOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Avatar, Button, Dropdown, Layout, Menu, Space, Tag, Typography } from 'antd'
import { useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { BrandMark } from '../components/BrandMark'

const { Header, Sider, Content } = Layout

const navigation = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '工作台' },
  { key: '/users', icon: <TeamOutlined />, label: '用户管理' },
  { key: '/roles', icon: <SafetyCertificateOutlined />, label: '角色管理' },
  { key: '/permissions', icon: <KeyOutlined />, label: '权限管理' },
  { key: '/profile', icon: <UserOutlined />, label: '个人信息' },
]

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobile, setMobile] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const wideContentPaths = ['/roles', '/permissions']
  const contentClassName = wideContentPaths.includes(location.pathname)
    ? 'app-content app-content--wide'
    : 'app-content'

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <Layout className="app-shell">
      <Sider
        className="app-sider"
        width={248}
        collapsedWidth={mobile ? 0 : 76}
        collapsible
        collapsed={collapsed}
        trigger={null}
        breakpoint="lg"
        onBreakpoint={(broken) => {
          setMobile(broken)
          setCollapsed(broken)
        }}
      >
        <div className="app-sider__brand">
          <BrandMark compact={collapsed && !mobile} light />
        </div>
        <div className="app-sider__label">{!collapsed && '管理中心'}</div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={navigation}
          onClick={({ key }) => {
            navigate(key)
            if (mobile) setCollapsed(true)
          }}
        />
        {!collapsed && (
          <div className="app-sider__footer">
            <span className="app-sider__status-dot" />
            <div>
              <strong>晨光服务</strong>
              <small>管理控制台 · v0.1</small>
            </div>
          </div>
        )}
      </Sider>

      {mobile && !collapsed && (
        <button
          className="sider-mask"
          aria-label="关闭导航"
          onClick={() => setCollapsed(true)}
        />
      )}

      <Layout>
        <Header className="app-header">
          <Button
            className="app-header__menu"
            type="text"
            icon={<MenuOutlined />}
            aria-label="切换导航"
            onClick={() => setCollapsed((value) => !value)}
          />
          <div className="app-header__welcome">
            <Typography.Text type="secondary">今天也要让工作更简单</Typography.Text>
            <Tag color="gold">管理端</Tag>
          </div>
          <Dropdown
            placement="bottomRight"
            menu={{
              items: [
                {
                  key: 'profile',
                  icon: <UserOutlined />,
                  label: '个人信息',
                  onClick: () => navigate('/profile'),
                },
                { type: 'divider' },
                {
                  key: 'logout',
                  icon: <LogoutOutlined />,
                  label: '退出登录',
                  danger: true,
                  onClick: handleLogout,
                },
              ],
            }}
          >
            <Button type="text" className="account-trigger">
              <Space>
                <Avatar className="account-trigger__avatar">
                  {user?.username.slice(0, 1).toUpperCase()}
                </Avatar>
                <span className="account-trigger__copy">
                  <strong>{user?.username}</strong>
                  <small>{user?.email}</small>
                </span>
              </Space>
            </Button>
          </Dropdown>
        </Header>
        <Content className={contentClassName}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
