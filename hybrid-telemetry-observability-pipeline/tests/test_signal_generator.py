"""
Unit tests for the Signal Generator module.
Verifies physical bounds, channel isolation, and anomaly generation.
"""

import pytest
from src.signal_generator import DetectorTelemetryFrame, SignalGenerator


def test_signal_generator_initialization():
    gen = SignalGenerator(sampling_rate_hz=200.0, num_channels=4)
    channels = gen.get_channel_ids()
    assert len(channels) == 4
    assert "sector_1_blm" in channels
    assert "sector_4_blm" in channels


def test_generate_sample_contract():
    gen = SignalGenerator(sampling_rate_hz=100.0, num_channels=2)
    sample = gen.generate_sample("sector_1_blm")

    assert isinstance(sample, DetectorTelemetryFrame)
    assert sample.channel_id == "sector_1_blm"
    assert sample.timestamp > 0
    assert 1.0 < sample.cryo_temp_kelvin < 15.0  # Within realistic cryogenic range
    assert sample.beam_intensity_protons > 1e10
    assert sample.blm_radiation_gy_per_sec >= 0.0


def test_invalid_channel_raises_error():
    gen = SignalGenerator(num_channels=2)
    with pytest.raises(ValueError):
        gen.generate_sample("invalid_sector_99")


def test_anomaly_injection_quench():
    # Force high probability of anomaly
    gen = SignalGenerator(
        sampling_rate_hz=100.0,
        num_channels=1,
        inject_anomalies=True,
        anomaly_probability=1.0,
    )
    samples = [gen.generate_sample("sector_1_blm") for _ in range(30)]
    assert any(s.is_anomaly_injected for s in samples)
