import axios, { AxiosError, type AxiosRequestConfig } from 'axios'
import type { ApiEnvelope, ValidationIssue } from '../types/api'
import { tokenStorage } from './token'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || ''

export class ApiError extends Error {
  readonly code?: number | string
  readonly status?: number
  readonly details?: ValidationIssue[]

  constructor(
    message: string,
    options: {
      code?: number | string
      status?: number
      details?: ValidationIssue[]
    } = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.code = options.code
    this.status = options.status
    this.details = options.details
  }
}

const client = axios.create({
  baseURL: apiBaseUrl,
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const token = tokenStorage.get()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

function publishUnauthorized(): void {
  tokenStorage.clear()
  window.dispatchEvent(new CustomEvent('chenguang:unauthorized'))
}

function isUnauthorized(code: number | string | undefined, status?: number): boolean {
  return status === 401 || String(code) === '401'
}

function getHttpError(error: AxiosError): ApiError {
  const payload = error.response?.data as
    | { detail?: ValidationIssue[] | string; message?: string }
    | undefined
  const details = Array.isArray(payload?.detail) ? payload.detail : undefined
  const detailMessage =
    typeof payload?.detail === 'string'
      ? payload.detail
      : details?.map((item) => item.msg).join('；')
  const message =
    payload?.message ||
    detailMessage ||
    (error.code === 'ECONNABORTED'
      ? '请求超时，请检查后端服务'
      : '无法连接服务，请确认后端已经启动')

  return new ApiError(message, {
    status: error.response?.status,
    details,
  })
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  return '操作失败，请稍后重试'
}

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  try {
    const response = await client.request<ApiEnvelope<T>>(config)
    const envelope = response.data

    if (String(envelope.code) !== '200') {
      if (isUnauthorized(envelope.code, response.status)) {
        publishUnauthorized()
      }
      throw new ApiError(envelope.message || '请求失败', {
        code: envelope.code,
        status: response.status,
      })
    }

    return envelope.data as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (axios.isAxiosError(error)) {
      if (isUnauthorized(undefined, error.response?.status)) {
        publishUnauthorized()
      }
      throw getHttpError(error)
    }
    throw error
  }
}

export async function requestRaw<T>(config: AxiosRequestConfig): Promise<T> {
  try {
    const response = await client.request<T>(config)
    return response.data
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw getHttpError(error)
    }
    throw error
  }
}
