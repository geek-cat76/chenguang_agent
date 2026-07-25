import {
  ArrowRightOutlined,
  LockOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { App, Button, Form, Input, Spin } from 'antd'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { BrandMark } from '../components/BrandMark'
import { authApi } from '../services/api'
import { getErrorMessage } from '../services/http'

interface LoginFormValues {
  username: string
  password: string
  captcha_code: string
}

interface LocationState {
  from?: string
}

export function LoginPage() {
  const [form] = Form.useForm<LoginFormValues>()
  const { message } = App.useApp()
  const navigate = useNavigate()
  const location = useLocation()
  const { token, user, loginWithToken } = useAuth()

  const captchaQuery = useQuery({
    queryKey: ['auth', 'captcha'],
    queryFn: authApi.getCaptcha,
    staleTime: 0,
    refetchOnWindowFocus: false,
  })

  useEffect(() => {
    if (token && user) {
      navigate('/dashboard', { replace: true })
    }
  }, [token, user, navigate])

  const refreshCaptcha = async () => {
    form.setFieldValue('captcha_code', '')
    await captchaQuery.refetch()
  }

  const loginMutation = useMutation({
    mutationFn: async (values: LoginFormValues) => {
      const captcha = captchaQuery.data
      if (!captcha) {
        throw new Error('验证码尚未加载，请刷新后重试')
      }

      const result = await authApi.login({
        ...values,
        captcha_key: captcha.key,
      })
      await loginWithToken(result.access_token)
    },
    onSuccess: () => {
      message.success('登录成功，欢迎回来')
      const state = location.state as LocationState | null
      navigate(state?.from || '/dashboard', { replace: true })
    },
    onError: async (error) => {
      message.error(getErrorMessage(error))
      // 后端会在登录校验时消费验证码，失败后也必须获取新验证码。
      await refreshCaptcha()
    },
  })

  return (
    <main className="login-page">
      <section className="login-story">
        <div className="login-story__orb login-story__orb--one" />
        <div className="login-story__orb login-story__orb--two" />
        <div className="login-story__brand">
          <BrandMark light />
        </div>
        <div className="login-story__copy">
          <span className="login-story__eyebrow">MANAGEMENT CONSOLE</span>
          <h1>
            让每一束晨光，
            <br />
            照亮高效协作。
          </h1>
          <p>
            统一管理平台账户、角色与访问权限，为后续 Agent 能力构建清晰、安全的基础。
          </p>
          <div className="login-story__features">
            <span>
              <SafetyCertificateOutlined /> 权限边界清晰
            </span>
            <span>
              <LockOutlined /> 数据访问可控
            </span>
          </div>
        </div>
        <div className="login-story__sunrise" aria-hidden="true">
          <span />
        </div>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div className="login-card__mobile-brand">
            <BrandMark />
          </div>
          <span className="login-card__eyebrow">WELCOME BACK</span>
          <h2>登录晨光</h2>
          <p className="login-card__intro">使用你的平台账户进入管理控制台</p>

          <Form<LoginFormValues>
            form={form}
            layout="vertical"
            size="large"
            requiredMark={false}
            onFinish={(values) => loginMutation.mutate(values)}
          >
            <Form.Item
              label="用户名"
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="请输入用户名"
                autoComplete="username"
              />
            </Form.Item>
            <Form.Item
              label="密码"
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="请输入密码"
                autoComplete="current-password"
              />
            </Form.Item>
            <Form.Item label="验证码" required>
              <div className="captcha-field">
                <Form.Item
                  name="captcha_code"
                  noStyle
                  rules={[{ required: true, message: '请输入验证码' }]}
                >
                  <Input
                    placeholder="验证码"
                    maxLength={8}
                    autoComplete="off"
                  />
                </Form.Item>
                <button
                  type="button"
                  className="captcha-image"
                  aria-label="刷新验证码"
                  title="点击刷新验证码"
                  onClick={() => void refreshCaptcha()}
                >
                  {captchaQuery.isFetching ? (
                    <Spin size="small" />
                  ) : captchaQuery.data ? (
                    <img src={captchaQuery.data.image} alt="图形验证码" />
                  ) : (
                    <ReloadOutlined />
                  )}
                </button>
                <Button
                  type="text"
                  icon={<ReloadOutlined />}
                  aria-label="刷新验证码"
                  onClick={() => void refreshCaptcha()}
                />
              </div>
            </Form.Item>
            {captchaQuery.isError && (
              <p className="login-card__error">
                {getErrorMessage(captchaQuery.error)}，请点击刷新。
              </p>
            )}
            <Button
              type="primary"
              htmlType="submit"
              loading={loginMutation.isPending}
              block
              className="login-card__submit"
            >
              进入平台 <ArrowRightOutlined />
            </Button>
          </Form>

          <footer>
            登录即代表你同意遵守平台安全规范
            <span>晨光 Agent 平台 · v0.1</span>
          </footer>
        </div>
      </section>
    </main>
  )
}
