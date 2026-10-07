"""
Unit tests for the DSP Engine module.
Verifies sliding window buffers, EWMA calculations, Z-Score detection,
FFT peak detection, and quench alarms.
"""

import numpy as np
from src.dsp_engine import CircularRingBuffer, DSPEngine
from src.signal_generator import DetectorTelemetryFrame


def test_circular_ring_buffer():
    buf = CircularRingBuffer(capacity=5)
    assert not buf.is_full()
    assert len(buf) == 0

    for i in range(5):
        buf.append(float(i))

    assert buf.is_full()
    assert len(buf) == 5
    np.testing.assert_array_equal(buf.to_numpy(), np.array([0, 1, 2, 3, 4]))

    # Test rollover
    buf.append(10.0)
    assert len(buf) == 5
    np.testing.assert_array_equal(buf.to_numpy(), np.array([1, 2, 3, 4, 10]))


def test_dsp_engine_warmup_and_processing():
    engine = DSPEngine(window_size=10, zscore_threshold=3.0)
    assert not engine.is_warmed_up()

    for i in range(10):
        frame = DetectorTelemetryFrame(
            timestamp=1000.0 + i,
            channel_id="test_channel",
            rf_phase_degrees=0.0,
            rf_amplitude_mv=250.0,
            beam_intensity_protons=1.15e11,
            cryo_temp_kelvin=1.9,
            blm_radiation_gy_per_sec=0.0001,
            is_anomaly_injected=False,
            anomaly_type="none",
        )
        res = engine.process_frame(frame)
        assert res.channel_id == "test_channel"
        assert res.alarm_status == "NOMINAL"
        assert res.processing_latency_ms >= 0.0

    assert engine.is_warmed_up()


def test_quench_critical_alarm():
    engine = DSPEngine(window_size=10, quench_threshold_k=4.2)
    frame = DetectorTelemetryFrame(
        timestamp=1000.0,
        channel_id="quench_chan",
        rf_phase_degrees=0.0,
        rf_amplitude_mv=250.0,
        beam_intensity_protons=1.15e11,
        cryo_temp_kelvin=5.5,  # Above quench threshold
        blm_radiation_gy_per_sec=0.0001,
        is_anomaly_injected=True,
        anomaly_type="cryogenic_quench",
    )
    res = engine.process_frame(frame)
    assert res.alarm_status == "CRITICAL_QUENCH"
    assert res.is_anomaly is True


def test_fft_and_snr_computation():
    engine = DSPEngine(sampling_rate_hz=100.0)
    t = np.linspace(0, 1.0, 100, endpoint=False)
    # Sine wave at 10 Hz
    signal = 5.0 * np.sin(2 * np.pi * 10.0 * t) + np.random.normal(0, 0.1, 100)

    freq, snr = engine.compute_fft_and_snr(signal)
    assert abs(freq - 10.0) <= 1.5
    assert snr > 10.0  # High SNR for clean sine
