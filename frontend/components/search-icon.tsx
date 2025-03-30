"use client"

import { useState, useEffect, useRef } from 'react'
import { useRouter, usePathname, useSearchParams } from 'next/navigation'
import { useDebounce } from '@/hooks/useDebounce'

export default function SearchIcon() {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [inputValue, setInputValue] = useState('')
  const router = useRouter()
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const inputRef = useRef<HTMLInputElement>(null)
  const isInitialMount = useRef(true)
  
  // Get the current search term from URL
  const searchTerm = searchParams ? searchParams.get('q') || '' : ''
  
  // Debounce the input value
  const debouncedSearchTerm = useDebounce(inputValue, 400)
  
  // Check if search is active
  const hasSearchQuery = searchTerm.length > 0
  
  // Detect if we're on mobile and set expanded state accordingly
  useEffect(() => {
    const checkIsMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      // Auto-expand on mobile
      if (mobile && !isExpanded) {
        setIsExpanded(true);
      }
    };
    
    // Run on mount
    checkIsMobile();
    
    // Set up listener for window resizes
    window.addEventListener('resize', checkIsMobile);
    
    // Cleanup
    return () => window.removeEventListener('resize', checkIsMobile);
  }, [isExpanded]);
  
  // Only sync from URL to input on initial mount, not on every URL change
  useEffect(() => {
    if (isInitialMount.current) {
      setInputValue(searchTerm)
      isInitialMount.current = false
    }
  }, [searchTerm])
  
  // Focus input when expanded
  useEffect(() => {
    if (isExpanded && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isExpanded])
  
  // Update URL with search term when debounced value changes
  useEffect(() => {
    // Only update URL if component has mounted and value is different from current URL
    if (!isInitialMount.current && debouncedSearchTerm !== searchTerm) {
      if (!searchParams) return;
      
      const params = new URLSearchParams(searchParams.toString())
      if (debouncedSearchTerm) {
        params.set('q', debouncedSearchTerm)
      } else {
        params.delete('q')
      }
      
      router.push(`${pathname}?${params.toString()}`)
    }
  }, [debouncedSearchTerm, searchParams, router, pathname, searchTerm])
  
  // Handle input change without immediately updating URL
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value)
  }
  
  // Clear search and close search bar
  const handleClear = () => {
    setInputValue('')
    // Clear search params immediately without waiting for debounce
    if (searchParams) {
      const params = new URLSearchParams(searchParams.toString())
      params.delete('q')
      router.push(`${pathname}?${params.toString()}`)
    }
    // Only close on desktop
    if (!isMobile) {
      setIsExpanded(false)
    }
  }
  
  // Handle key press for immediate search on Enter
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (!searchParams) return;
      
      const params = new URLSearchParams(searchParams.toString())
      if (inputValue) {
        params.set('q', inputValue)
      } else {
        params.delete('q')
      }
      
      router.push(`${pathname}?${params.toString()}`)
    }
  }
  
  // Close search bar when clicking outside (desktop only)
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        !isMobile &&
        inputRef.current && 
        !inputRef.current.contains(event.target as Node) && 
        !(event.target as HTMLElement).closest('.search-icon-button')
      ) {
        if (!hasSearchQuery) {
          setIsExpanded(false)
        }
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [hasSearchQuery, isMobile])
  
  // Desktop version with toggle
  if (!isMobile) {
    return (
      <div className="relative flex items-center">
        {/* Expandable search bar - positioned to the left of the icon */}
        <div 
          className={`absolute right-10 top-0 transform flex items-center transition-all duration-300 ease-in-out bg-white border search-bar-radius shadow-sm ${
            isExpanded ? 'w-56 opacity-100 pointer-events-auto' : 'w-10 opacity-0 pointer-events-none'
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
              onChange={handleInputChange}
              onKeyDown={handleKeyPress}
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
    )
  }
  
  // Mobile version - always expanded, full width
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
          onChange={handleInputChange}
          onKeyDown={handleKeyPress}
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
  )
} 