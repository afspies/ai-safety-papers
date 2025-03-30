import { Metadata } from "next"

export const metadata: Metadata = {
  title: "About - AI Safety Papers",
  description: "Learn more about AI Safety Papers",
}

export default function AboutLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
} 