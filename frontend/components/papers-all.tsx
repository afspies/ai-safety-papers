"use client";

import PaperGrid from "@/components/paper-grid";
import { filterPapersByQuery } from "@/lib/search";
import { PaperSummary } from "@/lib/types";
import { useSearchParams } from "next/navigation";
import { useMemo } from "react";

interface AllPapersProps {
  papers: PaperSummary[];
}

export function AllPapers({ papers: allPapers }: AllPapersProps) {
  const searchParams = useSearchParams();
  const sortedPapers = useMemo(() => {
    // Sort papers by date (newest first)
    return [...allPapers].sort((a, b) => {
      if (!a.submitted_date) return 1; // Papers without dates go to the end
      if (!b.submitted_date) return -1;

      const dateA = new Date(a.submitted_date);
      const dateB = new Date(b.submitted_date);

      return dateB.getTime() - dateA.getTime(); // Descending order (newest first)
    });
  }, [allPapers]);

  // Get search query from URL params - await the searchParams object
  const highlight = searchParams?.get("highlight");
  const searchQuery = searchParams?.get("q") || "";
  const showOnlyHighlighted = highlight === "true";

  const filteredPapers = useMemo(() => {
    const papers = showOnlyHighlighted
      ? sortedPapers.filter((paper) => paper.highlight)
      : sortedPapers;

    if (searchQuery) {
      return filterPapersByQuery(papers, searchQuery);
    }

    return papers;
  }, [sortedPapers, searchQuery, showOnlyHighlighted]);

  const searchInfo = searchQuery ? (
    <div className="mb-6 text-gray-600">
      Found {filteredPapers.length} paper
      {filteredPapers.length !== 1 ? "s" : ""}
      for "<span className="font-medium">{searchQuery}</span>"
      {showOnlyHighlighted ? " (highlights only)" : ""}
    </div>
  ) : null;

  return (
    <>
      {searchInfo}
      <PaperGrid papers={filteredPapers} />
      {filteredPapers.length === 0 && !searchQuery && (
        <div className="text-center py-12 text-gray-500">
          No papers available.
        </div>
      )}
      {filteredPapers.length === 0 && searchQuery && (
        <div className="text-center py-12 text-gray-500">
          No matching papers found. Try a different search term.
        </div>
      )}
    </>
  );
}
