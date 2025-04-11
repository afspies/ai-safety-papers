"use client";

import PaperGrid from "@/components/paper-grid";
import PaperList from "@/components/paper-list";
import { filterPapersByQuery } from "@/lib/search";
import { PaperSummary } from "@/lib/types";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

interface AllPapersProps {
  papers: PaperSummary[];
}

export function AllPapers({ papers: allPapers }: AllPapersProps) {
  const searchParams = useSearchParams();
  // State for view mode (grid or list)
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  // Load view preference from localStorage on mount
  useEffect(() => {
    const savedView = localStorage.getItem("paperViewMode");
    if (savedView === "list" || savedView === "grid") {
      setViewMode(savedView);
    }
  }, []);

  // Save view preference to localStorage when changed
  useEffect(() => {
    localStorage.setItem("paperViewMode", viewMode);
  }, [viewMode]);

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

  // Check for view mode in URL params
  useEffect(() => {
    console.log("URL params changed, checking view mode");
    const viewParam = searchParams?.get("view");
    
    if (viewParam === "list") {
      console.log("Setting view mode to list from URL param");
      setViewMode("list");
    } else {
      console.log("Setting view mode to grid (default or from URL param)");
      setViewMode("grid");
    }
  }, [searchParams]);

  return (
    <>
      {searchInfo}
      
      {viewMode === "grid" ? (
        <PaperGrid papers={filteredPapers} />
      ) : (
        <PaperList papers={filteredPapers} />
      )}
      
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
