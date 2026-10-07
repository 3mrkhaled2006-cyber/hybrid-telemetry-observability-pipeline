"""
Integration test for Main Application Daemon and Configuration.
Validates instantiation, lifecycle initialization, and daemon teardown.
"""

import asyncio

import pytest
from src.config import PipelineConfig
from src.main import PipelineDaemon, setup_logging


def test_pipeline_config_defaults():
    config = PipelineConfig()
    assert config.app_name == "hybrid-telemetry-observability-pipeline"
    assert config.sampling_rate_hz == 100.0
    assert config.window_size == 128
    assert config.health_port == 8080
    assert config.metrics_port == 9102
    assert config.cryo_quench_threshold_k == 4.2


def test_setup_logging():
    logger = setup_logging("DEBUG")
    assert logger.name == "telemetry.daemon"


@pytest.mark.asyncio
async def test_daemon_lifecycle_step():
    daemon = PipelineDaemon()
    assert daemon.running is False
    assert daemon.signal_gen is not None
    assert daemon.dsp_engine is not None

    # Test single iteration of processing loop without blocking
    daemon.running = True

    # Run loop briefly and cancel
    task = asyncio.create_task(daemon.run_telemetry_loop())
    await asyncio.sleep(0.05)
    daemon.stop()
    await task

    assert daemon.running is False
    await daemon.shutdown()
