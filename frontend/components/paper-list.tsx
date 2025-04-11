import type { PaperSummary } from "@/lib/types"
import { PaperListCard, PaperCardProvider } from "./paper-list-card"

interface PaperListProps {
  papers: PaperSummary[]
}

export default function PaperList({ papers }: PaperListProps) {
  return (
    <PaperCardProvider>
      <div className="flex flex-col gap-6">
        {papers.map((paper) => (
          <PaperListCard key={paper.uid} paper={paper} />
        ))}
      </div>
    </PaperCardProvider>
  )
} 