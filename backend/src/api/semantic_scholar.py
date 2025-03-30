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

    def __init__(self, api_key: str = None, development_mode: bool = False):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        
        # Set up API key if provided (it's now optional)
        if api_key and api_key not in ["your_semantic_scholar_api_key_here", "${SEMANTIC_SCHOLAR_API_KEY}"]:
            self.session.headers.update({"x-api-key": api_key})
            masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
            self.logger.debug(f"Initializing SemanticScholarAPI with key: {masked_key}")
        else:
            self.logger.info("Initializing SemanticScholarAPI without API key (using free tier)")
            
        self.development_mode = development_mode
        
        if development_mode:
            self.logger.info("SemanticScholarAPI initialized in development mode - will return mock data")
        else:
            self.logger.debug("SemanticScholarAPI initialized in normal mode")
            
        self.last_request_time = {}
        self.rate_limit_delay = {
            'default': 0.5,  # 2 requests per second for free tier
            'limited': 2.0   # 0.5 requests per second for bulk operations
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

        response = None
        for attempt in range(self.MAX_RETRIES):
            try:
                self.logger.debug(f"Attempt {attempt+1}/{self.MAX_RETRIES}")
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
                if response and response.status_code == 429:  # Too Many Requests
                    wait_time = backoff * (2 ** attempt)
                    self.logger.warning(f"Rate limited (429). Retrying in {wait_time} seconds.")
                    time.sleep(wait_time)
                elif response and response.status_code >= 500:  # Server error
                    wait_time = backoff * (2 ** attempt)
                    self.logger.warning(f"Server error ({response.status_code}). Retrying in {wait_time} seconds.")
                    time.sleep(wait_time)
                elif response and response.status_code == 404:  # Not found
                    self.logger.error(f"404 Not Found: {url}")
                    raise
                else:
                    self.logger.error(f"Request failed: {e}")
                    if response:
                        self.logger.error(f"Response status code: {response.status_code}")
                        self.logger.error(f"Response content: {response.text[:1000]}")  # Log first 1000 chars
                    else:
                        self.logger.error("No response object available (possible connection error)")
                    if attempt < self.MAX_RETRIES - 1:
                        wait_time = backoff * (2 ** attempt)
                        self.logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    raise

        self.logger.error("Max retries reached. Unable to complete request.")
        raise Exception("Max retries reached")

    def search_papers(self, query: str, limit: int = 100, year_range: str = None, offset: int = 0) -> List[Dict]:
        self.logger.info(f"Searching papers with query: {query}, limit: {limit}, offset: {offset}")
        
        # In development mode, return mock data
        if self.development_mode:
            self.logger.info("Development mode: Returning mock paper data")
            mock_papers = self._get_mock_papers(query, limit)
            self.logger.debug(f"Generated {len(mock_papers)} mock papers")
            return mock_papers
        
        # Normal API flow
        params = {
            "query": query,
            "limit": limit,
            "offset": offset,
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
            
    def _get_mock_papers(self, query: str, limit: int = 5) -> List[Dict]:
        """Generate mock paper data for development mode."""
        import random
        import uuid
        from datetime import datetime, timedelta
        
        # Generate a deterministic but unique set of papers for the query
        papers = []
        
        # Common AI safety paper titles for different queries
        title_templates = {
            "AI Safety": [
                "Evaluating {aspect} in Large Language Models: A {approach} Approach",
                "A Framework for {aspect} Alignment in Generative AI",
                "Towards Safer {system} Systems: {approach} for Risk Mitigation",
                "{approach} Methods for Assessing {aspect} in {system}",
                "Understanding and Preventing {aspect} in {system} through {approach}"
            ],
            "Mechanistic Interpretability": [
                "Interpreting {component} in {architecture} through {technique}",
                "A {technique} Approach to Mechanistic Interpretability in {architecture}",
                "Understanding {component} Representations in {architecture}",
                "Revealing {component} Structure through {technique} Analysis",
                "{technique} for Analyzing {component} Behavior in {system}"
            ]
        }
        
        # Components for generating realistic titles
        aspects = ["Safety", "Alignment", "Robustness", "Generalization", "Fairness", "Transparency", "Reliability"]
        approaches = ["Empirical", "Theoretical", "Causal", "Bayesian", "Game-Theoretic", "Adversarial", "Multi-Agent"]
        systems = ["Large Language Models", "Reinforcement Learning", "Neural Networks", "Multi-Modal", "Foundation Models", "Transformer"]
        components = ["Attention Heads", "Neurons", "Activations", "Embeddings", "Weight Matrices", "Circuit", "Modules"]
        architectures = ["Transformers", "GPT-style Models", "Diffusion Models", "Neural Networks", "Deep Learning Systems"]
        techniques = ["Causal Mediation", "Feature Attribution", "Activation Patching", "Matrix Factorization", "Influence Functions"]
        
        # Choose the right template set
        if "Mechanistic Interpretability" in query:
            templates = title_templates.get("Mechanistic Interpretability")
        else:
            templates = title_templates.get("AI Safety")
            
        if not templates:
            templates = title_templates.get("AI Safety")  # Default fallback
            
        # Generate papers
        for i in range(min(limit, 5)):  # Generate up to 5 mock papers
            # Generate a deterministic ID based on the query and index
            paper_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{query}_{i}"))
            
            # Create a random publication date within the last year
            days_ago = random.randint(1, 365)
            pub_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            # Generate title
            template = random.choice(templates)
            title = template.format(
                aspect=random.choice(aspects),
                approach=random.choice(approaches),
                system=random.choice(systems),
                component=random.choice(components),
                architecture=random.choice(architectures),
                technique=random.choice(techniques)
            )
            
            # Generate authors (2-4 authors)
            first_names = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Jamie", "Casey", "Riley"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
            num_authors = random.randint(2, 4)
            authors = []
            for _ in range(num_authors):
                author_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                authors.append({"name": author_name})
            
            # Generate abstract
            abstract = f"This paper presents a novel approach to {random.choice(aspects).lower()} in {random.choice(systems).lower()}. " \
                       f"We propose a {random.choice(approaches).lower()} method for assessing and improving model behavior. " \
                       f"Our experiments show promising results on benchmark datasets."
            
            # Create URL (prefer arxiv-style URLs for easier processing)
            arxiv_id = f"2303.{random.randint(10000, 99999)}"
            
            # Create a paper object
            paper = {
                "paperId": paper_id,
                "title": title,
                "authors": authors,
                "year": int(pub_date.split('-')[0]),
                "abstract": abstract,
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "venue": random.choice(["arXiv", "ICLR", "NeurIPS", "ICML", "AAAI"]),
                "publicationDate": pub_date,
                "tldr": {"text": abstract[:100] + "..."},
                "externalIds": {"ArXiv": arxiv_id},
                "isOpenAccess": True
            }
            
            papers.append(paper)
        
        return papers

    def fetch_paper_details_batch(self, paper_ids: List[str]) -> List[Dict]:
        self.logger.info(f"Fetching details for {len(paper_ids)} papers")
        
        # In development mode, return mock data
        if self.development_mode:
            self.logger.info("Development mode: Returning mock paper details")
            return [self._get_mock_paper_details(paper_id) for paper_id in paper_ids]
        
        # Normal API flow
        params = {
            "fields": "paperId,title,authors,year,abstract,url,venue,publicationDate"
        }
        data = self._make_request("POST", "paper/batch", json={"ids": paper_ids}, params=params)
        self.logger.debug(f"Successfully fetched details for {len(data)} papers")
        return data
        
    def _get_mock_paper_details(self, paper_id: str) -> Dict:
        """Generate mock paper details for a specific paper ID."""
        # Generate deterministic paper details based on the paper ID
        import random
        import hashlib
        
        # Use the paper ID to seed the random generator for deterministic output
        seed = int(hashlib.md5(paper_id.encode()).hexdigest(), 16) % (10**8)
        random.seed(seed)
        
        # Generate mock data similar to _get_mock_papers but for a specific ID
        aspects = ["Safety", "Alignment", "Robustness", "Generalization", "Fairness", "Transparency", "Reliability"]
        approaches = ["Empirical", "Theoretical", "Causal", "Bayesian", "Game-Theoretic", "Adversarial", "Multi-Agent"]
        systems = ["Large Language Models", "Reinforcement Learning", "Neural Networks", "Multi-Modal", "Foundation Models", "Transformer"]
        
        title = f"A {random.choice(approaches)} Approach to {random.choice(aspects)} in {random.choice(systems)}"
        
        first_names = ["Alex", "Sam", "Jordan", "Taylor", "Morgan", "Jamie", "Casey", "Riley"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        num_authors = random.randint(2, 4)
        authors = []
        for _ in range(num_authors):
            author_name = f"{random.choice(first_names)} {random.choice(last_names)}"
            authors.append({"name": author_name})
        
        abstract = f"This paper presents a novel approach to {random.choice(aspects).lower()} in {random.choice(systems).lower()}. " \
                   f"We propose a {random.choice(approaches).lower()} method for assessing and improving model behavior. " \
                   f"Our experiments show promising results on benchmark datasets."
        
        from datetime import datetime, timedelta
        days_ago = random.randint(1, 365)
        pub_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        arxiv_id = f"2303.{random.randint(10000, 99999)}"
        
        return {
            "paperId": paper_id,
            "title": title,
            "authors": authors,
            "year": int(pub_date.split('-')[0]),
            "abstract": abstract,
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "venue": random.choice(["arXiv", "ICLR", "NeurIPS", "ICML", "AAAI"]),
            "publicationDate": pub_date
        }

    def get_paper_by_id(self, paper_id: str) -> Dict:
        """
        Fetch a paper by its ID directly from Semantic Scholar.
        
        Args:
            paper_id: The paper ID to fetch
            
        Returns:
            Dict containing the paper details, or None if not found
        """
        self.logger.info(f"Fetching paper with ID: {paper_id}")
        
        # In development mode, return mock data
        if self.development_mode:
            self.logger.info("Development mode: Returning mock paper data")
            return self._get_mock_paper_details(paper_id)
        
        # Normal API flow
        try:
            params = {
                "fields": "paperId,title,authors,year,abstract,url,venue,publicationDate,tldr,embedding,isOpenAccess,openAccessPdf,externalIds"
            }
            
            # Direct endpoint for a single paper
            data = self._make_request("GET", f"paper/{paper_id}", params=params)
            
            if not data:
                self.logger.error(f"No data returned for paper ID: {paper_id}")
                return None
                
            # Process paper to ensure we have the best available URL
            if data is None:
                return None
                
            # Log TLDR information for debugging
            if 'tldr' in data:
                self.logger.debug(f"Found TLDR for paper {data.get('paperId')}: {data['tldr']}")
            else:
                self.logger.debug(f"No TLDR found for paper {data.get('paperId')}")
            
            # Start with the default URL
            best_url = data.get('url', '')
            
            # Check for open access PDF URL first
            if data.get('openAccessPdf', None) is not None and data['openAccessPdf'].get('url'):
                best_url = data['openAccessPdf']['url']
            # Check for ArXiv ID regardless of isOpenAccess status
            elif data.get('externalIds', {}).get('ArXiv'):
                arxiv_id = data['externalIds']['ArXiv']
                best_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            # If no ArXiv, but paper is marked as open access, might have other sources
            elif data.get('isOpenAccess'):
                # Could add other open access sources here if needed
                pass
            
            # Update the paper URL and log the change
            if best_url != data.get('url'):
                self.logger.debug(f"Updated URL for paper {data['paperId']}: {best_url}")
                if 'arxiv.org' in best_url:
                    self.logger.debug(f"Using ArXiv URL for paper {data['paperId']}")
            data['url'] = best_url
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error in get_paper_by_id: {str(e)}")
            self.logger.exception("Full traceback:")
            return None

    def get_relevant_papers(self, query: str, months: int = 1, limit: int = 100, ignore_date_range: bool = False, offset: int = 0) -> List[Dict]:
        self.logger.info(f"Fetching relevant papers for the last {months} months (ignore_date_range: {ignore_date_range}, offset: {offset})")
        
        current_date = datetime.now().date()
        start_date = current_date - timedelta(days=30*months)
        year_range = f"{start_date.year}-{current_date.year}"
        
        papers = self.search_papers(query, limit=limit, year_range=None if ignore_date_range else year_range, offset=offset)
        
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
