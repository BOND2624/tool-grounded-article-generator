import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Tool-Grounded Article Generator',
  description: 'Generate high-quality articles with AI',
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
