"""
Unit tests for the Telemetry Exporter.
Verifies Prometheus metrics registration, label mapping, and value updates.
"""

from prometheus_client import CollectorRegistry
from src.dsp_engine import DSPMetricsResult
from src.signal_generator import DetectorTelemetryFrame
from src.telemetry_exporter import TelemetryExporter


def test_exporter_metrics_recording():
    # Use isolated test registry
    test_registry = CollectorRegistry()
    exporter = TelemetryExporter(registry=test_registry)

    frame = DetectorTelemetryFrame(
        timestamp=1000.0,
        channel_id="test_sector",
        rf_phase_degrees=45.0,
        rf_amplitude_mv=250.0,
        beam_intensity_protons=1.2e11,
        cryo_temp_kelvin=1.92,
        blm_radiation_gy_per_sec=1e-5,
        is_anomaly_injected=False,
        anomaly_type="none",
    )

    dsp_result = DSPMetricsResult(
        channel_id="test_sector",
        sample_count=128,
        mean_cryo_temp=1.91,
        ewma_cryo_temp=1.915,
        temp_zscore=0.1,
        mean_beam_intensity=1.2e11,
        mean_blm_radiation=1e-5,
        rf_peak_freq_hz=400.0,
        snr_db=24.5,
        is_anomaly=False,
        alarm_status="NOMINAL",
        processing_latency_ms=0.85,
    )

    exporter.record_metrics(frame, dsp_result, window_size=128)

    # Validate metric values
    sample_count = test_registry.get_sample_value(
        "telemetry_samples_processed_total",
        labels={"channel_id": "test_sector"},
    )
    assert sample_count == 1.0

    cryo_val = test_registry.get_sample_value(
        "telemetry_cryo_temperature_kelvin",
        labels={"channel_id": "test_sector"},
    )
    assert cryo_val == 1.92

    buffer_fill = test_registry.get_sample_value(
        "telemetry_ring_buffer_fill_ratio",
        labels={"channel_id": "test_sector"},
    )
    assert buffer_fill == 1.0
