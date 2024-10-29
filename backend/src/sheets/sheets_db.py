import os
import sys
import logging
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any
import json

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

class SheetsDB:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    HEADER_ROW = [
        "Title", "Submitted Date", "TLDR", "URL", "Authors",
        "Abstract", "Venue", "Include on Website", "Post to Bots", "Posted Date",
        "Year", "Paper ID", "AI Safety Relevance", "Mechanistic Interpretability Relevance",
        "Embedding Model", "Embedding Vector"
    ]

    # Define the mapping of columns to their indices
    COLUMN_MAP = {
        'title': 0,
        'submitted_date': 1,
        'tldr': 2,
        'url': 3,
        'authors': 4,
        'abstract': 5,
        'venue': 6,
        'include_on_website': 7,
        'post_to_bots': 8,
        'posted_date': 9,
        'year': 10,
        'paper_id': 11,
        'ai_safety_relevance': 12,
        'mech_int_relevance': 13,
        'embedding_model': 14,
        'embedding_vector': 15
    }

    def __init__(self, spreadsheet_id: str, range_name: str, credentials_file: str):
        self.logger = logging.getLogger(__name__)
        self.spreadsheet_id = spreadsheet_id
        # Update the range to include all columns
        self.range_name = f"{range_name.split('!')[0]}!A:P"
        self.credentials_file = os.path.abspath(os.path.join(project_root, 'secrets', credentials_file))
        self.creds = None
        self.service = None
        self.local_data = []
        self.setup_credentials()
        self.load_data()
        self.ensure_header_row()
        self.clean_old_papers()

    def setup_credentials(self):
        self.logger.debug(f"Setting up credentials from file: {self.credentials_file}")
        self.creds = Credentials.from_service_account_file(self.credentials_file, scopes=self.SCOPES)
        self.service = build('sheets', 'v4', credentials=self.creds)
        self.logger.debug("Credentials set up successfully")

    def load_data(self):
        self.logger.info("Loading data from Google Sheets")
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range=self.range_name).execute()
            self.local_data = result.get('values', [])
            self.logger.debug(f"Loaded {len(self.local_data)} rows from Google Sheets")
        except HttpError as error:
            self.logger.error(f"An error occurred while loading data: {error}")

    def ensure_header_row(self):
        self.logger.info("Ensuring header row exists")
        if not self.local_data or self.local_data[0] != self.HEADER_ROW:
            self.logger.debug("Header row not found, adding it")
            self.local_data.insert(0, self.HEADER_ROW)
            self.update_sheet()
        else:
            self.logger.debug("Header row already exists")

    def _round_vector(self, vector, decimal_places=4):
        return [round(v, decimal_places) for v in vector]

    def _format_date(self, date: datetime) -> str:
        """Format date as dd/mm/yyyy"""
        return date.strftime("%d/%m/%Y") if date else ''

    def add_entry(self, entry: Dict[str, Any]):
        self.logger.info(f"Adding new entry: {entry['id']}")
        if not self.entry_exists(entry['id']):
            new_row = [''] * len(self.HEADER_ROW)  # Initialize with empty strings
            new_row[self.COLUMN_MAP['title']] = entry['title']
            new_row[self.COLUMN_MAP['submitted_date']] = self._format_date(entry['submitted_date']) if entry['submitted_date'] else ''
            new_row[self.COLUMN_MAP['tldr']] = entry.get('tldr', {}).get('text', '')
            new_row[self.COLUMN_MAP['url']] = entry['url']  # Use the open access PDF URL
            new_row[self.COLUMN_MAP['authors']] = ', '.join(entry['authors'])
            new_row[self.COLUMN_MAP['abstract']] = entry['abstract']
            new_row[self.COLUMN_MAP['venue']] = entry['venue']
            new_row[self.COLUMN_MAP['include_on_website']] = 'FALSE'
            new_row[self.COLUMN_MAP['post_to_bots']] = 'FALSE'
            new_row[self.COLUMN_MAP['posted_date']] = ''
            new_row[self.COLUMN_MAP['year']] = str(entry['year'])
            new_row[self.COLUMN_MAP['paper_id']] = entry['id']
            new_row[self.COLUMN_MAP['ai_safety_relevance']] = '1' if entry['query'] == "AI Safety" else '0'
            new_row[self.COLUMN_MAP['mech_int_relevance']] = '1' if entry['query'] == "Mechanistic Interpretability" else '0'
            new_row[self.COLUMN_MAP['embedding_model']] = entry.get('embedding', {}).get('model', '')
            new_row[self.COLUMN_MAP['embedding_vector']] = json.dumps(self._round_vector(entry.get('embedding', {}).get('vector', [])))
            
            self.local_data.append(new_row)
            self.update_sheet()
            self.logger.debug(f"Entry {entry['id']} added successfully")
        else:
            self.logger.debug(f"Entry {entry['id']} already exists, updating relevance scores and new fields")
            self.update_existing_entry(entry)

    def update_existing_entry(self, entry: Dict[str, Any]):
        for row in self.local_data:
            if row[self.COLUMN_MAP['paper_id']] == entry['id']:
                # Update relevance scores
                if entry['query'] == "AI Safety":
                    row[self.COLUMN_MAP['ai_safety_relevance']] = '1'
                elif entry['query'] == "Mechanistic Interpretability":
                    row[self.COLUMN_MAP['mech_int_relevance']] = '1'
                
                # Update TLDR and embedding if they exist
                if 'tldr' in entry and 'text' in entry['tldr']:
                    row[self.COLUMN_MAP['tldr']] = entry['tldr']['text']
                if 'embedding' in entry:
                    if 'model' in entry['embedding']:
                        row[self.COLUMN_MAP['embedding_model']] = entry['embedding']['model']
                    if 'vector' in entry['embedding']:
                        row[self.COLUMN_MAP['embedding_vector']] = json.dumps(self._round_vector(entry['embedding']['vector']))
                
                self.update_sheet()
                break

    def entry_exists(self, identifier: str) -> bool:
        return any(row[self.COLUMN_MAP['paper_id']] == identifier for row in self.local_data)

    def update_property(self, paper_id: str, property_name: str, value: str):
        property_index = self.COLUMN_MAP.get(property_name)

        if property_index is None:
            raise ValueError(f"Invalid property name: {property_name}")

        for row in self.local_data:
            if row[self.COLUMN_MAP['paper_id']] == paper_id:
                row[property_index] = value
                self.update_sheet()
                break

    def get_papers_to_post(self) -> List[Dict[str, Any]]:
        papers_to_post = []
        for row in self.local_data[1:]:  # Skip header row
            if row[self.COLUMN_MAP['post_to_bots']] == 'TRUE' and row[self.COLUMN_MAP['posted_date']] == '':
                papers_to_post.append({
                    'id': row[self.COLUMN_MAP['paper_id']],
                    'title': row[self.COLUMN_MAP['title']],
                    'authors': row[self.COLUMN_MAP['authors']],
                    'year': row[self.COLUMN_MAP['year']],
                    'abstract': row[self.COLUMN_MAP['abstract']],
                    'url': row[self.COLUMN_MAP['url']],
                    'venue': row[self.COLUMN_MAP['venue']],
                    'tldr': row[self.COLUMN_MAP['tldr']],
                    'embedding_model': row[self.COLUMN_MAP['embedding_model']],
                    'embedding_vector': json.loads(row[self.COLUMN_MAP['embedding_vector']]) if row[self.COLUMN_MAP['embedding_vector']] else []
                })
        return papers_to_post

    def mark_as_posted(self, paper_id: str):
        self.update_property(paper_id, 'posted', self._format_date(datetime.now()))

    def get_papers_for_website(self) -> List[Dict[str, Any]]:
        return [
            {
                'id': row[self.COLUMN_MAP['paper_id']],
                'title': row[self.COLUMN_MAP['title']],
                'authors': row[self.COLUMN_MAP['authors']],
                'year': row[self.COLUMN_MAP['year']],
                'abstract': row[self.COLUMN_MAP['abstract']],
                'url': row[self.COLUMN_MAP['url']],
                'venue': row[self.COLUMN_MAP['venue']],
                'tldr': row[self.COLUMN_MAP['tldr']],
                'embedding_model': row[self.COLUMN_MAP['embedding_model']],
                'embedding_vector': json.loads(row[self.COLUMN_MAP['embedding_vector']]) if row[self.COLUMN_MAP['embedding_vector']] else []
            }
            for row in self.local_data[1:] if row[self.COLUMN_MAP['include_on_website']] == 'TRUE'
        ]

    def update_sheet(self):
        self.logger.info("Updating Google Sheet")
        body = {'values': self.local_data}
        try:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id, range=self.range_name,
                valueInputOption='USER_ENTERED', body=body).execute()
            self.logger.debug("Google Sheet updated successfully")
        except HttpError as error:
            self.logger.error(f"An error occurred while updating the sheet: {error}")
            self.logger.error(f"Attempted range: {self.range_name}")
            self.logger.error(f"Number of columns in data: {len(self.local_data[0]) if self.local_data else 0}")

    def get_all_entries(self) -> List[List[str]]:
        return self.local_data

    def clean_old_papers(self):
        self.logger.info("Cleaning old papers")
        one_week_ago = datetime.now().date() - timedelta(days=7)
        self.local_data = [self.HEADER_ROW] + [
            row for row in self.local_data[1:]
            if (row[self.COLUMN_MAP['include_on_website']] == 'TRUE' or row[self.COLUMN_MAP['post_to_bots']] == 'TRUE' or row[self.COLUMN_MAP['posted_date']] != '') or  # Keep if posted or flagged
               (self._parse_date(row[self.COLUMN_MAP['submitted_date']]) > one_week_ago if row[self.COLUMN_MAP['submitted_date']] else False)  # Keep if submitted within last week
        ]
        self.update_sheet()
        self.logger.debug(f"Cleaned sheet, new size: {len(self.local_data)} rows")

    def update_relevance_scores(self, paper_id: str, query: str):
        for row in self.local_data:
            if row[self.COLUMN_MAP['paper_id']] == paper_id:
                if query == "AI Safety":
                    row[self.COLUMN_MAP['ai_safety_relevance']] = '1'  # AI Safety Relevance
                elif query == "Mechanistic Interpretability":
                    row[self.COLUMN_MAP['mech_int_relevance']] = '1'  # Mechanistic Interpretability Relevance
                self.update_sheet()
                break

    def _parse_date(self, date_string: str) -> datetime.date:
        """Parse date string in either 'yyyy-mm-dd' or 'dd/mm/yyyy' format."""
        try:
            return datetime.strptime(date_string, "%d/%m/%Y").date()
        except ValueError:
            try:
                return datetime.strptime(date_string, "%Y-%m-%d").date()
            except ValueError:
                self.logger.error(f"Unable to parse date: {date_string}")
                return None
