import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Format author names for display (first initial + last name)
// Returns "A.Smith, B.Jones, et al." format
export function formatAuthors(authors: string[]): string {
  if (!authors || authors.length === 0) return "Unknown Author";
  
  // Format each author name (first initial + last name)
  const formattedAuthors = authors.map(author => {
    const nameParts = author.split(' ');
    if (nameParts.length === 1) return author;
    
    // Get last name
    const lastName = nameParts[nameParts.length - 1];
    
    // Format initials for first and middle names
    const initials = nameParts.slice(0, -1).map(name => `${name.charAt(0)}.`).join('');
    
    // Add a thin space (\u2009) between initials and last name
    return `${initials}\u2009${lastName}`;
  });
  
  // Limit to first 2 authors + "et al." if more
  if (formattedAuthors.length > 2) {
    return `${formattedAuthors[0]}, ${formattedAuthors[1]}, et al.`;
  }
  
  return formattedAuthors.join(', ');
}

// Helper function to format date
export function formatDateFriendly(date: Date | string | undefined, compact: boolean = false): string {
  if (!date) return "";
  
  try {
    // Handle ISO string format
    const dateObj = typeof date === "string" ? new Date(date) : date;
    if (isNaN(dateObj.getTime())) return "";
    
    if (compact) {
      // Shorter format for the card bubble (e.g., "Jan 2024")
      return dateObj.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short'
      });
    }
    
    // Full format for other uses
    return dateObj.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch (e) {
    console.error("Error formatting date:", e, date);
    return "";
  }
}

// Helper function to add ordinal suffix
export function addOrdinalSuffix(day: number): string {
  if (day > 3 && day < 21) return `${day}th`;
  switch (day % 10) {
    case 1: return `${day}st`;
    case 2: return `${day}nd`;
    case 3: return `${day}rd`;
    default: return `${day}th`;
  }
}
