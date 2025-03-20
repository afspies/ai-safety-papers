import requests
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_caching():
    """Test the API caching implementation."""
    base_url = "http://localhost:8000/api"
    
    # Test 1: Basic caching of the same endpoint
    logger.info("== Test 1: Basic caching of the same endpoint ==")
    
    # First request - should be a cache miss
    logger.info("Making first request to /api/papers...")
    start_time = time.time()
    response = requests.get(f"{base_url}/papers")
    duration = time.time() - start_time
    
    if response.status_code != 200:
        logger.error(f"Request failed with status code: {response.status_code}")
    else:
        logger.info(f"First request took {duration:.2f} seconds")
    
    # Second request - should be a cache hit
    logger.info("Making second request to /api/papers...")
    start_time = time.time()
    response = requests.get(f"{base_url}/papers")
    duration = time.time() - start_time
    
    if response.status_code != 200:
        logger.error(f"Request failed with status code: {response.status_code}")
    else:
        logger.info(f"Second request took {duration:.2f} seconds")
    
    # Test 2: Different endpoints with shared cache
    logger.info("\n== Test 2: Different endpoints with shared cache ==")
    
    # First request to highlighted - may use cached data from all_papers
    logger.info("Making first request to /api/papers/highlighted...")
    start_time = time.time()
    response = requests.get(f"{base_url}/papers/highlighted")
    duration = time.time() - start_time
    
    if response.status_code != 200:
        logger.error(f"Request failed with status code: {response.status_code}")
    else:
        logger.info(f"First request to highlighted took {duration:.2f} seconds")
    
    # Second request to highlighted - should be a cache hit
    logger.info("Making second request to /api/papers/highlighted...")
    start_time = time.time()
    response = requests.get(f"{base_url}/papers/highlighted")
    duration = time.time() - start_time
    
    if response.status_code != 200:
        logger.error(f"Request failed with status code: {response.status_code}")
    else:
        logger.info(f"Second request to highlighted took {duration:.2f} seconds")
    
    # Test 3: Cache expiration (waiting just 1 second to see if cache is still valid)
    logger.info("\n== Test 3: Cache validity check ==")
    
    logger.info("Waiting 1 second...")
    time.sleep(1)
    
    # Request after wait - should still be a cache hit 
    logger.info("Making request after waiting 1 second...")
    start_time = time.time()
    response = requests.get(f"{base_url}/papers")
    duration = time.time() - start_time
    
    if response.status_code != 200:
        logger.error(f"Request failed with status code: {response.status_code}")
    else:
        logger.info(f"Request after waiting took {duration:.2f} seconds")
    
    logger.info("Cache test complete.")

if __name__ == "__main__":
    test_api_caching()