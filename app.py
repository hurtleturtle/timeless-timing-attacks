from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from typing import Optional
import logging
import time
import uuid
from datetime import datetime
from fastapi.responses import JSONResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('app')

app = FastAPI(title="Async Processing API")

class ProcessResponse(BaseModel):
    result: str
    processing_time: float
    request_id: str
    start_time: float
    end_time: float

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler that logs all errors."""
    error_id = str(uuid.uuid4())[:8]
    logger.error(f"[{error_id}] Unhandled error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_id": error_id,
            "detail": str(exc)
        }
    )

async def process_data(data: str, request_id: str) -> str:
    """Simulate some async processing on the input data."""
    password = "0123ABCD"
    delay_increment = 0.2
    
    # Pad data with '$' if shorter than password
    padded_data = data.ljust(len(password), '$')
    
    # Sequential character comparison with increasing delays
    for i, (test_char, pw_char) in enumerate(zip(padded_data, password)):
        if test_char == pw_char:
            # Increase delay for each correct character
            await asyncio.sleep(delay_increment)
            logger.info(f"[{request_id}] Correct char at position {i}, waiting {delay_increment:.3f}s")
        else:
            # Immediate return for incorrect characters
            logger.info(f"[{request_id}] Incorrect char at position {i}")
            return "Incorrect"
    
    # Additional delay for completely correct password
    logger.info(f"[{request_id}] All chars correct: {data}")
    return "Correct"

@app.get("/process", response_model=ProcessResponse)
async def process_endpoint(password: str):
    request_id = str(uuid.uuid4())[:8]  # Generate unique ID for this request
    start_time = time.time()
    try:
        logger.info(f"[{request_id}] Starting request processing at {datetime.fromtimestamp(start_time).strftime('%H:%M:%S.%f')}")
        
        # Process the password
        result = await process_data(password, request_id)
        
        end_time = time.time()
        processing_time = end_time - start_time
        logger.info(f"[{request_id}] Request completed in {processing_time:.3f}s at {datetime.fromtimestamp(end_time).strftime('%H:%M:%S.%f')}")
        
        return ProcessResponse(
            result=result,
            processing_time=processing_time,
            request_id=request_id,
            start_time=start_time,
            end_time=end_time
        )
    except Exception as e:
        logger.error(f"[{request_id}] Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/test-concurrency")
async def test_concurrency():
    """Test endpoint to demonstrate concurrent processing."""
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Starting concurrency test")
    
    # Create two tasks that will run concurrently
    async def task1():
        logger.info(f"[{request_id}] Task 1 started")
        await asyncio.sleep(1)
        logger.info(f"[{request_id}] Task 1 completed")
        return "Task 1"

    async def task2():
        logger.info(f"[{request_id}] Task 2 started")
        await asyncio.sleep(1)
        logger.info(f"[{request_id}] Task 2 completed")
        return "Task 2"

    # Run both tasks concurrently
    results = await asyncio.gather(task1(), task2())
    logger.info(f"[{request_id}] Both tasks completed: {results}")
    
    return {"results": results}

if __name__ == "__main__":
    import hypercorn.asyncio
    import hypercorn.config
    
    config = hypercorn.config.Config()
    config.bind = ["0.0.0.0:8000"]
    config.certfile = "certs/cert.pem"
    config.keyfile = "certs/key.pem"
    config.alpn_protocols = ["h2", "http/1.1"]
    config.accesslog = "-"  # Log to stdout
    config.errorlog = "-"   # Log errors to stdout
    config.loglevel = "INFO"
    config.use_reloader = True
    config.access_log_format = '%(m)s %(U)s %(q)s %(s)s %(D)s'
    
    # Log server startup
    logger.info("Starting server with HTTP/2 support")
    logger.info("Server will process requests concurrently")
    
    asyncio.run(hypercorn.asyncio.serve(app, config)) 