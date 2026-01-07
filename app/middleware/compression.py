"""Response compression middleware.

Note: FastAPI/Uvicorn handles GZip compression automatically via the
'--compress-level' flag or CompressionMiddleware from starlette.
This module is kept for potential custom compression logic.
"""

from starlette.middleware.gzip import GZipMiddleware

# Use Starlette's built-in GZip middleware
CompressionMiddleware = GZipMiddleware

