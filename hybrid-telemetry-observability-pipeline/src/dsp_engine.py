"""
Digital Signal Processing (DSP) & Statistical Anomaly Engine.
Executes real-time sliding window analysis:
- Ring buffer sampling
- EWMA (Exponentially Weighted Moving Average)
- Fast Fourier Transform (FFT) peak frequency estimation
- Signal-to-Noise Ratio (SNR) in dB
- Robust Z-score anomaly & quench classification
"""

from collections import deque
from dataclasses import dataclass

import numpy as np

from src.signal_generator import DetectorTelemetryFrame


@dataclass
class DSPMetricsResult:
    """Aggregated numerical indicators produced by the DSP pipeline."""

    channel_id: str
    sample_count: int
    mean_cryo_temp: float
    ewma_cryo_temp: float
    temp_zscore: float
    mean_beam_intensity: float
    mean_blm_radiation: float
    rf_peak_freq_hz: float
    snr_db: float
    is_anomaly: bool
    alarm_status: str  # NOMINAL, WARNING, CRITICAL_QUENCH, BEAM_DUMP_TRIGGERED
    processing_latency_ms: float


class CircularRingBuffer:
    """Fixed-capacity ring buffer for low-latency sliding window computation."""

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.buffer: deque[float] = deque(maxlen=capacity)

    def append(self, val: float) -> None:
        self.buffer.append(val)

    def is_full(self) -> bool:
        return len(self.buffer) == self.capacity

    def to_numpy(self) -> np.ndarray:
        return np.array(self.buffer, dtype=np.float64)

    def __len__(self) -> int:
        return len(self.buffer)


class DSPEngine:
    """
    Real-Time Digital Signal Processing Engine.
    Processes telemetry frames and derives physical health indicators and alarms.
    """

    def __init__(
        self,
        window_size: int = 128,
        zscore_threshold: float = 3.0,
        ewma_alpha: float = 0.15,
        sampling_rate_hz: float = 100.0,
        quench_threshold_k: float = 4.2,
    ):
        self.window_size = window_size
        self.zscore_threshold = zscore_threshold
        self.ewma_alpha = ewma_alpha
        self.sampling_rate_hz = sampling_rate_hz
        self.quench_threshold_k = quench_threshold_k

        # Per-channel ring buffers
        self._temp_buffers: dict[str, CircularRingBuffer] = {}
        self._rf_buffers: dict[str, CircularRingBuffer] = {}
        self._blm_buffers: dict[str, CircularRingBuffer] = {}
        self._intensity_buffers: dict[str, CircularRingBuffer] = {}

        # Per-channel EWMA tracking
        self._ewma_temps: dict[str, float] = {}

    def _ensure_channel(self, channel_id: str) -> None:
        if channel_id not in self._temp_buffers:
            self._temp_buffers[channel_id] = CircularRingBuffer(self.window_size)
            self._rf_buffers[channel_id] = CircularRingBuffer(self.window_size)
            self._blm_buffers[channel_id] = CircularRingBuffer(self.window_size)
            self._intensity_buffers[channel_id] = CircularRingBuffer(self.window_size)

    def compute_fft_and_snr(self, signal: np.ndarray) -> tuple[float, float]:
        """
        Compute peak frequency and SNR (Signal-to-Noise Ratio) in decibels.
        """
        n = len(signal)
        if n < 4:
            return 0.0, 0.0

        # Remove DC offset
        detrended = signal - np.mean(signal)
        fft_vals = np.abs(np.fft.rfft(detrended))
        fft_freqs = np.fft.rfftfreq(n, d=1.0 / self.sampling_rate_hz)

        # Skip zero frequency (DC component)
        if len(fft_vals) <= 1:
            return 0.0, 0.0

        peak_idx = 1 + np.argmax(fft_vals[1:])
        peak_freq = float(fft_freqs[peak_idx])

        # Signal power vs noise power
        signal_power = float(fft_vals[peak_idx] ** 2)
        noise_power = float(np.sum(fft_vals**2) - signal_power) + 1e-12

        snr = 10.0 * np.log10(max(1e-12, signal_power / noise_power))
        return peak_freq, float(snr)

    def process_frame(self, frame: DetectorTelemetryFrame) -> DSPMetricsResult:
        """
        Ingest a single frame, update sliding buffers, compute rolling DSP
        transforms, and classify system health status.
        """
        import time

        t_start = time.perf_counter()
        chan = frame.channel_id
        self._ensure_channel(chan)

        # Update buffers
        self._temp_buffers[chan].append(frame.cryo_temp_kelvin)
        self._rf_buffers[chan].append(frame.rf_amplitude_mv)
        self._blm_buffers[chan].append(frame.blm_radiation_gy_per_sec)
        self._intensity_buffers[chan].append(frame.beam_intensity_protons)

        temp_arr = self._temp_buffers[chan].to_numpy()
        rf_arr = self._rf_buffers[chan].to_numpy()
        blm_arr = self._blm_buffers[chan].to_numpy()
        intensity_arr = self._intensity_buffers[chan].to_numpy()

        # Update EWMA
        if chan not in self._ewma_temps:
            self._ewma_temps[chan] = frame.cryo_temp_kelvin
        else:
            self._ewma_temps[chan] = (
                self.ewma_alpha * frame.cryo_temp_kelvin
                + (1.0 - self.ewma_alpha) * self._ewma_temps[chan]
            )

        # Rolling Statistics
        mean_temp = float(np.mean(temp_arr))
        std_temp = float(np.std(temp_arr)) if len(temp_arr) > 1 else 0.0
        zscore = (frame.cryo_temp_kelvin - mean_temp) / (std_temp + 1e-6)

        mean_intensity = float(np.mean(intensity_arr))
        mean_blm = float(np.mean(blm_arr))

        # FFT & SNR on RF cavity amplitude
        peak_freq, snr_db = self.compute_fft_and_snr(rf_arr)

        # Physical Alarm & Health Classification
        alarm_status = "NOMINAL"
        is_anomaly = False

        if frame.cryo_temp_kelvin >= self.quench_threshold_k:
            alarm_status = "CRITICAL_QUENCH"
            is_anomaly = True
        elif frame.blm_radiation_gy_per_sec > 0.005:
            alarm_status = "BEAM_DUMP_TRIGGERED"
            is_anomaly = True
        elif abs(zscore) > self.zscore_threshold or frame.is_anomaly_injected:
            alarm_status = "WARNING"
            is_anomaly = True

        processing_latency_ms = (time.perf_counter() - t_start) * 1000.0

        return DSPMetricsResult(
            channel_id=chan,
            sample_count=len(temp_arr),
            mean_cryo_temp=mean_temp,
            ewma_cryo_temp=self._ewma_temps[chan],
            temp_zscore=float(zscore),
            mean_beam_intensity=mean_intensity,
            mean_blm_radiation=mean_blm,
            rf_peak_freq_hz=peak_freq,
            snr_db=snr_db,
            is_anomaly=is_anomaly,
            alarm_status=alarm_status,
            processing_latency_ms=processing_latency_ms,
        )

    def is_warmed_up(self) -> bool:
        """Check if all active channels have saturated their sliding window buffer."""
        if not self._temp_buffers:
            return False
        return all(buf.is_full() for buf in self._temp_buffers.values())
