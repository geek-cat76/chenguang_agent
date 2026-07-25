export interface ApiEnvelope<T> {
  code: number | string
  message: string
  data: T | null
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface PageParams {
  page: number
  page_size: number
  keyword?: string
}

export interface Captcha {
  key: string
  image: string
}

export interface LoginPayload {
  username: string
  password: string
  captcha_key: string
  captcha_code: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
}

export interface UserWithRoles extends User {
  roles: Role[]
}

export interface UserCreatePayload {
  username: string
  email: string
  password: string
}

export interface Permission {
  id: number
  code: string
  name: string
  description: string | null
}

export interface PermissionCreatePayload {
  code: string
  name: string
  description?: string | null
}

export interface PermissionUpdatePayload {
  name?: string | null
  description?: string | null
}

export interface Role {
  id: number
  code: string
  name: string
  description: string | null
  permissions: Permission[]
}

export interface RoleCreatePayload {
  code: string
  name: string
  description?: string | null
}

export interface RoleUpdatePayload {
  name?: string | null
  description?: string | null
}

export interface HealthStatus {
  status: string
}

export interface ValidationIssue {
  loc: Array<string | number>
  msg: string
  type: string
}
