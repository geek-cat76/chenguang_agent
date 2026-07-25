import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import {
  Alert,
  App,
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Space,
  Table,
  type TableProps,
} from 'antd'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { PageHeading } from '../components/PageHeading'
import { permissionApi } from '../services/api'
import { getErrorMessage } from '../services/http'
import type {
  Permission,
  PermissionCreatePayload,
  PermissionUpdatePayload,
} from '../types/api'

interface PermissionFormValues {
  code: string
  name: string
  description?: string
}

export function PermissionsPage() {
  const [form] = Form.useForm<PermissionFormValues>()
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [keyword, setKeyword] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editingPermission, setEditingPermission] = useState<Permission | null>(null)
  const { message } = App.useApp()
  const queryClient = useQueryClient()

  const permissionsQuery = useQuery({
    queryKey: ['permissions', 'list', page, pageSize, keyword],
    queryFn: () =>
      permissionApi.list({ page, page_size: pageSize, keyword: keyword || undefined }),
  })

  const saveMutation = useMutation({
    mutationFn: (values: PermissionFormValues) => {
      if (editingPermission) {
        const payload: PermissionUpdatePayload = {
          name: values.name,
          description: values.description || null,
        }
        return permissionApi.update(editingPermission.id, payload)
      }
      const payload: PermissionCreatePayload = {
        code: values.code,
        name: values.name,
        description: values.description || null,
      }
      return permissionApi.create(payload)
    },
    onSuccess: async () => {
      message.success(editingPermission ? '权限已更新' : '权限创建成功')
      setFormOpen(false)
      setEditingPermission(null)
      form.resetFields()
      await queryClient.invalidateQueries({ queryKey: ['permissions'] })
      await queryClient.invalidateQueries({ queryKey: ['roles'] })
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const deleteMutation = useMutation({
    mutationFn: permissionApi.remove,
    onSuccess: async () => {
      message.success('权限已删除')
      await queryClient.invalidateQueries({ queryKey: ['permissions'] })
      await queryClient.invalidateQueries({ queryKey: ['roles'] })
    },
    onError: (error) => message.error(getErrorMessage(error)),
  })

  const openCreate = () => {
    setEditingPermission(null)
    form.resetFields()
    setFormOpen(true)
  }

  const openEdit = (permission: Permission) => {
    setEditingPermission(permission)
    form.setFieldsValue({
      code: permission.code,
      name: permission.name,
      description: permission.description || undefined,
    })
    setFormOpen(true)
  }

  const columns: TableProps<Permission>['columns'] = [
    {
      title: '权限名称',
      dataIndex: 'name',
      minWidth: 170,
      render: (name: string, record) => (
        <span className="cell-title">
          <strong>{name}</strong>
          <small>权限 ID · {record.id}</small>
        </span>
      ),
    },
    {
      title: '权限编码',
      dataIndex: 'code',
      minWidth: 190,
      render: (code: string) => <code className="resource-code">{code}</code>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      minWidth: 220,
      render: (description: string | null) => description || <span className="muted">—</span>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space size={2}>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(record)}>
            编辑
          </Button>
          <Popconfirm
            title="删除这个权限？"
            description="角色中的关联权限会同步解除。"
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
        eyebrow="CAPABILITIES"
        title="权限管理"
        description="使用稳定的权限编码定义平台中的最小操作能力。"
        actions={
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            新建权限
          </Button>
        }
      />

      {permissionsQuery.isError && (
        <Alert
          className="page-alert"
          type="error"
          showIcon
          message="权限列表加载失败"
          description={getErrorMessage(permissionsQuery.error)}
          action={<Button onClick={() => void permissionsQuery.refetch()}>重试</Button>}
        />
      )}

      <Card className="surface-card" bordered={false}>
        <div className="table-toolbar">
          <span className="table-toolbar__meta">
            共 {permissionsQuery.data?.total ?? 0} 个权限点
          </span>
          <Input.Search
            allowClear
            placeholder="搜索权限编码或名称"
            enterButton="搜索"
            onSearch={(value) => {
              setPage(1)
              setKeyword(value.trim())
            }}
          />
        </div>
        <Table<Permission>
          className="resource-table"
          rowKey="id"
          columns={columns}
          dataSource={permissionsQuery.data?.items ?? []}
          loading={permissionsQuery.isLoading || permissionsQuery.isFetching}
          scroll={{ x: 'max-content' }}
          pagination={{
            current: page,
            pageSize,
            total: permissionsQuery.data?.total ?? 0,
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
        title={editingPermission ? '编辑权限' : '新建权限'}
        open={formOpen}
        okText={editingPermission ? '保存修改' : '创建权限'}
        cancelText="取消"
        confirmLoading={saveMutation.isPending}
        onOk={() => void form.submit()}
        onCancel={() => {
          setFormOpen(false)
          setEditingPermission(null)
          form.resetFields()
        }}
      >
        <p className="modal-note">
          建议使用“资源:动作”格式，例如 user:list。权限编码创建后不能修改。
        </p>
        <Form<PermissionFormValues>
          form={form}
          layout="vertical"
          requiredMark={false}
          onFinish={(values) => saveMutation.mutate(values)}
        >
          <Form.Item
            label="权限编码"
            name="code"
            rules={[{ required: true, whitespace: true, message: '请输入权限编码' }]}
          >
            <Input placeholder="例如：user:list" disabled={Boolean(editingPermission)} />
          </Form.Item>
          <Form.Item
            label="权限名称"
            name="name"
            rules={[{ required: true, whitespace: true, message: '请输入权限名称' }]}
          >
            <Input placeholder="例如：查看用户列表" />
          </Form.Item>
          <Form.Item label="权限描述" name="description">
            <Input.TextArea rows={3} placeholder="说明该权限允许执行的操作" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
