import logging
from contextlib import asynccontextmanager
import httpx
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from app.core.config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for API Gateway.
    """
    # Startup
    logger.info("Starting Volitas API Gateway...")
    
    # Initialize HTTP client for backend services
    app.state.http_client = httpx.AsyncClient(timeout=30.0)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Volitas API Gateway...")
    await app.state.http_client.aclose()


app = FastAPI(
    title="Volitas API Gateway",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Default CORS configuration for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:4173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Backend service URLs
BACKEND_API_URL = "http://localhost:8001"  # volitas-backend-api


@app.get("/")
async def root():
    return {
        "message": "Welcome to Volitas API Gateway",
        "version": "1.0.0",
        "services": {
            "backend_api": BACKEND_API_URL,
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy", "service": "api-gateway"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_backend(request: Request, path: str):
    """
    Proxy all API requests to the backend API service.
    """
    try:
        # Build target URL
        url = f"{BACKEND_API_URL}/{path}"
        
        # Forward query parameters
        if request.url.query:
            url += f"?{request.url.query}"
        
        # Get request body if present
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
        
        # Forward headers (except host)
        headers = dict(request.headers)
        headers.pop("host", None)
        
        # Make request to backend
        async with app.state.http_client as client:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
            )
        
        # Return response
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            try:
                content = response.json()
            except:
                content = response.text
        else:
            content = response.text
            
        return JSONResponse(
            content=content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
        
    except httpx.RequestError as e:
        logger.error(f"Request to backend failed: {e}")
        raise HTTPException(status_code=503, detail="Backend service unavailable")
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail="Internal gateway error")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
