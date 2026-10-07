"""
Telemetry Exporter Module.
Exposes Prometheus metrics instrumented for SRE Golden Signals, low-level DSP telemetry,
and physical detector alerts.
"""

from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    Info,
    start_http_server,
)

from src.dsp_engine import DSPMetricsResult
from src.signal_generator import DetectorTelemetryFrame


class TelemetryExporter:
    """
    Manages Prometheus metric definitions and updates them based on
    real-time detector signals and DSP calculations.
    """

    def __init__(self, registry=REGISTRY):
        self.registry = registry

        # Application & Build Information
        self.info_build = Info(
            "telemetry_pipeline",
            "Pipeline daemon build metadata and version info",
            registry=self.registry,
        )
        self.info_build.info({"version": "1.0.0", "target": "cern-lhc-simulator"})

        # --- Counters ---
        self.counter_samples_total = Counter(
            "telemetry_samples_processed_total",
            "Total number of raw detector telemetry frames processed",
            ["channel_id"],
            registry=self.registry,
        )

        self.counter_anomalies_total = Counter(
            "telemetry_anomalies_detected_total",
            "Total number of anomalies detected by the DSP pipeline",
            ["channel_id", "alarm_status"],
            registry=self.registry,
        )

        self.counter_quench_events_total = Counter(
            "telemetry_quench_events_total",
            "Total number of critical superconducting magnet quench conditions detected",
            ["channel_id"],
            registry=self.registry,
        )

        # --- Gauges ---
        self.gauge_cryo_temp = Gauge(
            "telemetry_cryo_temperature_kelvin",
            "Instantaneous cryogenic magnet temperature in Kelvin",
            ["channel_id"],
            registry=self.registry,
        )

        self.gauge_ewma_temp = Gauge(
            "telemetry_cryo_temperature_ewma_kelvin",
            "Exponentially weighted moving average of cryogenic temperature in Kelvin",
            ["channel_id"],
            registry=self.registry,
        )

        self.gauge_beam_intensity = Gauge(
            "telemetry_beam_intensity_protons",
            "Estimated circulating particle beam intensity in protons per bunch",
            ["channel_id"],
            registry=self.registry,
        )

        self.gauge_blm_radiation = Gauge(
            "telemetry_blm_radiation_gy_per_sec",
            "Beam Loss Monitor radiation absorption rate in Gray per second",
            ["channel_id"],
            registry=self.registry,
        )

        self.gauge_snr_db = Gauge(
            "telemetry_rf_snr_decibels",
            "Signal-to-Noise Ratio (SNR) of RF cavity oscillation in decibels",
            ["channel_id"],
            registry=self.registry,
        )

        self.gauge_zscore = Gauge(
            "telemetry_cryo_temp_zscore",
            "Normalized rolling Z-Score of cryogenic temperature deviation",
            ["channel_id"],
            registry=self.registry,
        )

        self.gauge_buffer_fill_ratio = Gauge(
            "telemetry_ring_buffer_fill_ratio",
            "Fill ratio of the DSP sliding window ring buffer (0.0 to 1.0)",
            ["channel_id"],
            registry=self.registry,
        )

        # --- Histograms ---
        # Latency histogram with sub-millisecond to millisecond buckets
        self.hist_dsp_latency = Histogram(
            "telemetry_dsp_processing_latency_seconds",
            "Time spent executing DSP transforms and statistical anomaly classification",
            ["channel_id"],
            buckets=(
                0.00005,  # 50 us
                0.0001,   # 100 us
                0.00025,  # 250 us
                0.0005,   # 500 us
                0.001,    # 1 ms
                0.0025,   # 2.5 ms
                0.005,    # 5 ms
                0.010,    # 10 ms
                0.025,    # 25 ms
                0.050,    # 50 ms
            ),
            registry=self.registry,
        )

    def record_metrics(
        self,
        frame: DetectorTelemetryFrame,
        dsp_result: DSPMetricsResult,
        window_size: int,
    ) -> None:
        """Update all Prometheus metric counters and gauges."""
        chan = frame.channel_id

        # Update Counters
        self.counter_samples_total.labels(channel_id=chan).inc()

        if dsp_result.is_anomaly:
            self.counter_anomalies_total.labels(
                channel_id=chan,
                alarm_status=dsp_result.alarm_status,
            ).inc()

        if dsp_result.alarm_status == "CRITICAL_QUENCH":
            self.counter_quench_events_total.labels(channel_id=chan).inc()

        # Update Gauges
        self.gauge_cryo_temp.labels(channel_id=chan).set(frame.cryo_temp_kelvin)
        self.gauge_ewma_temp.labels(channel_id=chan).set(dsp_result.ewma_cryo_temp)
        self.gauge_beam_intensity.labels(channel_id=chan).set(frame.beam_intensity_protons)
        self.gauge_blm_radiation.labels(channel_id=chan).set(frame.blm_radiation_gy_per_sec)
        self.gauge_snr_db.labels(channel_id=chan).set(dsp_result.snr_db)
        self.gauge_zscore.labels(channel_id=chan).set(dsp_result.temp_zscore)

        fill_ratio = min(1.0, dsp_result.sample_count / float(window_size))
        self.gauge_buffer_fill_ratio.labels(channel_id=chan).set(fill_ratio)

        # Update Histogram (convert ms to seconds)
        latency_sec = dsp_result.processing_latency_ms / 1000.0
        self.hist_dsp_latency.labels(channel_id=chan).observe(latency_sec)

    def start_server(self, port: int, host: str = "0.0.0.0") -> None:  # nosec B104
        """Start standard Prometheus metrics HTTP server daemon."""
        start_http_server(port=port, addr=host, registry=self.registry)
