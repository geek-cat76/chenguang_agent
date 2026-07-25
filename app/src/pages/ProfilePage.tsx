import { CheckCircleFilled, MailOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import { Avatar, Card, Descriptions, Tag } from 'antd'
import { useAuth } from '../auth/AuthContext'
import { PageHeading } from '../components/PageHeading'

export function ProfilePage() {
  const { user } = useAuth()

  return (
    <div>
      <PageHeading
        eyebrow="ACCOUNT"
        title="个人信息"
        description="查看当前登录账户及会话身份信息。"
      />
      <Card className="surface-card profile-card" bordered={false}>
        <div className="profile-card__hero">
          <Avatar size={78}>{user?.username.slice(0, 1).toUpperCase()}</Avatar>
          <div>
            <span className="section-kicker">CURRENT ACCOUNT</span>
            <h2>{user?.username}</h2>
            <p>
              <MailOutlined /> {user?.email}
            </p>
          </div>
          <Tag color={user?.is_active ? 'success' : 'default'}>
            {user?.is_active ? '账户正常' : '账户停用'}
          </Tag>
        </div>
        <Descriptions column={{ xs: 1, sm: 2 }} className="profile-card__details">
          <Descriptions.Item label="用户 ID">#{user?.id}</Descriptions.Item>
          <Descriptions.Item label="登录方式">Bearer Token</Descriptions.Item>
          <Descriptions.Item label="认证状态">
            <span className="positive-text">
              <CheckCircleFilled /> 已通过认证
            </span>
          </Descriptions.Item>
          <Descriptions.Item label="权限模型">
            <SafetyCertificateOutlined /> User → Role → Permission
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </div>
  )
}
