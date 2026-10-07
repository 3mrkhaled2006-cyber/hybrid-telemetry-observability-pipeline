"""
Pipeline Configuration Module.
Provides strongly-typed, environment-aware configuration using Pydantic.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineConfig(BaseSettings):
    """Core runtime configuration for telemetry pipeline daemon."""

    model_config = SettingsConfigDict(
        env_prefix="PIPELINE_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application Metadata
    app_name: str = Field(default="hybrid-telemetry-observability-pipeline")
    environment: str = Field(default="production")
    log_level: str = Field(default="INFO")
    version: str = Field(default="1.0.0")

    # Networking & Ports (0.0.0.0 required for container interface exposure)
    health_host: str = Field(default="0.0.0.0")  # nosec B104
    health_port: int = Field(default=8080)
    metrics_host: str = Field(default="0.0.0.0")  # nosec B104
    metrics_port: int = Field(default=9102)

    # Signal & Sampling Parameters
    sampling_rate_hz: float = Field(default=100.0, ge=1.0, le=10000.0)
    window_size: int = Field(default=128, ge=16, le=4096)
    num_channels: int = Field(default=4, ge=1, le=16)

    # Synthetic Physics & Anomaly Simulation
    inject_anomalies: bool = Field(default=True)
    anomaly_probability: float = Field(default=0.03, ge=0.0, le=1.0)
    beam_energy_gev: float = Field(default=7000.0)  # CERN LHC Nominal (7 TeV)
    cryo_nominal_temp_k: float = Field(default=1.9)  # Superfluid Helium Temperature
    cryo_quench_threshold_k: float = Field(default=4.2)  # Quench threshold (He boiling pt)

    # DSP Algorithm Parameters
    zscore_threshold: float = Field(default=3.0, ge=1.0)
    ewma_alpha: float = Field(default=0.15, gt=0.0, le=1.0)


# Global singleton configuration
settings = PipelineConfig()
