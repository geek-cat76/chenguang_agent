import {
  DeleteOutlined,
  EditOutlined,
  KeyOutlined,
  PlusOutlined,
} from '@ant-design/icons'
import {
  Alert,
  App,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  type TableProps,
} from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { PageHeading } from '../components/PageHeading'
import { permissionApi, roleApi } from '../services/api'
import { getErrorMessage } from '../services/http'
import type { Role, RoleCreatePayload, RoleUpdatePayload } from '../types/api'

interface RoleFormValues {
  code: string
  name: string
  description?: string
}

interface AssignPermissionsPayload {
  roleId: number
  permissionIds: number[]
}

export function RolesPage() {
  const [roleForm] = Form.useForm<RoleFormValues>()
  const [permissionsForm] = Form.useForm<{ permission_ids: number[] }>()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [keyword, setKeyword] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editingRole, setEditingRole] = useState<Role | null>(null)
  const [permissionRole, setPermissionRole] = useState<Role | null>(null)
  const { message } = App.useApp()
  const queryClient = useQueryClient()

  const rolesQuery = useQuery({
    queryKey: ['roles', 'list', page, pageSize, keyword],
    queryFn: () =>
      roleApi.list({ page, page_size: pageSize, keyword: keyword || undefined }),
  })

  const permissionsQuery = useQuery({
    queryKey: ['permissions', 'options'],
    queryFn: () => permissionApi.list({ page: 1, page_size: 100 }),
    enabled: Boolean(permissionRole),
  })

  const roleDetailQuery = useQuery({
    queryKey: ['roles', permissionRole?.id, 'detail'],
    queryFn: () => roleApi.get(permissionRole!.id),
    enabled: Boolean(permissionRole),
  })

  useEffect(() => {
    if (!roleDetailQuery.data) return
    permissionsForm.setFieldValue(
      'permission_ids',
      roleDetailQuery.data.permissions.map((permission) => permission.id),
    )
  }, [roleDetailQuery.data, permissionsForm])

  const saveMutation = useMutation({
    mutationFn: (values: RoleFormValues) => {
      if (editingRole) {
        const payload: RoleUpdatePayload = {
          name: values.name,
          description: values.description || null,
        }
        return roleApi.update(editingRole.id, payload)
      }
      const payload: RoleCreatePayload = {
        code: values.code,
        name: values.name,
        description: values.description || null,
      }
      return roleApi.create(payload)
    },
    onSuccess: async () => {
      message.success(editingRole ? '角色已更新' : '角色创建成功')
      setFormOpen(false)
      setEditingRole(null)
      roleForm.resetFields()
      await queryClient.invalidateQueries({ queryKey: ['roles'] })
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const deleteMutation = useMutation({
    mutationFn: roleApi.remove,
    onSuccess: async () => {
      message.success('角色已删除')
      await queryClient.invalidateQueries({ queryKey: ['roles'] })
      await queryClient.invalidateQueries({ queryKey: ['users'] })
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const assignPermissionsMutation = useMutation({
    mutationFn: ({ roleId, permissionIds }: AssignPermissionsPayload) =>
      roleApi.assignPermissions(roleId, permissionIds),
    onSuccess: async () => {
      message.success('角色权限已更新')
      setPermissionRole(null)
      permissionsForm.resetFields()
      await queryClient.invalidateQueries({ queryKey: ['roles'] })
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const openCreate = () => {
    setEditingRole(null)
    roleForm.resetFields()
    setFormOpen(true)
  }

  const openEdit = (role: Role) => {
    setEditingRole(role)
    roleForm.setFieldsValue({
      code: role.code,
      name: role.name,
      description: role.description || undefined,
    })
    setFormOpen(true)
  }

  const columns: TableProps<Role>['columns'] = [
    {
      title: '角色',
      dataIndex: 'name',
      minWidth: 150,
      render: (name: string, record) => (
        <span className="cell-title">
          <strong>{name}</strong>
          <small>角色 ID · {record.id}</small>
        </span>
      ),
    },
    {
      title: '角色编码',
      dataIndex: 'code',
      minWidth: 140,
      render: (code: string) => <code className="resource-code">{code}</code>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      minWidth: 170,
      render: (description: string | null) => description || <span className="muted">—</span>,
    },
    {
      title: '已配置权限',
      dataIndex: 'permissions',
      minWidth: 210,
      render: (permissions: Role['permissions']) => (
        <div className="permission-tags">
          {permissions.length > 0 ? (
            <>
              {permissions.slice(0, 3).map((permission) => (
                <Tag key={permission.id} color="gold">
                  {permission.name}
                </Tag>
              ))}
              {permissions.length > 3 && <Tag>+{permissions.length - 3}</Tag>}
            </>
          ) : (
            <span className="muted">暂未配置</span>
          )}
        </div>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 220,
      render: (_, record) => (
        <Space size={2}>
          <Button
            type="link"
            icon={<KeyOutlined />}
            onClick={() => {
              permissionsForm.setFieldValue('permission_ids', [])
              setPermissionRole(record)
            }}
          >
            配置权限
          </Button>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="删除这个角色？"
            description="关联关系会同步解除，此操作无法撤销。"
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
            onConfirm={() => deleteMutation.mutate(record.id)}
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div className="management-page">
      <PageHeading
        eyebrow="ACCESS GROUPS"
        title="角色管理"
        description="把一组权限组合成稳定的业务角色，再分配给用户。"
        actions={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建角色
          </Button>
        }
      />

      {rolesQuery.isError && (
        <Alert
          className="page-alert"
          type="error"
          showIcon
          message="角色列表加载失败"
          description={getErrorMessage(rolesQuery.error)}
          action={<Button onClick={() => void rolesQuery.refetch()}>重试</Button>}
        />
      )}

      <Card className="surface-card" bordered={false}>
        <div className="table-toolbar">
          <span className="table-toolbar__meta">共 {rolesQuery.data?.total ?? 0} 个角色</span>
          <Input.Search
            allowClear
            placeholder="搜索角色编码或名称"
            enterButton="搜索"
            onSearch={(value) => {
              setPage(1)
              setKeyword(value.trim())
            }}
          />
        </div>
        <Table<Role>
          className="resource-table"
          rowKey="id"
          columns={columns}
          dataSource={rolesQuery.data?.items ?? []}
          loading={rolesQuery.isLoading || rolesQuery.isFetching}
          scroll={{ x: 'max-content' }}
          pagination={{
            current: page,
            pageSize,
            total: rolesQuery.data?.total ?? 0,
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
        title={editingRole ? '编辑角色' : '新建角色'}
        open={formOpen}
        okText={editingRole ? '保存修改' : '创建角色'}
        cancelText="取消"
        confirmLoading={saveMutation.isPending}
        onOk={() => void roleForm.submit()}
        onCancel={() => {
          setFormOpen(false)
          setEditingRole(null)
          roleForm.resetFields()
        }}
      >
        <p className="modal-note">角色编码是稳定业务标识，创建后不能修改。</p>
        <Form<RoleFormValues>
          form={roleForm}
          layout="vertical"
          requiredMark={false}
          onFinish={(values) => saveMutation.mutate(values)}
        >
          <Form.Item
            label="角色编码"
            name="code"
            rules={[{ required: true, whitespace: true, message: '请输入角色编码' }]}
          >
            <Input placeholder="例如：admin" disabled={Boolean(editingRole)} />
          </Form.Item>
          <Form.Item
            label="角色名称"
            name="name"
            rules={[{ required: true, whitespace: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="例如：系统管理员" />
          </Form.Item>
          <Form.Item label="角色描述" name="description">
            <Input.TextArea rows={3} placeholder="说明该角色的职责范围" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`配置 ${permissionRole?.name ?? ''} 的权限`}
        open={Boolean(permissionRole)}
        width={620}
        okText="保存权限"
        cancelText="取消"
        confirmLoading={assignPermissionsMutation.isPending}
        onOk={() => void permissionsForm.submit()}
        onCancel={() => {
          setPermissionRole(null)
          permissionsForm.resetFields()
        }}
      >
        <p className="modal-note">保存后会整体替换该角色现有权限，请核对完整选择。</p>
        <Form<{ permission_ids: number[] }>
          form={permissionsForm}
          layout="vertical"
          onFinish={({ permission_ids }) => {
            if (permissionRole) {
              assignPermissionsMutation.mutate({
                roleId: permissionRole.id,
                permissionIds: permission_ids,
              })
            }
          }}
        >
          <Form.Item label="权限点" name="permission_ids" initialValue={[]}>
            <Select
              mode="multiple"
              allowClear
              loading={permissionsQuery.isLoading || roleDetailQuery.isLoading}
              placeholder="选择一个或多个权限点"
              optionFilterProp="label"
              options={(permissionsQuery.data?.items ?? []).map((permission) => ({
                value: permission.id,
                label: `${permission.name}（${permission.code}）`,
              }))}
            />
          </Form.Item>
          {(permissionsQuery.isError || roleDetailQuery.isError) && (
            <Alert
              type="error"
              showIcon
              message={getErrorMessage(permissionsQuery.error || roleDetailQuery.error)}
            />
          )}
        </Form>
      </Modal>
    </div>
  )
}
