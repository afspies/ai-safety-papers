import arxiv
import logging
from typing import List, Dict
from datetime import datetime, timedelta

class ArxivAPI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = arxiv.Client()
        self.logger.debug("ArxivAPI initialized")

    def search_papers(self, query: str, max_results: int = 1000) -> List[Dict]:
        self.logger.info(f"Searching papers with query: {query}")
        
        # Set the date range for the last 7 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        date_filter = f" AND submittedDate:[{start_date.strftime('%Y%m%d')}0000 TO {end_date.strftime('%Y%m%d')}2359]"
        full_query = query + date_filter

        search = arxiv.Search(
            query=full_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        papers = []
        for result in self.client.results(search):
            paper = {
                'id': result.entry_id.split('/')[-1],
                'title': result.title,
                'authors': [author.name for author in result.authors],
                'year': result.published.year,
                'abstract': result.summary,
                'url': result.pdf_url,
                'venue': 'arXiv',
                'submitted_date': result.published.date()
            }
            papers.append(paper)

        self.logger.debug(f"Found {len(papers)} papers")
        return papers

    def fetch_paper_details(self, paper_id: str) -> Dict:
        self.logger.info(f"Fetching details for paper: {paper_id}")
        search = arxiv.Search(id_list=[paper_id])
        result = next(self.client.results(search))
        
        paper = {
            'id': result.entry_id.split('/')[-1],
            'title': result.title,
            'authors': [author.name for author in result.authors],
            'year': result.published.year,
            'abstract': result.summary,
            'url': result.pdf_url,
            'venue': 'arXiv'
        }
        
        self.logger.debug(f"Successfully fetched details for paper: {paper_id}")
        return paper