import { PlusOutlined, SafetyCertificateOutlined } from '@ant-design/icons'
import {
  Alert,
  App,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
  type TableProps,
} from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { PageHeading } from '../components/PageHeading'
import { roleApi, userApi } from '../services/api'
import { getErrorMessage } from '../services/http'
import type { User, UserCreatePayload } from '../types/api'

interface AssignRolesPayload {
  userId: number
  roleIds: number[]
}

export function UsersPage() {
  const [createForm] = Form.useForm<UserCreatePayload>()
  const [rolesForm] = Form.useForm<{ role_ids: number[] }>()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [keyword, setKeyword] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const { message } = App.useApp()
  const queryClient = useQueryClient()

  const usersQuery = useQuery({
    queryKey: ['users', 'list', page, pageSize, keyword],
    queryFn: () =>
      userApi.list({
        page,
        page_size: pageSize,
        keyword: keyword || undefined,
      }),
  })

  const rolesQuery = useQuery({
    queryKey: ['roles', 'options'],
    queryFn: () => roleApi.list({ page: 1, page_size: 100 }),
    enabled: Boolean(selectedUser),
  })

  const userRolesQuery = useQuery({
    queryKey: ['users', selectedUser?.id, 'roles'],
    queryFn: () => userApi.getRoles(selectedUser!.id),
    enabled: Boolean(selectedUser),
  })

  useEffect(() => {
    if (!selectedUser || !userRolesQuery.data) return
    const userWithRoles = userRolesQuery.data[0]
    rolesForm.setFieldValue(
      'role_ids',
      userWithRoles?.roles.map((role) => role.id) ?? [],
    )
  }, [selectedUser, userRolesQuery.data, rolesForm])

  const createMutation = useMutation({
    mutationFn: userApi.create,
    onSuccess: async () => {
      message.success('用户创建成功')
      setCreateOpen(false)
      createForm.resetFields()
      await queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const assignRolesMutation = useMutation({
    mutationFn: ({ userId, roleIds }: AssignRolesPayload) =>
      userApi.assignRoles(userId, roleIds),
    onSuccess: async () => {
      message.success('用户角色已更新')
      setSelectedUser(null)
      rolesForm.resetFields()
      await queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const columns: TableProps<User>['columns'] = [
    {
      title: '用户',
      dataIndex: 'username',
      minWidth: 180,
      render: (username: string, record) => (
        <span className="cell-title">
          <strong>{username}</strong>
          <small>用户 ID · {record.id}</small>
        </span>
      ),
    },
    {
      title: '邮箱地址',
      dataIndex: 'email',
      minWidth: 230,
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      width: 110,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '正常' : '已停用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          icon={<SafetyCertificateOutlined />}
          onClick={() => {
            rolesForm.setFieldValue('role_ids', [])
            setSelectedUser(record)
          }}
        >
          分配角色
        </Button>
      ),
    },
  ]

  return (
    <div>
      <PageHeading
        eyebrow="IDENTITY"
        title="用户管理"
        description="创建平台账户，并通过角色为用户配置访问能力。"
        actions={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            新建用户
          </Button>
        }
      />

      {usersQuery.isError && (
        <Alert
          className="page-alert"
          type="error"
          showIcon
          message="用户列表加载失败"
          description={getErrorMessage(usersQuery.error)}
          action={<Button onClick={() => void usersQuery.refetch()}>重试</Button>}
        />
      )}

      <Card className="surface-card" bordered={false}>
        <div className="table-toolbar">
          <span className="table-toolbar__meta">
            共 {usersQuery.data?.total ?? 0} 个平台账户
          </span>
          <Input.Search
            allowClear
            placeholder="搜索用户名或邮箱"
            enterButton="搜索"
            onSearch={(value) => {
              setPage(1)
              setKeyword(value.trim())
            }}
          />
        </div>
        <Table<User>
          rowKey="id"
          columns={columns}
          dataSource={usersQuery.data?.items ?? []}
          loading={usersQuery.isLoading || usersQuery.isFetching}
          scroll={{ x: 760 }}
          pagination={{
            current: page,
            pageSize,
            total: usersQuery.data?.total ?? 0,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
            onChange: (nextPage, nextPageSize) => {
              setPage(nextPageSize !== pageSize ? 1 : nextPage)
              setPageSize(nextPageSize)
            },
          }}
        />
      </Card>

      <Modal
        title="新建平台用户"
        open={createOpen}
        okText="创建用户"
        cancelText="取消"
        confirmLoading={createMutation.isPending}
        onOk={() => void createForm.submit()}
        onCancel={() => {
          setCreateOpen(false)
          createForm.resetFields()
        }}
      >
        <p className="modal-note">
          当前接口创建的用户默认为启用状态。密码只会提交给后端进行哈希，不会在前端保存。
        </p>
        <Form<UserCreatePayload>
          form={createForm}
          layout="vertical"
          requiredMark={false}
          onFinish={(values) => createMutation.mutate(values)}
        >
          <Form.Item
            label="用户名"
            name="username"
            rules={[{ required: true, whitespace: true, message: '请输入用户名' }]}
          >
            <Input placeholder="例如：chenxi" autoComplete="off" />
          </Form.Item>
          <Form.Item
            label="邮箱"
            name="email"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '邮箱格式不正确' },
            ]}
          >
            <Input placeholder="name@example.com" autoComplete="off" />
          </Form.Item>
          <Form.Item
            label="初始密码"
            name="password"
            rules={[{ required: true, message: '请输入初始密码' }]}
          >
            <Input.Password placeholder="请输入初始密码" autoComplete="new-password" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`为 ${selectedUser?.username ?? ''} 分配角色`}
        open={Boolean(selectedUser)}
        okText="保存角色"
        cancelText="取消"
        confirmLoading={assignRolesMutation.isPending}
        onOk={() => void rolesForm.submit()}
        onCancel={() => {
          setSelectedUser(null)
          rolesForm.resetFields()
        }}
      >
        <p className="modal-note">保存后会整体替换该用户现有角色，请核对完整选择。</p>
        <Form<{ role_ids: number[] }>
          form={rolesForm}
          layout="vertical"
          onFinish={({ role_ids }) => {
            if (selectedUser) {
              assignRolesMutation.mutate({ userId: selectedUser.id, roleIds: role_ids })
            }
          }}
        >
          <Form.Item label="角色" name="role_ids" initialValue={[]}>
            <Select
              mode="multiple"
              allowClear
              loading={rolesQuery.isLoading || userRolesQuery.isLoading}
              placeholder="选择一个或多个角色"
              optionFilterProp="label"
              options={(rolesQuery.data?.items ?? []).map((role) => ({
                value: role.id,
                label: `${role.name}（${role.code}）`,
              }))}
            />
          </Form.Item>
          {(rolesQuery.isError || userRolesQuery.isError) && (
            <Alert
              type="error"
              showIcon
              message={getErrorMessage(rolesQuery.error || userRolesQuery.error)}
            />
          )}
          <Space size={6} wrap>
            {(userRolesQuery.data?.[0]?.roles ?? []).map((role) => (
              <Tag key={role.id}>{role.name}</Tag>
            ))}
          </Space>
        </Form>
      </Modal>
    </div>
  )
}
