# Search Feature Implementation

## Overview
Add a search functionality to the papers listing page with an expandable search bar activated by clicking a search icon placed next to the filter button.

## UI Components

1. **SearchIcon Component**
   - Add a search icon button next to the filter button
   - Handle click to expand/collapse the search bar
   - Implement smooth transition/animation for good UX

2. **SearchBar Component**
   - Create an expandable input field
   - Add placeholder text (e.g., "Search papers...")
   - Implement autofocus when expanded
   - Include clear button to reset search

## Search Logic

1. **Client-side Filtering**
   - Filter papers based on search query against titles and abstracts
   - Implement case-insensitive matching
   - Consider fuzzy search for better results
   - Debounce input to prevent excessive re-renders

2. **Search State Management**
   - Store search term in URL query parameters (for shareable links)
   - Synchronize UI with URL state
   - Preserve search state during navigation

## Implementation Steps

1. **Create Search Components**
   ```jsx
   // components/SearchBar.jsx
   import { useState, useEffect, useRef } from 'react'
   import { useRouter, usePathname, useSearchParams } from 'next/navigation'
   
   export default function SearchBar({ isExpanded, setIsExpanded }) {
     const router = useRouter()
     const pathname = usePathname()
     const searchParams = useSearchParams()
     const inputRef = useRef(null)
     
     // Get the current search term from URL
     const searchTerm = searchParams.get('q') || ''
     
     // Focus input when expanded
     useEffect(() => {
       if (isExpanded && inputRef.current) {
         inputRef.current.focus()
       }
     }, [isExpanded])
     
     // Update URL with search term
     const handleSearch = (term) => {
       const params = new URLSearchParams(searchParams)
       if (term) {
         params.set('q', term)
       } else {
         params.delete('q')
       }
       
       router.push(`${pathname}?${params.toString()}`)
     }
     
     return (
       <div className={`search-container ${isExpanded ? 'expanded' : 'collapsed'}`}>
         <input
           ref={inputRef}
           type="text"
           placeholder="Search papers..."
           value={searchTerm}
           onChange={(e) => handleSearch(e.target.value)}
           className="search-input"
         />
         {searchTerm && (
           <button 
             onClick={() => handleSearch('')}
             className="clear-button"
           >
             Clear
           </button>
         )}
       </div>
     )
   }
   ```

2. **Create Search Icon Component**
   ```jsx
   // components/SearchIcon.jsx
   import { useState } from 'react'
   import SearchBar from './SearchBar'
   
   export default function SearchIcon() {
     const [isExpanded, setIsExpanded] = useState(false)
     
     return (
       <div className="search-icon-container">
         <button 
           onClick={() => setIsExpanded(!isExpanded)}
           className="search-icon-button"
           aria-label="Search papers"
         >
           <SearchIconSVG />
         </button>
         <SearchBar 
           isExpanded={isExpanded} 
           setIsExpanded={setIsExpanded} 
         />
       </div>
     )
   }
   
   function SearchIconSVG() {
     return (
       <svg 
         xmlns="http://www.w3.org/2000/svg" 
         width="24" 
         height="24" 
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
     )
   }
   ```

3. **Add CSS for Animation**
   ```css
   /* styles/search.css */
   .search-icon-container {
     display: flex;
     align-items: center;
     position: relative;
   }
   
   .search-icon-button {
     background: none;
     border: none;
     cursor: pointer;
     padding: 8px;
     color: #333;
     z-index: 2;
   }
   
   .search-container {
     display: flex;
     align-items: center;
     overflow: hidden;
     transition: width 0.3s ease;
   }
   
   .search-container.collapsed {
     width: 0;
   }
   
   .search-container.expanded {
     width: 300px;
   }
   
   .search-input {
     width: 100%;
     padding: 8px 12px;
     border: 1px solid #ddd;
     border-radius: 4px;
     outline: none;
   }
   
   .clear-button {
     background: none;
     border: none;
     cursor: pointer;
     margin-left: -30px;
     color: #999;
   }
   ```

4. **Implement Paper Filtering Logic**
   ```jsx
   // utils/search.js
   
   /**
    * Filter papers based on search query
    * @param {Array} papers - Array of paper objects
    * @param {String} query - Search query
    * @returns {Array} - Filtered papers
    */
   export function filterPapers(papers, query) {
     if (!query || query.trim() === '') {
       return papers;
     }
     
     const normalizedQuery = query.toLowerCase().trim();
     
     return papers.filter(paper => {
       const title = paper.title?.toLowerCase() || '';
       const abstract = paper.abstract?.toLowerCase() || '';
       const summary = paper.summary?.toLowerCase() || '';
       const tldr = paper.tldr?.toLowerCase() || '';
       
       return (
         title.includes(normalizedQuery) ||
         abstract.includes(normalizedQuery) ||
         summary.includes(normalizedQuery) ||
         tldr.includes(normalizedQuery)
       );
     });
   }
   ```

5. **Update Main Page Component**
   ```jsx
   // pages/index.jsx or app/page.jsx
   'use client'; // if using app directory
   
   import { useSearchParams } from 'next/navigation';
   import { useState, useEffect } from 'react';
   import SearchIcon from '../components/SearchIcon';
   import { filterPapers } from '../utils/search';
   
   export default function HomePage() {
     const [papers, setPapers] = useState([]);
     const [isLoading, setIsLoading] = useState(true);
     const searchParams = useSearchParams();
     const searchQuery = searchParams.get('q') || '';
     
     useEffect(() => {
       // Fetch papers from API
       async function fetchPapers() {
         setIsLoading(true);
         try {
           const response = await fetch('/api/papers');
           const data = await response.json();
           setPapers(data);
         } catch (error) {
           console.error('Error fetching papers:', error);
         } finally {
           setIsLoading(false);
         }
       }
       
       fetchPapers();
     }, []);
     
     // Filter papers based on search query
     const filteredPapers = filterPapers(papers, searchQuery);
     
     return (
       <div className="container">
         <div className="header">
           <h1>AI Safety Papers</h1>
           <div className="toolbar">
             <SearchIcon />
             <FilterButton /> {/* Your existing filter button */}
           </div>
         </div>
         
         {isLoading ? (
           <div>Loading papers...</div>
         ) : (
           <>
             {searchQuery && (
               <p className="search-results">
                 Found {filteredPapers.length} results for "{searchQuery}"
               </p>
             )}
             
             <div className="papers-grid">
               {filteredPapers.map(paper => (
                 <PaperCard key={paper.id} paper={paper} />
               ))}
             </div>
             
             {filteredPapers.length === 0 && (
               <div className="no-results">
                 No papers found for "{searchQuery}"
               </div>
             )}
           </>
         )}
       </div>
     );
   }
   ```

## Future Considerations

1. **Server-side Search**
   - For larger datasets, implement server-side search
   - Create API endpoint with search parameter
   - Update fetch logic to include search term

2. **Pagination**
   - Implement pagination for better performance with large datasets
   - Maintain search context when navigating between pages
   - Consider infinite scrolling as an alternative

3. **Advanced Search Features**
   - Add filters for publication date, authors, tags
   - Implement advanced query syntax (AND, OR, quotes for exact match)
   - Add sorting options (relevance, date, etc.)

4. **Search Analytics**
   - Track popular search terms
   - Improve search based on user behavior

## Accessibility Considerations

1. Ensure proper ARIA labels for search components
2. Make sure keyboard navigation works correctly
3. Provide visual feedback for search state
4. Ensure sufficient color contrast for all elements 