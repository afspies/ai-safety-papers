export interface PaperSummary {
  uid: string
  title: string
  authors: string[]
  abstract: string
  tldr: string
  thumbnail_url: string
  submitted_date?: Date | string
  highlight: boolean
  tags: string[]
}

export interface FigureSchema {
  id?: string
  caption?: string
  url: string
  has_subfigures?: boolean
  subfigures?: any[]
  type?: string
  parent_caption?: string
}

export interface PaperDetail extends PaperSummary {
  summary: string
  url: string
  venue: string
  figures: FigureSchema[]
}

