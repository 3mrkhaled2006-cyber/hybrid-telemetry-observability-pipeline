"""
Main Application Daemon.
Orchestrates high-frequency detector signal generation, real-time DSP analysis,
Prometheus metrics exporting, and Kubernetes probe servers with graceful shutdown.
"""

import asyncio
import logging
import signal

from src.config import settings
from src.dsp_engine import DSPEngine
from src.health import HealthServer
from src.signal_generator import SignalGenerator
from src.telemetry_exporter import TelemetryExporter


def setup_logging(level_name: str) -> logging.Logger:
    """Initialize structured stream logging."""
    numeric_level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("telemetry.daemon")


class PipelineDaemon:
    """Master lifecycle manager for the hybrid telemetry observability pipeline."""

    def __init__(self):
        self.logger = setup_logging(settings.log_level)
        self.running = False

        self.signal_gen = SignalGenerator(
            sampling_rate_hz=settings.sampling_rate_hz,
            num_channels=settings.num_channels,
            inject_anomalies=settings.inject_anomalies,
            anomaly_probability=settings.anomaly_probability,
            nominal_cryo_temp_k=settings.cryo_nominal_temp_k,
            quench_threshold_k=settings.cryo_quench_threshold_k,
        )

        self.dsp_engine = DSPEngine(
            window_size=settings.window_size,
            zscore_threshold=settings.zscore_threshold,
            ewma_alpha=settings.ewma_alpha,
            sampling_rate_hz=settings.sampling_rate_hz,
            quench_threshold_k=settings.cryo_quench_threshold_k,
        )

        self.exporter = TelemetryExporter()
        self.health_server = HealthServer(
            is_ready_callback=self.dsp_engine.is_warmed_up,
            host=settings.health_host,
            port=settings.health_port,
        )

    async def run_telemetry_loop(self) -> None:
        """High-frequency sampling and processing loop."""
        interval = 1.0 / settings.sampling_rate_hz
        channel_ids = self.signal_gen.get_channel_ids()
        self.logger.info(
            "Starting DSP telemetry loop across %d channels at %.1f Hz",
            len(channel_ids),
            settings.sampling_rate_hz,
        )

        iterations = 0
        while self.running:
            t_start = asyncio.get_event_loop().time()

            for chan_id in channel_ids:
                # 1. Generate physical telemetry sample
                frame = self.signal_gen.generate_sample(chan_id)

                # 2. Execute DSP and statistical anomaly classification
                dsp_result = self.dsp_engine.process_frame(frame)

                # 3. Export to Prometheus collectors
                self.exporter.record_metrics(
                    frame=frame,
                    dsp_result=dsp_result,
                    window_size=settings.window_size,
                )

                if dsp_result.is_anomaly and iterations % 50 == 0:
                    self.logger.warning(
                        f"Anomaly detected on {chan_id}: Status={dsp_result.alarm_status}, "
                        f"Cryo={frame.cryo_temp_kelvin:.2f}K (Z={dsp_result.temp_zscore:.2f}), "
                        f"BLM={frame.blm_radiation_gy_per_sec:.5f}Gy/s"
                    )

            iterations += 1
            elapsed = asyncio.get_event_loop().time() - t_start
            sleep_time = max(0.0, interval - elapsed)
            await asyncio.sleep(sleep_time)

    async def start(self) -> None:
        """Bootstrap all subsystems and listen for termination signals."""
        self.logger.info(
            "Initializing %s [env=%s, version=%s]",
            settings.app_name,
            settings.environment,
            settings.version,
        )

        # 1. Start Prometheus HTTP exposition server
        self.logger.info(
            "Exposing Prometheus metrics on http://%s:%d/metrics",
            settings.metrics_host,
            settings.metrics_port,
        )
        self.exporter.start_server(
            port=settings.metrics_port,
            host=settings.metrics_host,
        )

        # 2. Start Health probe server
        self.logger.info(
            "Exposing Health probes on http://%s:%d (/healthz, /readyz)",
            settings.health_host,
            settings.health_port,
        )
        await self.health_server.start()

        self.running = True

        # 3. Register signal handlers
        loop = asyncio.get_running_loop()
        stop_signals: set[signal.Signals] = {signal.SIGINT, signal.SIGTERM}

        for sig in stop_signals:
            try:
                loop.add_signal_handler(sig, self.stop)
            except NotImplementedError:
                # Windows event loop fallback
                signal.signal(sig, lambda s, f: self.stop())

        # 4. Run main processing loop
        try:
            await self.run_telemetry_loop()
        finally:
            await self.shutdown()

    def stop(self) -> None:
        """Signal termination flag."""
        self.logger.info("Termination signal received. Initiating graceful shutdown...")
        self.running = False

    async def shutdown(self) -> None:
        """Drain buffers and stop HTTP servers."""
        self.logger.info("Stopping health probe server...")
        await self.health_server.stop()
        self.logger.info("Telemetry pipeline daemon stopped cleanly.")


def main():
    daemon = PipelineDaemon()
    try:
        asyncio.run(daemon.start())
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
