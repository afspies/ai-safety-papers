"use client";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

export default function SearchDesktop() {
  const [inputValue, setInputValue] = useState("");
  const [isExpanded, setIsExpanded] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (isExpanded) {
      inputRef.current?.focus();
    }
  }, [isExpanded]);

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    router.replace(`/?q=${e.target.value}`, { scroll: false });
  };

  const handleClear = () => {
    setInputValue("");
    router.replace("/", { scroll: false });
  };

  return (
    <div className="relative flex items-center">
      {/* Expandable search bar - positioned to the left of the icon */}
      <div
        className={`absolute right-10 top-0 transform flex items-center transition-all duration-300 ease-in-out bg-white border search-bar-radius shadow-sm ${
          isExpanded
            ? "w-56 opacity-100 pointer-events-auto"
            : "w-10 opacity-0 pointer-events-none"
        }`}
      >
        <div className="pl-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-gray-400"
          >
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
        </div>

        <div className="relative flex-1">
          <input
            ref={inputRef}
            type="text"
            placeholder="Search papers..."
            value={inputValue}
            onChange={onChange}
            className="w-full p-2 pr-8 focus:outline-none search-input-radius"
          />

          {inputValue && (
            <button
              onClick={handleClear}
              className="absolute right-1 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700 focus:outline-none"
              aria-label="Clear search"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Search icon button - always visible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="search-icon-button p-2 text-gray-600 hover:text-gray-900 focus:outline-none z-10 button-radius"
        aria-label={isExpanded ? "Close search" : "Search papers"}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </button>
    </div>
  );
}

export function SearchMobile() {
  const [inputValue, setInputValue] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    router.replace(`/?q=${e.target.value}`, { scroll: false });
  };

  const handleClear = () => {
    setInputValue("");
    router.replace("/", { scroll: false });
  };

  return (
    <div className="w-full flex items-center bg-white border search-bar-radius shadow-sm">
      <div className="pl-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-gray-400"
        >
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
      </div>

      <div className="relative flex-1">
        <input
          ref={inputRef}
          type="text"
          placeholder="Search papers..."
          value={inputValue}
          onChange={onChange}
          className="w-full p-2 pr-8 focus:outline-none search-input-radius"
        />

        {inputValue && (
          <button
            onClick={handleClear}
            className="absolute right-1 top-1/2 -translate-y-1/2 p-1 text-gray-500 hover:text-gray-700 focus:outline-none"
            aria-label="Clear search"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
