import type {
  Captcha,
  HealthStatus,
  LoginPayload,
  PageParams,
  PageResult,
  Permission,
  PermissionCreatePayload,
  PermissionUpdatePayload,
  Role,
  RoleCreatePayload,
  RoleUpdatePayload,
  TokenResponse,
  User,
  UserCreatePayload,
  UserWithRoles,
} from '../types/api'
import { request, requestRaw } from './http'

export const authApi = {
  getCaptcha: () => request<Captcha>({ method: 'GET', url: '/api/v1/captcha' }),
  login: (data: LoginPayload) =>
    request<TokenResponse>({ method: 'POST', url: '/api/v1/auth/login', data }),
}

export const userApi = {
  me: () => request<User>({ method: 'GET', url: '/api/v1/users/me' }),
  list: (params: PageParams) =>
    request<PageResult<User>>({ method: 'GET', url: '/api/v1/users', params }),
  get: (userId: number) =>
    request<User>({ method: 'GET', url: `/api/v1/users/${userId}` }),
  create: (data: UserCreatePayload) =>
    request<User>({ method: 'POST', url: '/api/v1/users', data }),
  getRoles: (userId: number) =>
    request<UserWithRoles[]>({
      method: 'GET',
      url: `/api/v1/users/${userId}/roles`,
    }),
  assignRoles: (userId: number, roleIds: number[]) =>
    request<User>({
      method: 'PUT',
      url: `/api/v1/users/${userId}/roles`,
      // OpenAPI 明确要求原始数组，不能包装成 { role_ids: [...] }。
      data: roleIds,
    }),
}

export const roleApi = {
  list: (params: PageParams) =>
    request<PageResult<Role>>({ method: 'GET', url: '/api/v1/roles', params }),
  get: (roleId: number) =>
    request<Role>({ method: 'GET', url: `/api/v1/roles/${roleId}` }),
  create: (data: RoleCreatePayload) =>
    request<Role>({ method: 'POST', url: '/api/v1/roles', data }),
  update: (roleId: number, data: RoleUpdatePayload) =>
    request<Role>({ method: 'PUT', url: `/api/v1/roles/${roleId}`, data }),
  remove: (roleId: number) =>
    request<null>({ method: 'DELETE', url: `/api/v1/roles/${roleId}` }),
  assignPermissions: (roleId: number, permissionIds: number[]) =>
    request<Role>({
      method: 'PUT',
      url: `/api/v1/roles/${roleId}/permissions`,
      data: { permission_ids: permissionIds },
    }),
}

export const permissionApi = {
  list: (params: PageParams) =>
    request<PageResult<Permission>>({
      method: 'GET',
      // 后端列表路由显式声明了尾斜杠，保留它可避免重定向。
      url: '/api/v1/permissions/',
      params,
    }),
  get: (permissionId: number) =>
    request<Permission>({
      method: 'GET',
      url: `/api/v1/permissions/${permissionId}`,
    }),
  create: (data: PermissionCreatePayload) =>
    request<Permission>({
      method: 'POST',
      url: '/api/v1/permissions/',
      data,
    }),
  update: (permissionId: number, data: PermissionUpdatePayload) =>
    request<Permission>({
      method: 'PUT',
      url: `/api/v1/permissions/${permissionId}`,
      data,
    }),
  remove: (permissionId: number) =>
    request<null>({
      method: 'DELETE',
      url: `/api/v1/permissions/${permissionId}`,
    }),
}

export const systemApi = {
  health: () => requestRaw<HealthStatus>({ method: 'GET', url: '/health' }),
}
