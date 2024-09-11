import os
import sys
import logging
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict, Any

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

class SheetsDB:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    HEADER_ROW = [
        "Paper ID", "Title", "Authors", "Year", "Abstract", "URL", "Venue",
        "Include on Website", "Post to Bots", "Posted Date", "Submitted Date"
    ]

    def __init__(self, spreadsheet_id: str, range_name: str, credentials_file: str):
        self.logger = logging.getLogger(__name__)
        self.spreadsheet_id = spreadsheet_id
        self.range_name = range_name
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

    def add_entry(self, entry: Dict[str, Any]):
        self.logger.info(f"Adding new entry: {entry['id']}")
        if not self.entry_exists(entry['id']):
            new_row = [
                entry['id'],
                entry['title'],
                ', '.join(entry['authors']),  # Authors are already a list of strings
                str(entry['year']),
                entry['abstract'],
                entry['url'],
                entry['venue'],
                'FALSE',  # Include on Website
                'FALSE',  # Post to Bots
                '',  # Posted Date
                entry['submitted_date'].isoformat()  # Submitted Date
            ]
            self.local_data.append(new_row)
            self.update_sheet()
            self.logger.debug(f"Entry {entry['id']} added successfully")
        else:
            self.logger.debug(f"Entry {entry['id']} already exists, skipping")

    def entry_exists(self, identifier: str) -> bool:
        return any(row[0] == identifier for row in self.local_data)

    def update_property(self, paper_id: str, property_name: str, value: str):
        property_index = {
            'website': 7,
            'bots': 8,
            'posted': 9
        }.get(property_name)

        if property_index is None:
            raise ValueError(f"Invalid property name: {property_name}")

        for row in self.local_data:
            if row[0] == paper_id:
                row[property_index] = value
                self.update_sheet()
                break

    def get_papers_to_post(self) -> List[Dict[str, str]]:
        papers_to_post = []
        for row in self.local_data:
            if row[8] == 'TRUE' and row[9] == '':  # bots is True and posted is empty
                papers_to_post.append({
                    'id': row[0],
                    'title': row[1],
                    'authors': row[2],
                    'year': row[3],
                    'abstract': row[4],
                    'url': row[5],
                    'venue': row[6]
                })
        return papers_to_post

    def mark_as_posted(self, paper_id: str):
        self.update_property(paper_id, 'posted', datetime.now().isoformat())

    def get_papers_for_website(self) -> List[Dict[str, str]]:
        return [
            {
                'id': row[0],
                'title': row[1],
                'authors': row[2],
                'year': row[3],
                'abstract': row[4],
                'url': row[5],
                'venue': row[6]
            }
            for row in self.local_data if row[7] == 'TRUE'  # website is True
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

    def get_all_entries(self) -> List[List[str]]:
        return self.local_data

    def clean_old_papers(self):
        self.logger.info("Cleaning old papers")
        one_week_ago = datetime.now().date() - timedelta(days=7)
        self.local_data = [self.HEADER_ROW] + [
            row for row in self.local_data[1:]
            if (row[7] == 'TRUE' or row[8] == 'TRUE' or row[9] != '') or  # Keep if posted or flagged
               (datetime.fromisoformat(row[10]).date() > one_week_ago)  # Keep if submitted within last week
        ]
        self.update_sheet()
        self.logger.debug(f"Cleaned sheet, new size: {len(self.local_data)} rows")