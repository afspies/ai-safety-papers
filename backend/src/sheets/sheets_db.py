import os
import sys
import logging
from datetime import datetime, timedelta
import gspread
from typing import List, Dict, Any, Optional
import json

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

class SheetsDB:
    HEADER_ROW = [
        "Title", "Submitted Date", "TLDR", "URL", "Authors",
        "Abstract", "Venue", "Include on Website", "Post to Bots", "Posted Date",
        "Year", "Paper ID", "AI Safety Relevance", "Mech Int Relevance",
        "Embedding Model", "Embedding Vector"
    ]
    # Define the mapping of columns to their indices
    COLUMN_MAP = {k.lower().replace(' ','_'): i for i,k in enumerate(HEADER_ROW)}

    def __init__(self, spreadsheet_id: str, range_name: str, credentials_file: str):
        self.logger = logging.getLogger(__name__)
        self.credentials_file = os.path.abspath(os.path.join(project_root, 'secrets', credentials_file))
        
        # Initialize gspread client
        self.gc = gspread.service_account(filename=self.credentials_file)
        self.spreadsheet = self.gc.open_by_key(spreadsheet_id)
        self.worksheet = self.spreadsheet.sheet1  # Get first worksheet
        
        self.ensure_header_row()
        self.clean_duplicates()
        self.clean_old_papers()

    def ensure_header_row(self):
        """Ensure the header row exists and is correct."""
        first_row = self.worksheet.row_values(1)
        if not first_row or first_row != self.HEADER_ROW:
            self.worksheet.update('A1', [self.HEADER_ROW])
            self.logger.debug("Header row added")

    def add_entry(self, entry: Dict[str, Any]):
        """Add a new entry to the spreadsheet."""
        try:
            paper_id = entry.get('id')
            if not paper_id:
                self.logger.error("Entry missing required 'id' field")
                return

            # Check if entry exists
            existing_cells = self.worksheet.findall(paper_id)
            if existing_cells:
                self.update_existing_entry(entry)
                return

            # Create new row
            new_row = [''] * len(self.HEADER_ROW)
            new_row[self.COLUMN_MAP['title']] = entry.get('title', '')
            new_row[self.COLUMN_MAP['submitted_date']] = entry.get('submitted_date').strftime("%d/%m/%Y") if entry.get('submitted_date') else ''
            new_row[self.COLUMN_MAP['tldr']] = entry.get('tldr', {}).get('text', '')
            new_row[self.COLUMN_MAP['url']] = entry.get('url', '')
            new_row[self.COLUMN_MAP['authors']] = ', '.join(entry.get('authors', []))
            new_row[self.COLUMN_MAP['abstract']] = entry.get('abstract', '')
            new_row[self.COLUMN_MAP['venue']] = entry.get('venue', '')
            new_row[self.COLUMN_MAP['include_on_website']] = 'FALSE'
            new_row[self.COLUMN_MAP['post_to_bots']] = 'FALSE'
            new_row[self.COLUMN_MAP['posted_date']] = ''
            new_row[self.COLUMN_MAP['year']] = str(entry.get('year', ''))
            new_row[self.COLUMN_MAP['paper_id']] = entry['id']
            new_row[self.COLUMN_MAP['ai_safety_relevance']] = '1' if entry.get('query') == "AI Safety" else '0'
            new_row[self.COLUMN_MAP['mech_int_relevance']] = '1' if entry.get('query') == "Mechanistic Interpretability" else '0'
            
            # Handle embedding data
            embedding_data = entry.get('embedding', {})
            new_row[self.COLUMN_MAP['embedding_model']] = embedding_data.get('model', '')
            embedding_vector = embedding_data.get('vector', [])
            new_row[self.COLUMN_MAP['embedding_vector']] = json.dumps(self._round_vector(embedding_vector)) if embedding_vector else '[]'

            # Append the new row
            self.worksheet.append_row(new_row)
            self.logger.debug(f"Added new entry for paper {paper_id}")

        except Exception as e:
            self.logger.error(f"Error adding entry {entry.get('id', 'unknown')}: {e}")
            raise

    def update_existing_entry(self, entry: Dict[str, Any]):
        """Update an existing entry in the spreadsheet."""
        try:
            cell = self.worksheet.find(entry['id'])
            row = cell.row
            
            # Create a list of updates in the format gspread expects
            updates = []
            
            # Update relevance scores
            if entry['query'] == "AI Safety":
                self.worksheet.update_cell(row, self.COLUMN_MAP['ai_safety_relevance'] + 1, '1')
            elif entry['query'] == "Mechanistic Interpretability":
                self.worksheet.update_cell(row, self.COLUMN_MAP['mech_int_relevance'] + 1, '1')
            
            # Update TLDR and embedding if they exist
            if 'tldr' in entry and 'text' in entry['tldr']:
                self.worksheet.update_cell(row, self.COLUMN_MAP['tldr'] + 1, entry['tldr']['text'])
                
            if 'embedding' in entry:
                if 'model' in entry['embedding']:
                    self.worksheet.update_cell(row, self.COLUMN_MAP['embedding_model'] + 1, entry['embedding']['model'])
                if 'vector' in entry['embedding']:
                    self.worksheet.update_cell(row, self.COLUMN_MAP['embedding_vector'] + 1, 
                                            json.dumps(self._round_vector(entry['embedding']['vector'])))

        except gspread.exceptions.WorksheetNotFound:
            self.logger.warning(f"Could not find paper {entry['id']} for update")

    def _round_vector(self, vector, decimal_places=4):
        """Round vector values to specified decimal places."""
        return [round(v, decimal_places) for v in vector]

    def get_papers_to_post(self) -> List[Dict[str, Any]]:
        """Get papers that need to be posted."""
        all_values = self.worksheet.get_all_records()
        papers_to_post = {}
        
        for row in all_values:
            if (not row['Posted Date'] and 
                (row['Post to Bots'] == 'TRUE' or row['Include on Website'] == 'TRUE')):
                paper_id = row['Paper ID']
                if paper_id not in papers_to_post:
                    papers_to_post[paper_id] = {
                        'id': paper_id,
                        'title': row['Title'],
                        'authors': row['Authors'].split(', '),
                        'year': row['Year'],
                        'abstract': row['Abstract'],
                        'url': row['URL'],
                        'venue': row['Venue'],
                        # Structure TLDR like the Semantic Scholar API response
                        'tldr': {'text': row['TLDR']} if row['TLDR'] else None,
                        'embedding_model': row['Embedding Model'],
                        'embedding_vector': json.loads(row['Embedding Vector']) if row['Embedding Vector'] else []
                    }
        
        return list(papers_to_post.values())

    def mark_as_posted(self, paper_id: str):
        """Mark a paper as posted."""
        try:
            cell = self.worksheet.find(paper_id)
            self.worksheet.update_cell(cell.row, self.COLUMN_MAP['posted_date'] + 1, 
                                    datetime.now().strftime("%d/%m/%Y"))
        except gspread.exceptions.WorksheetNotFound:
            self.logger.warning(f"Could not find paper {paper_id} to mark as posted")

    def clean_old_papers(self):
        """Remove papers older than a year unless they're flagged or posted."""
        all_records = self.worksheet.get_all_records()
        one_year_ago = datetime.now().date() - timedelta(days=365)
        
        rows_to_keep = [self.HEADER_ROW]
        for row in all_records:
            if (row['Include on Website'] == 'TRUE' or 
                row['Post to Bots'] == 'TRUE' or 
                row['Posted Date']):
                rows_to_keep.append(list(row.values()))
                continue
                
            try:
                submitted_date = datetime.strptime(row['Submitted Date'], "%d/%m/%Y").date()
                if submitted_date > one_year_ago:
                    rows_to_keep.append(list(row.values()))
            except (ValueError, TypeError):    
                continue
        
        self.worksheet.clear()
        self.worksheet.update('A1', rows_to_keep)

    def clean_duplicates(self):
        """Remove duplicate entries from the sheet."""
        all_records = self.worksheet.get_all_records()
        seen_ids = set()
        unique_rows = [self.HEADER_ROW]
        
        for row in all_records:
            paper_id = row['Paper ID']
            if paper_id and paper_id not in seen_ids:
                seen_ids.add(paper_id)
                unique_rows.append(list(row.values()))
        
        self.worksheet.clear()
        self.worksheet.update('A1', unique_rows)

    def _record_to_paper(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a spreadsheet record to a paper dictionary."""
        try:
            return {
                'id': record['Paper ID'],
                'title': record['Title'],
                'authors': record['Authors'].split(', ') if record['Authors'] else [],
                'year': record['Year'],
                'abstract': record['Abstract'],
                'url': record['URL'],
                'venue': record['Venue'],
                'tldr': {'text': record['TLDR']} if record['TLDR'] else None,
                'submitted_date': datetime.strptime(record['Submitted Date'], "%d/%m/%Y").date() if record['Submitted Date'] else None
            }
        except Exception as e:
            self.logger.error(f"Error converting record to paper: {e}")
            return None

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """Get a specific paper by its ID."""
        try:
            all_records = self.worksheet.get_all_records()
            for record in all_records:
                if record.get('Paper ID') == paper_id:
                    return self._record_to_paper(record)
            return None
        except Exception as e:
            self.logger.error(f"Error getting paper by ID {paper_id}: {e}")
            return None

    def update_entry(self, entry: Dict[str, Any]):
        """Update an existing entry with new information."""
        try:
            cell = self.worksheet.find(entry['id'])
            if not cell:
                self.logger.warning(f"Could not find paper {entry['id']} to update")
                return
                
            row = cell.row
            
            # Update basic fields
            updates = {
                'Title': entry.get('title', ''),
                'Authors': ', '.join(entry.get('authors', [])),
                'Year': entry.get('year', ''),
                'Abstract': entry.get('abstract', ''),
                'URL': entry.get('url', ''),
                'Venue': entry.get('venue', ''),
                'TLDR': entry.get('tldr', {}).get('text', '') if isinstance(entry.get('tldr'), dict) else entry.get('tldr', ''),
            }
            
            # Update each field
            for col_name, value in updates.items():
                col_index = self.COLUMN_MAP[col_name.lower().replace(' ', '_')] + 1
                self.worksheet.update_cell(row, col_index, value)
                
            self.logger.debug(f"Updated entry for paper {entry['id']}")
            
        except Exception as e:
            self.logger.error(f"Error updating entry {entry.get('id', 'unknown')}: {e}")
