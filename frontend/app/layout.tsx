import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Article Generator',
  description: 'AI-powered article generation with web search',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
