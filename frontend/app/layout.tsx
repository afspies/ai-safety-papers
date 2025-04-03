import type React from "react"
import type { Metadata } from "next"
import { Merriweather, Source_Serif_4 } from "next/font/google"
import "./globals.css"
import Navbar from "@/components/navbar"
import Footer from "@/components/footer"

// Load Source Serif 4 for headings
const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  variable: "--font-source-serif",
  weight: ["400", "500", "600", "700"],
})

// Load Merriweather for body text
const merriweather = Merriweather({
  subsets: ["latin"],
  variable: "--font-merriweather",
  weight: ["300", "400", "700", "900"],
})

export const metadata: Metadata = {
  title: "AI Safety Papers",
  description: "A curated selection of research papers on AI safety and Alignment",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${sourceSerif.variable} ${merriweather.variable} font-serif h-full bg-white`}>
        <div className="flex flex-col min-h-screen">
          <Navbar />
          <main className="flex-grow bg-white">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  )
}



import './globals.css'