import type { PaperSummary } from "@/lib/types"
import PaperCard, { PaperCardProvider } from "./paper-card"

interface PaperGridProps {
  papers: PaperSummary[]
}

export default function PaperGrid({ papers }: PaperGridProps) {
  return (
    <PaperCardProvider>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {papers.map((paper) => (
          <PaperCard key={paper.uid} paper={paper} />
        ))}
      </div>
    </PaperCardProvider>
  )
}

