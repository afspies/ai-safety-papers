"use client";

import { cn } from "@/lib/utils";
import { GridIcon, List } from "lucide-react";
import { useEffect, useState } from "react";

interface ViewToggleProps {
  onChange: (view: "grid" | "list") => void;
  view: "grid" | "list";
}

export default function ViewToggle({ onChange, view }: ViewToggleProps) {
  const [mounted, setMounted] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    setMounted(true);
    
    // Check if device is mobile
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768); // Standard mobile breakpoint
    };
    
    // Initial check
    checkIfMobile();
    
    // Add resize listener
    window.addEventListener("resize", checkIfMobile);
    
    // Cleanup
    return () => {
      window.removeEventListener("resize", checkIfMobile);
    };
  }, []);

  // Debug current view
  useEffect(() => {
    console.log("Current view in ViewToggle:", view);
  }, [view]);

  // Handler functions with explicit debugging
  const handleGridClick = () => {
    console.log("Grid button clicked");
    onChange("grid");
  };

  const handleListClick = () => {
    console.log("List button clicked");
    onChange("list");
  };

  // Don't render on server or on mobile devices
  if (!mounted || isMobile) {
    return null;
  }

  return (
    <div className="flex items-center rounded-lg border border-gray-200 p-1">
      <button
        onClick={handleGridClick}
        className={cn(
          "p-1.5 rounded-md transition-colors",
          view === "grid"
            ? "bg-blue-50 text-blue-600 border-blue-200 border"
            : "text-gray-600 hover:text-gray-800 hover:bg-gray-50"
        )}
        aria-label="Grid view"
        title="Grid view"
      >
        <GridIcon size={20} />
      </button>
      <button
        onClick={handleListClick}
        className={cn(
          "p-1.5 rounded-md transition-colors",
          view === "list"
            ? "bg-blue-50 text-blue-600 border-blue-200 border"
            : "text-gray-600 hover:text-gray-800 hover:bg-gray-50"
        )}
        aria-label="List view"
        title="List view"
      >
        <List size={20} />
      </button>
    </div>
  );
} 