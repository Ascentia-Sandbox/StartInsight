import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const size = { width: 180, height: 180 }
export const contentType = 'image/png'

export default function AppleIcon() {
  return new ImageResponse(
    <div
      style={{
        background: '#0D9488',
        width: 180,
        height: 180,
        borderRadius: 36,
        display: 'flex',
        alignItems: 'flex-end',
        padding: 20,
        gap: 8,
      }}
    >
      <div style={{ background: 'white', width: 28, height: 60, borderRadius: 4, opacity: 0.9 }} />
      <div style={{ background: 'white', width: 28, height: 90, borderRadius: 4, opacity: 0.95 }} />
      <div style={{ background: 'white', width: 28, height: 120, borderRadius: 4 }} />
    </div>
  )
}
