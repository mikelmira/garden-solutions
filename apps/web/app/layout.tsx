import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/lib/auth'
import { Toaster } from "@/components/ui/toaster"

import { IntegrationDebugPanel } from '@/components/debug/IntegrationDebugPanel'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
    title: 'Garden Solutions',
    description: 'Ordering & Fulfilment System',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                <AuthProvider>
                    {children}
                    <IntegrationDebugPanel />
                </AuthProvider>
                <Toaster />
            </body>
        </html>
    )
}
