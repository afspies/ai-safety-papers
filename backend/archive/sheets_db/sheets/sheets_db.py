import os
import sys
import logging
from datetime import datetime, timedelta
import gspread
from typing import List, Dict, Any, Optional
import json
import time

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

# Import needed for models but handle circular imports
from pathlib import Path

class SheetsDB:
    HEADER_ROW = [
        "Title", "Submitted Date", "TLDR", "URL", "Authors",
        "Abstract", "Venue", "Highlight", "Include on Website", "Post to Bots", "Posted Date",
        "Year", "Paper ID", "AI Safety Relevance", "Mech Int Relevance",
        "Embedding Model", "Embedding Vector"
    ]
    # Define the mapping of columns to their indices
    COLUMN_MAP = {k.lower().replace(' ','_'): i for i,k in enumerate(HEADER_ROW)}
    
    # Cache settings
    CACHE_DURATION = 300  # Cache data for 5 minutes

    def __init__(self, spreadsheet_id: str = None, range_name: str = None, credentials_file: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize cache
        self._cache = {}
        self._last_refresh = {}
        
        # If no parameters are provided, attempt to load from config
        if not all([spreadsheet_id, range_name, credentials_file]):
            from backend.src.utils.config_loader import load_config
            config = load_config()
            spreadsheet_id = config['google_sheets']['spreadsheet_id']
            range_name = config['google_sheets']['range_name']
            credentials_file = config['google_sheets']['credentials_file']
        
        self.credentials_file = os.path.abspath(os.path.join(project_root, 'secrets', credentials_file))
        
        # Initialize gspread client
        self.gc = gspread.service_account(filename=self.credentials_file)
        self.spreadsheet = self.gc.open_by_key(spreadsheet_id)
        self.worksheet = self.spreadsheet.sheet1  # Get first worksheet
        
        self.ensure_header_row()
        
        # Only run these cleanup operations for non-API contexts
        # to improve API response time
        if os.environ.get('API_MODE') != 'true':
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
            new_row[self.COLUMN_MAP['highlight']] = 'FALSE'
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
                        'embedding_vector': json.loads(row['Embedding Vector']) if row['Embedding Vector'] else [],
                        'highlight': row.get('Highlight') == 'TRUE'
                    }
            # Also include papers that are already posted but need to be highlighted
            elif row.get('Posted Date') and row.get('Highlight') == 'TRUE' and row.get('Include on Website') == 'TRUE':
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
                        'tldr': {'text': row['TLDR']} if row['TLDR'] else None,
                        'embedding_model': row['Embedding Model'],
                        'embedding_vector': json.loads(row['Embedding Vector']) if row['Embedding Vector'] else [],
                        'highlight': True
                    }
        
        return list(papers_to_post.values())
        
    def get_papers(self) -> List:
        """Get all website-enabled papers for API use.
        
        Returns:
            List of Article objects representing all papers marked for website inclusion
        """
        # Check if we have a valid cache
        cache_key = 'all_papers'
        current_time = time.time()
        
        if (cache_key in self._cache and 
            cache_key in self._last_refresh and 
            current_time - self._last_refresh[cache_key] < self.CACHE_DURATION):
            cache_age = current_time - self._last_refresh[cache_key]
            self.logger.info(f"Cache HIT for 'all_papers' (age: {cache_age:.1f}s)")
            return self._cache[cache_key]
            
        self.logger.info("Cache MISS for 'all_papers', fetching from Google Sheets")
        
        try:
            from backend.src.models.article import Article
            from backend.src.utils.config_loader import load_config
            
            config = load_config()
            website_content_path = Path(config.get('website', {}).get('content_path', '../ai-safety-site/content/en'))
            data_dir = Path(config.get('data_dir', 'data'))
            
            # Measure time for fetching sheets data
            start_time = time.time()
            all_values = self.worksheet.get_all_records()
            sheets_fetch_time = time.time() - start_time
            self.logger.info(f"Fetched sheets data in {sheets_fetch_time:.2f}s")
            
            papers = []
            
            for row in all_values:
                if row.get('Include on Website') == 'TRUE':
                    try:
                        article = Article(
                            uid=row['Paper ID'],
                            title=row['Title'],
                            url=row['URL'],
                            authors=row['Authors'].split(', ') if row['Authors'] else [],
                            abstract=row['Abstract'],
                            venue=row['Venue'],
                            submitted_date=datetime.strptime(row['Submitted Date'], "%d/%m/%Y").date() if row['Submitted Date'] else None
                        )
                        
                        # Set TLDR
                        if row['TLDR']:
                            article.set_tldr(row['TLDR'])
                        
                        # Set highlight status
                        article.set_highlight(row.get('Highlight') == 'TRUE')
                        
                        # Set website content path
                        article.website_content_path = website_content_path
                        
                        # Set data folder
                        data_path = data_dir / article.uid
                        article.data_folder = data_path
                        
                        papers.append(article)
                    except Exception as row_e:
                        self.logger.error(f"Error processing row for paper {row.get('Paper ID', 'unknown')}: {row_e}")
                        continue
            
            # Update cache
            self._cache[cache_key] = papers
            self._last_refresh[cache_key] = current_time
            
            total_time = time.time() - start_time
            self.logger.info(f"Successfully loaded {len(papers)} papers from sheets in {total_time:.2f}s")
            return papers
        except Exception as e:
            self.logger.error(f"Error getting papers: {e}")
            self.logger.exception("Full traceback:")
            return []
        
    def get_highlighted_papers(self) -> List[Dict[str, Any]]:
        """Get papers that are marked as highlights."""
        # Check if we have a valid cache
        cache_key = 'highlighted_papers'
        current_time = time.time()
        
        if (cache_key in self._cache and 
            cache_key in self._last_refresh and 
            current_time - self._last_refresh[cache_key] < self.CACHE_DURATION):
            cache_age = current_time - self._last_refresh[cache_key]
            self.logger.info(f"Cache HIT for 'highlighted_papers' (age: {cache_age:.1f}s)")
            return self._cache[cache_key]
            
        self.logger.info("Cache MISS for 'highlighted_papers', checking if we can use all_papers cache")
        
        try:
            # Reuse papers from get_papers if available to avoid another API call
            if 'all_papers' in self._cache and current_time - self._last_refresh.get('all_papers', 0) < self.CACHE_DURATION:
                self.logger.debug("Using cached papers to filter for highlighted papers")
                highlighted_papers = [p for p in self._cache['all_papers'] if p.highlight]
                
                # Update cache
                self._cache[cache_key] = highlighted_papers
                self._last_refresh[cache_key] = current_time
                
                return highlighted_papers
            
            # Otherwise fetch from sheets directly
            start_time = time.time()
            all_values = self.worksheet.get_all_records()
            sheets_fetch_time = time.time() - start_time
            self.logger.info(f"Fetched sheets data in {sheets_fetch_time:.2f}s")
            
            highlighted_papers = {}
            
            for row in all_values:
                if row.get('Highlight') == 'TRUE' and row.get('Include on Website') == 'TRUE':
                    paper_id = row['Paper ID']
                    if paper_id not in highlighted_papers:
                        highlighted_papers[paper_id] = self._record_to_paper(row)
            
            result = list(highlighted_papers.values())
            
            # Update cache
            self._cache[cache_key] = result
            self._last_refresh[cache_key] = current_time
            
            total_time = time.time() - start_time
            self.logger.info(f"Successfully loaded {len(result)} highlighted papers in {total_time:.2f}s")
            
            return result
        except Exception as e:
            self.logger.error(f"Error getting highlighted papers: {e}")
            self.logger.exception("Full traceback:")
            return []

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
                'submitted_date': datetime.strptime(record['Submitted Date'], "%d/%m/%Y").date() if record['Submitted Date'] else None,
                'highlight': record.get('Highlight') == 'TRUE'
            }
        except Exception as e:
            self.logger.error(f"Error converting record to paper: {e}")
            return None

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """Get a specific paper by its ID."""
        # Check if we have the paper in the all_papers cache
        cache_key = 'all_papers'
        current_time = time.time()
        
        # Try to reuse all_papers cache if available
        if (cache_key in self._cache and 
            cache_key in self._last_refresh and 
            current_time - self._last_refresh[cache_key] < self.CACHE_DURATION):
                
            self.logger.info(f"Checking for paper {paper_id} in cache")
            
            for paper in self._cache[cache_key]:
                if getattr(paper, 'uid', None) == paper_id:
                    self.logger.info(f"Cache HIT for paper {paper_id}")
                    return paper
                    
            self.logger.info(f"Paper {paper_id} not found in cache, querying sheets directly")
                    
        # If not in cache or cache expired, fetch directly
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
