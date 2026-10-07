"""
Kubernetes Health & Readiness HTTP Probes.
Provides /healthz (liveness) and /readyz (readiness) endpoints
to satisfy Kubernetes kubelet probe contracts.
"""

from collections.abc import Callable

from aiohttp import web


class HealthServer:
    """Async HTTP server handling Kubernetes probe requests."""

    def __init__(
        self,
        is_ready_callback: Callable[[], bool],
        host: str = "0.0.0.0",  # nosec B104
        port: int = 8080,
    ):
        self.is_ready_callback = is_ready_callback
        self.host = host
        self.port = port
        self.app = web.Application()
        self._setup_routes()
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    def _setup_routes(self) -> None:
        self.app.router.add_get("/healthz", self.handle_liveness)
        self.app.router.add_get("/readyz", self.handle_readiness)
        self.app.router.add_get("/", self.handle_index)

    async def handle_liveness(self, request: web.Request) -> web.Response:
        """Liveness check: confirms HTTP event loop is alive and non-blocked."""
        return web.json_response(
            {"status": "UP", "component": "telemetry-pipeline"},
            status=200,
        )

    async def handle_readiness(self, request: web.Request) -> web.Response:
        """
        Readiness check: confirms DSP sliding window buffer is populated
        and anomaly detection is operational.
        """
        if self.is_ready_callback():
            return web.json_response(
                {"status": "READY", "warmup": "COMPLETE"},
                status=200,
            )
        return web.json_response(
            {"status": "NOT_READY", "reason": "Buffer warming up"},
            status=503,
        )

    async def handle_index(self, request: web.Request) -> web.Response:
        return web.json_response(
            {
                "service": "hybrid-telemetry-observability-pipeline",
                "endpoints": ["/healthz", "/readyz", "http://<host>:9102/metrics"],
            },
            status=200,
        )

    async def start(self) -> None:
        """Start async HTTP server."""
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, self.host, self.port)
        await self._site.start()

    async def stop(self) -> None:
        """Gracefully stop async HTTP server."""
        if self._runner:
            await self._runner.cleanup()
