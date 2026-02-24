import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function OGImage() {
  return new ImageResponse(
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: 1200,
        height: 630,
        background: 'linear-gradient(135deg, #0D9488 0%, #0F766E 50%, #134E4A 100%)',
        padding: '80px 96px',
        color: 'white',
        fontFamily: 'Georgia, serif',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 32 }}>
        {/* Icon */}
        <div
          style={{
            background: 'rgba(255,255,255,0.15)',
            borderRadius: 16,
            padding: 16,
            display: 'flex',
            alignItems: 'flex-end',
            gap: 4,
            height: 64,
            width: 64,
          }}
        >
          <div style={{ background: 'white', width: 12, height: 28, borderRadius: 3, opacity: 0.8 }} />
          <div style={{ background: 'white', width: 12, height: 40, borderRadius: 3, opacity: 0.9 }} />
          <div style={{ background: 'white', width: 12, height: 52, borderRadius: 3 }} />
        </div>
        <span style={{ fontSize: 32, fontWeight: 700, letterSpacing: '-0.5px' }}>StartInsight</span>
      </div>
      <div style={{ fontSize: 68, fontWeight: 800, lineHeight: 1.05, marginBottom: 24 }}>
        Discover Your Next<br />Million-Dollar Idea
      </div>
      <div style={{ fontSize: 28, opacity: 0.85, marginBottom: 48 }}>
        AI-powered market intelligence from real startup signals
      </div>
      <div style={{ display: 'flex', gap: 20 }}>
        {['SaaS Automation', 'B2B Analytics', 'No-Code Tools'].map((label) => (
          <div
            key={label}
            style={{
              background: 'rgba(255,255,255,0.12)',
              borderRadius: 12,
              padding: '14px 24px',
              border: '1px solid rgba(255,255,255,0.2)',
              fontSize: 20,
            }}
          >
            📈 {label}
          </div>
        ))}
      </div>
      <div
        style={{
          marginTop: 'auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          opacity: 0.7,
        }}
      >
        <span style={{ fontSize: 20 }}>startinsight.co</span>
        <div
          style={{
            background: '#F59E0B',
            color: '#1C1917',
            borderRadius: 999,
            padding: '8px 20px',
            fontSize: 18,
            fontWeight: 700,
          }}
        >
          Free to Start
        </div>
      </div>
    </div>
  )
}
