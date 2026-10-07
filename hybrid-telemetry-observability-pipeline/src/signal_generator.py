"""
Signal Generator & Physical Detector Telemetry Simulator.
Simulates high-frequency detector hardware telemetry (CERN LHC beam instrumentation,
RF cavity resonance, beam loss monitors, and superconducting magnet cryogenics).
"""

import random
import time
from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class DetectorTelemetryFrame:
    """Immutable snapshot of physical detector telemetry at time t."""

    timestamp: float
    channel_id: str
    rf_phase_degrees: float
    rf_amplitude_mv: float
    beam_intensity_protons: float
    cryo_temp_kelvin: float
    blm_radiation_gy_per_sec: float
    is_anomaly_injected: bool
    anomaly_type: str


class SignalGenerator:
    """
    High-fidelity physical signal simulator producing multi-channel telemetry streams
    with realistic stochastic noise and physical anomaly vectors.
    """

    def __init__(
        self,
        sampling_rate_hz: float = 100.0,
        num_channels: int = 4,
        inject_anomalies: bool = True,
        anomaly_probability: float = 0.03,
        nominal_cryo_temp_k: float = 1.9,
        quench_threshold_k: float = 4.2,
    ):
        self.sampling_rate_hz = sampling_rate_hz
        self.dt = 1.0 / sampling_rate_hz
        self.num_channels = num_channels
        self.inject_anomalies = inject_anomalies
        self.anomaly_probability = anomaly_probability
        self.nominal_cryo_temp_k = nominal_cryo_temp_k
        self.quench_threshold_k = quench_threshold_k

        self._t = 0.0
        # State tracking per channel for continuous physical state simulation
        self._channel_states: dict[str, dict[str, Any]] = {}
        for i in range(num_channels):
            chan_id = f"sector_{i+1}_blm"
            self._channel_states[chan_id] = {
                "base_cryo_temp": nominal_cryo_temp_k + random.uniform(-0.02, 0.02),
                "beam_intensity": 1.15e11 * (1.0 + random.uniform(-0.01, 0.01)),
                "carrier_freq_hz": 400.78 + random.uniform(-0.05, 0.05),  # 400 MHz LHC RF base
                "active_quench": False,
                "quench_countdown": 0,
            }

    def generate_sample(self, channel_id: str) -> DetectorTelemetryFrame:
        """
        Generate a single telemetry sample for the specified channel,
        advancing physical simulation time.
        """
        state = self._channel_states.get(channel_id)
        if not state:
            raise ValueError(f"Unknown channel: {channel_id}")

        self._t += self.dt
        t = self._t

        # 1. RF Cavity phase and amplitude (harmonic oscillator with phase noise)
        freq = state["carrier_freq_hz"]
        phase_jitter = np.random.normal(0.0, 0.35)
        rf_phase = (np.sin(2.0 * np.pi * freq * t) * 180.0 / np.pi) + phase_jitter
        rf_amplitude = 250.0 + (np.cos(2.0 * np.pi * 0.1 * t) * 5.0) + np.random.normal(0.0, 1.2)

        # 2. Beam Intensity (protons per bunch) with slow burn-off and Poisson-like fluctuations
        beam_intensity = state["beam_intensity"] + np.random.normal(0.0, 1e8)

        # 3. Cryogenics temperature (Kelvin)
        cryo_temp = state["base_cryo_temp"] + np.random.normal(0.0, 0.005)

        # 4. Beam Loss Monitor (radiation dosage rate in Gray/s)
        # Background radiation is sub-microGray/s
        blm_radiation = max(0.0, np.random.exponential(scale=1.5e-5))

        # 5. Anomaly Injection Logic
        is_anomaly = False
        anomaly_type = "none"

        # Check ongoing quench recovery
        if state["active_quench"]:
            state["quench_countdown"] -= 1
            cryo_temp += random.uniform(2.5, 4.8)  # Superconducting quench heating
            blm_radiation += random.uniform(0.005, 0.08)  # Radiation surge from beam dump
            is_anomaly = True
            anomaly_type = "cryogenic_quench"
            if state["quench_countdown"] <= 0:
                state["active_quench"] = False

        elif self.inject_anomalies and random.random() < self.anomaly_probability:
            is_anomaly = True
            roll = random.random()
            if roll < 0.35:
                # Magnet quench initiation
                state["active_quench"] = True
                state["quench_countdown"] = random.randint(15, 40)
                cryo_temp += 3.0
                anomaly_type = "cryogenic_quench"
            elif roll < 0.70:
                # Beam loss radiation burst
                blm_radiation += random.uniform(0.01, 0.05)
                beam_intensity -= 1e10  # Beam loss
                anomaly_type = "beam_loss_burst"
            else:
                # RF Cavity phase slip
                rf_phase += random.choice([-90.0, 90.0, 180.0])
                anomaly_type = "rf_phase_slip"

        return DetectorTelemetryFrame(
            timestamp=time.time(),
            channel_id=channel_id,
            rf_phase_degrees=float(rf_phase),
            rf_amplitude_mv=float(rf_amplitude),
            beam_intensity_protons=float(beam_intensity),
            cryo_temp_kelvin=float(cryo_temp),
            blm_radiation_gy_per_sec=float(blm_radiation),
            is_anomaly_injected=is_anomaly,
            anomaly_type=anomaly_type,
        )

    def get_channel_ids(self) -> list[str]:
        """Return list of active detector channel identifiers."""
        return list(self._channel_states.keys())
