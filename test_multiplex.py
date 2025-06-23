from h2time import H2Time, H2Request
import asyncio
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')

async def test_multiplex():
    """Test HTTP/2 multiplexing by sending two requests in the same TCP packet."""
    # Create two identical requests
    r1 = H2Request(
        method="GET",
        url="https://localhost:8000/process?password=0123ABCD",
        headers={"User-Agent": "h2time/0.1"}
    )
    r2 = H2Request(
        method="GET",
        url="https://localhost:8000/process?password=0123ABCD",
        headers={"User-Agent": "h2time/0.1"}
    )
    
    logger.info("Starting multiplex test")
    start_time = datetime.now()
    
    async with H2Time(r1, r2, 
                     num_request_pairs=1,
                     sequential=False,  # Important: Use parallel mode
                     inter_request_time_ms=0,  # No delay between requests
                     verify_cert=False) as h2t:
        results = await h2t.run_attack()
        
        if results:
            # Parse the response bodies to get timing information
            for i, (diff, status, _) in enumerate(results):
                if status == "200":
                    logger.info(f"Request {i+1} completed with status {status}")
                    logger.info(f"Time difference: {diff/1e9:.6f}s")
                else:
                    logger.error(f"Request {i+1} failed with status {status}")
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    logger.info(f"Total test time: {total_time:.3f}s")

if __name__ == "__main__":
    asyncio.run(test_multiplex()) 