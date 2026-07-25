import {
  ArrowRightOutlined,
  CheckCircleFilled,
  KeyOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { Alert, Button, Card, Col, Progress, Row, Skeleton, Space, Tag } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { PageHeading } from '../components/PageHeading'
import { permissionApi, roleApi, systemApi, userApi } from '../services/api'

interface MetricCardProps {
  label: string
  value?: number
  loading: boolean
  icon: React.ReactNode
  tone: 'amber' | 'green' | 'blue'
  onClick: () => void
}

function MetricCard({
  label,
  value,
  loading,
  icon,
  tone,
  onClick,
}: MetricCardProps) {
  return (
    <Card className={`metric-card metric-card--${tone}`} bordered={false}>
      <div className="metric-card__top">
        <span className="metric-card__icon">{icon}</span>
        <Button type="text" icon={<ArrowRightOutlined />} onClick={onClick} />
      </div>
      {loading ? <Skeleton.Input active size="small" /> : <strong>{value ?? '—'}</strong>}
      <span className="metric-card__label">{label}</span>
    </Card>
  )
}

export function DashboardPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const hour = new Date().getHours()
  const greeting = hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'

  const healthQuery = useQuery({
    queryKey: ['system', 'health'],
    queryFn: systemApi.health,
    refetchInterval: 60_000,
  })
  const usersQuery = useQuery({
    queryKey: ['users', 'count'],
    queryFn: () => userApi.list({ page: 1, page_size: 1 }),
  })
  const rolesQuery = useQuery({
    queryKey: ['roles', 'count'],
    queryFn: () => roleApi.list({ page: 1, page_size: 1 }),
  })
  const permissionsQuery = useQuery({
    queryKey: ['permissions', 'count'],
    queryFn: () => permissionApi.list({ page: 1, page_size: 1 }),
  })

  const readyCount = [usersQuery, rolesQuery, permissionsQuery].filter(
    (query) => query.isSuccess,
  ).length

  return (
    <div>
      <PageHeading
        eyebrow="OVERVIEW"
        title={`${greeting}，${user?.username}`}
        description="从这里掌握平台基础数据，并快速进入账户与权限配置。"
        actions={
          <Tag
            className="health-tag"
            color={healthQuery.data?.status === 'ok' ? 'success' : 'warning'}
            icon={healthQuery.data?.status === 'ok' ? <CheckCircleFilled /> : undefined}
          >
            {healthQuery.data?.status === 'ok' ? '后端服务正常' : '服务状态待确认'}
          </Tag>
        }
      />

      <Row gutter={[18, 18]}>
        <Col xs={24} sm={8}>
          <MetricCard
            label="平台用户"
            value={usersQuery.data?.total}
            loading={usersQuery.isLoading}
            icon={<TeamOutlined />}
            tone="amber"
            onClick={() => navigate('/users')}
          />
        </Col>
        <Col xs={24} sm={8}>
          <MetricCard
            label="角色组"
            value={rolesQuery.data?.total}
            loading={rolesQuery.isLoading}
            icon={<SafetyCertificateOutlined />}
            tone="green"
            onClick={() => navigate('/roles')}
          />
        </Col>
        <Col xs={24} sm={8}>
          <MetricCard
            label="权限点"
            value={permissionsQuery.data?.total}
            loading={permissionsQuery.isLoading}
            icon={<KeyOutlined />}
            tone="blue"
            onClick={() => navigate('/permissions')}
          />
        </Col>
      </Row>

      <Row gutter={[18, 18]} className="dashboard-secondary">
        <Col xs={24} lg={15}>
          <Card className="surface-card setup-card" bordered={false}>
            <div className="section-kicker">GETTING STARTED</div>
            <h3>配置平台访问秩序</h3>
            <p>按权限点、角色、用户的顺序配置，可以更清晰地维护 RBAC 关系。</p>
            <div className="setup-steps">
              {[
                {
                  index: '01',
                  title: '定义权限点',
                  desc: '用稳定的 code 描述一项操作能力',
                  path: '/permissions',
                },
                {
                  index: '02',
                  title: '创建角色',
                  desc: '将一组权限组合成业务角色',
                  path: '/roles',
                },
                {
                  index: '03',
                  title: '分配给用户',
                  desc: '为账户授予一个或多个角色',
                  path: '/users',
                },
              ].map((step) => (
                <button key={step.index} onClick={() => navigate(step.path)}>
                  <span>{step.index}</span>
                  <div>
                    <strong>{step.title}</strong>
                    <small>{step.desc}</small>
                  </div>
                  <ArrowRightOutlined />
                </button>
              ))}
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={9}>
          <Card className="surface-card readiness-card" bordered={false}>
            <div className="section-kicker">SYSTEM READINESS</div>
            <h3>基础能力就绪度</h3>
            <div className="readiness-card__score">
              <Progress
                type="dashboard"
                percent={Math.round((readyCount / 3) * 100)}
                strokeColor="#eaa02b"
                trailColor="#eff0ea"
                size={132}
              />
              <p>已连接 {readyCount}/3 个核心资源</p>
            </div>
            <Space direction="vertical" size={10} className="readiness-card__checks">
              <span>
                <CheckCircleFilled /> 账户认证接口
              </span>
              <span>
                <CheckCircleFilled /> RBAC 数据模型
              </span>
              <span>
                <CheckCircleFilled /> 统一业务响应处理
              </span>
            </Space>
          </Card>
        </Col>
      </Row>

      <Alert
        className="dashboard-alert"
        type="warning"
        showIcon
        message="当前后端管理接口尚未全部接入权限依赖"
        description="本前端会携带登录令牌并提供管理入口，但真正的安全边界必须由后端 require_permission 负责。部署到非开发环境前请先完成后端鉴权加固。"
      />
    </div>
  )
}
