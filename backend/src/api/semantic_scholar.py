import requests
import logging
import time
from typing import List, Dict
from requests.exceptions import RequestException
from datetime import datetime, timedelta
from urllib.parse import urlencode

class SemanticScholarAPI:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    MAX_RETRIES = 5
    INITIAL_BACKOFF = 1  # Initial backoff time in seconds

    def __init__(self, api_key: str):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({"x-api-key": api_key})
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        self.logger.debug(f"Initializing SemanticScholarAPI with key: {masked_key}")
        self.logger.debug("SemanticScholarAPI initialized")
        self.last_request_time = {}
        self.rate_limit_delay = {
            'default': 0.1,  # 10 requests per second
            'limited': 1.0   # 1 request per second
        }

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        url = f"{self.BASE_URL}/{endpoint}"
        backoff = self.INITIAL_BACKOFF

        # Log the request details
        masked_headers = dict(self.session.headers)
        if 'x-api-key' in masked_headers:
            masked_headers['x-api-key'] = f"{masked_headers['x-api-key'][:4]}...{masked_headers['x-api-key'][-4:]}"
        
        # Construct and log the full URL
        if 'params' in kwargs:
            full_url = f"{url}?{urlencode(kwargs['params'])}"
        else:
            full_url = url
        self.logger.debug(f"Full request URL: {full_url}")
        
        self.logger.debug(f"Making request: {method} {url}")
        self.logger.debug(f"Headers: {masked_headers}")
        self.logger.debug(f"Params: {kwargs.get('params', {})}")

        # Determine the rate limit delay based on the endpoint
        if any(ep in endpoint for ep in ['/paper/batch', '/paper/search/bulk', '/recommendations']):
            delay = self.rate_limit_delay['limited']
        else:
            delay = self.rate_limit_delay['default']

        # Implement rate limiting
        current_time = time.time()
        if endpoint in self.last_request_time:
            time_since_last_request = current_time - self.last_request_time[endpoint]
            if time_since_last_request < delay:
                time.sleep(delay - time_since_last_request)

        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                self.last_request_time[endpoint] = time.time()
                return response.json()
            except RequestException as e:
                if response.status_code == 429:  # Too Many Requests
                    wait_time = backoff * (2 ** attempt)
                    self.logger.warning(f"Rate limited. Retrying in {wait_time} seconds.")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Request failed: {e}")
                    self.logger.error(f"Response status code: {response.status_code}")
                    self.logger.error(f"Response content: {response.text}")
                    raise

        self.logger.error("Max retries reached. Unable to complete request.")
        raise Exception("Max retries reached")

    def search_papers(self, query: str, limit: int = 100, year_range: str = None) -> List[Dict]:
        self.logger.info(f"Searching papers with query: {query}")
        params = {
            "query": query,
            "limit": limit,
            "fields": "paperId,title,authors,year,abstract,url,venue,publicationDate,tldr,embedding,isOpenAccess,openAccessPdf",
            "fieldsOfStudy": "Computer Science",
            "openAccessPdf": "true"  # Restrict to papers with a public PDF
        }
        if year_range:
            params["year"] = year_range

        data = self._make_request("GET", "paper/search", params=params)
        self.logger.debug(f"Raw API response: {data}")  # Log the raw response

        papers = data.get("data", [])
        self.logger.debug(f"Found {len(papers)} papers")

        # Log each paper's open access status and URL
        for paper in papers:
            self.logger.debug(f"Paper ID: {paper.get('paperId')}, Open Access: {paper.get('isOpenAccess')}, Open Access URL: {paper.get('openAccessPdf', {}).get('url')}")

        if not papers:
            self.logger.warning(f"No papers found. Full response: {data}")
        return papers

    def fetch_paper_details_batch(self, paper_ids: List[str]) -> List[Dict]:
        self.logger.info(f"Fetching details for {len(paper_ids)} papers")
        params = {
            "fields": "paperId,title,authors,year,abstract,url,venue,publicationDate"
        }
        data = self._make_request("POST", "paper/batch", json={"ids": paper_ids}, params=params)
        self.logger.debug(f"Successfully fetched details for {len(data)} papers")
        return data

    def get_relevant_papers(self, query: str, months: int = 1, limit: int = 100, ignore_date_range: bool = False) -> List[Dict]:
        self.logger.info(f"Fetching relevant papers for the last {months} months (ignore_date_range: {ignore_date_range})")
        
        current_date = datetime.now().date()
        start_date = current_date - timedelta(days=30*months)
        year_range = f"{start_date.year}-{current_date.year}"
        
        papers = self.search_papers(query, limit=limit, year_range=None if ignore_date_range else year_range)
        
        self.logger.debug(f"Total papers before filtering: {len(papers)}")
        
        if not ignore_date_range:
            # Filter papers by date
            filtered_papers = [
                paper for paper in papers
                if paper.get('publicationDate') and start_date <= datetime.fromisoformat(paper['publicationDate']).date() <= current_date
            ]
        else:
            filtered_papers = papers
        
        # Add query as a field to each paper
        for paper in filtered_papers:
            paper['query'] = query
            # Ensure pdf_url is always set
            paper['url'] = paper.get('openAccessPdf', {}).get('url', paper.get('url'))
        
        self.logger.debug(f"Found {len(filtered_papers)} relevant papers after {'date filtering' if not ignore_date_range else 'no date filtering'}")
        return filtered_papers
