interface BrandMarkProps {
  compact?: boolean
  light?: boolean
}

export function BrandMark({ compact = false, light = false }: BrandMarkProps) {
  return (
    <div className={`brand-mark${compact ? ' brand-mark--compact' : ''}`}>
      <span className="brand-mark__icon" aria-hidden="true">
        <span className="brand-mark__sun" />
        <span className="brand-mark__ray brand-mark__ray--left" />
        <span className="brand-mark__ray brand-mark__ray--right" />
      </span>
      {!compact && (
        <span className={`brand-mark__text${light ? ' brand-mark__text--light' : ''}`}>
          <strong>晨光</strong>
          <small>AGENT PLATFORM</small>
        </span>
      )}
    </div>
  )
}
