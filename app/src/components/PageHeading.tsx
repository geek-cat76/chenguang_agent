import type { ReactNode } from 'react'

interface PageHeadingProps {
  eyebrow: string
  title: string
  description: string
  actions?: ReactNode
}

export function PageHeading({
  eyebrow,
  title,
  description,
  actions,
}: PageHeadingProps) {
  return (
    <div className="page-heading">
      <div>
        <span className="page-heading__eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {actions && <div className="page-heading__actions">{actions}</div>}
    </div>
  )
}
