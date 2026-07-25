import { Button, Result } from 'antd'
import { useNavigate } from 'react-router-dom'

export function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div className="screen-result">
      <Result
        status="404"
        title="页面没有找到"
        subTitle="你访问的地址不存在，或页面已经移动。"
        extra={
          <Button type="primary" onClick={() => navigate('/dashboard')}>
            返回工作台
          </Button>
        }
      />
    </div>
  )
}
