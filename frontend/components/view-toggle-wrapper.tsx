"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import ViewToggle from "./view-toggle";

export default function ViewToggleWrapper() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Get the current view mode from URL or localStorage
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid"); // Default to grid view
  
  // Initialize view mode from localStorage and URL on mount
  useEffect(() => {
    // First try to get from localStorage
    if (typeof window !== "undefined") {
      const savedView = localStorage.getItem("paperViewMode");
      if (savedView === "list" || savedView === "grid") {
        setViewMode(savedView as "grid" | "list");
      }
    }
    
    // Then check URL params which override localStorage
    const viewParam = searchParams?.get("view");
    if (viewParam === "list") {
      setViewMode("list");
    } else if (viewParam === null || viewParam === "grid") {
      setViewMode("grid");
    }
  }, [searchParams]); // Only run on mount and when searchParams changes
  
  // Update URL when toggle changes
  const handleViewChange = (view: "grid" | "list") => {
    console.log("ViewToggleWrapper handling view change:", view);
    
    // Update local state
    setViewMode(view);
    
    // Save to localStorage
    if (typeof window !== "undefined") {
      localStorage.setItem("paperViewMode", view);
    }
    
    // Create new URL with updated params
    const params = new URLSearchParams(searchParams?.toString() || "");
    
    if (view === "grid") {
      // Remove the parameter for the default view to keep URLs clean
      params.delete("view");
    } else {
      params.set("view", view);
    }
    
    // Update the URL without refreshing the page
    const newUrl = `/?${params.toString()}`;
    console.log("Navigating to:", newUrl);
    router.push(newUrl);
  };
  
  console.log("Rendering ViewToggleWrapper with viewMode:", viewMode);
  
  return <ViewToggle view={viewMode} onChange={handleViewChange} />;
} 