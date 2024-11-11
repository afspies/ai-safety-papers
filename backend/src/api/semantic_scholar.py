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
                # Log the response details
                self.logger.debug(f"Response status code: {response.status_code}")
                self.logger.debug(f"Response headers: {dict(response.headers)}")
                
                # Check if the response is valid JSON before parsing
                try:
                    data = response.json()
                except ValueError as e:
                    self.logger.error(f"Failed to parse JSON response: {e}")
                    self.logger.error(f"Response content: {response.text[:1000]}")  # Log first 1000 chars
                    raise

                response.raise_for_status()
                self.last_request_time[endpoint] = time.time()
                return data
            except RequestException as e:
                if response.status_code == 429:  # Too Many Requests
                    wait_time = backoff * (2 ** attempt)
                    self.logger.warning(f"Rate limited. Retrying in {wait_time} seconds.")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"Request failed: {e}")
                    self.logger.error(f"Response status code: {response.status_code}")
                    self.logger.error(f"Response content: {response.text[:1000]}")  # Log first 1000 chars
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = backoff * (2 ** attempt)
                        self.logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    raise

        self.logger.error("Max retries reached. Unable to complete request.")
        raise Exception("Max retries reached")

    def search_papers(self, query: str, limit: int = 100, year_range: str = None) -> List[Dict]:
        self.logger.info(f"Searching papers with query: {query}")
        params = {
            "query": query,
            "limit": limit,
            "fields": "paperId,title,authors,year,abstract,url,venue,publicationDate,tldr,embedding,isOpenAccess,openAccessPdf,externalIds",
            "fieldsOfStudy": "Computer Science"
        }
        if year_range:
            params["year"] = year_range

        try:
            data = self._make_request("GET", "paper/search", params=params)
            
            # Add debug logging for the response
            self.logger.debug(f"Response data keys: {data.keys() if data else 'None'}")
            
            if not data:
                self.logger.error("Received empty response from API")
                return []
                
            papers = data.get("data", [])
            if not papers:
                self.logger.warning("No papers found in response")
                return []
                
            self.logger.debug(f"Found {len(papers)} papers in response")
            
            # Process papers to ensure we have the best available URL and log TLDRs
            for paper in papers:
                if paper is None:
                    continue
                
                # Log TLDR information for debugging
                if 'tldr' in paper:
                    self.logger.debug(f"Found TLDR for paper {paper.get('paperId')}: {paper['tldr']}")
                else:
                    self.logger.debug(f"No TLDR found for paper {paper.get('paperId')}")
                
                # Start with the default URL
                best_url = paper.get('url', '')
                
                # Check for open access PDF URL first
                if paper.get('openAccessPdf', None) is not None and paper['openAccessPdf'].get('url'):
                    best_url = paper['openAccessPdf']['url']
                # Check for ArXiv ID regardless of isOpenAccess status
                elif paper.get('externalIds', {}).get('ArXiv'):
                    arxiv_id = paper['externalIds']['ArXiv']
                    best_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                # If no ArXiv, but paper is marked as open access, might have other sources
                elif paper.get('isOpenAccess'):
                    # Could add other open access sources here if needed
                    pass
                
                # Update the paper URL and log the change
                if best_url != paper.get('url'):
                    self.logger.debug(f"Updated URL for paper {paper['paperId']}: {best_url}")
                    if 'arxiv.org' in best_url:
                        self.logger.debug(f"Using ArXiv URL for paper {paper['paperId']}")
                paper['url'] = best_url
            
            return papers
        except Exception as e:
            self.logger.error(f"Error in search_papers: {str(e)}")
            self.logger.exception("Full traceback:")
            return []

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
        
        # Add query and ensure best URL is used
        for paper in filtered_papers:
            paper['query'] = query
            # URL should already be the best available from search_papers()
            if not paper.get('url'):
                self.logger.warning(f"No URL found for paper {paper.get('paperId')}")
        
        self.logger.debug(f"Found {len(filtered_papers)} relevant papers after {'date filtering' if not ignore_date_range else 'no date filtering'}")
        return filtered_papers
