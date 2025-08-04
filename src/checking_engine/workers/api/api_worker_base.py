from typing import Dict, Any

from checking_engine.workers.base_worker import BaseWorker
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)


class BaseAPIWorker(BaseWorker):
    """Base class for API-style workers (SIEM / EDR integrations).

    Provide a helper to make asynchronous HTTP requests.
    Subclasses should implement ``process_task`` to make the actual API call and parse the result.
    """

    worker_type: str = "api"

    async def _do_request(self, url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Make an HTTP request and return a dict."""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **kwargs) as resp:
                body = await resp.text()
                return {
                    "status": resp.status,
                    "headers": dict(resp.headers),
                    "body": body,
                }
