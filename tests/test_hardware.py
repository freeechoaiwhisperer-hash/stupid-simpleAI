"""Tests for core/hardware.py"""

import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import hardware


class TestRecommendModel:
    def test_high_ram_recommends_llama_8b(self):
        model = hardware.recommend_model(ram_gb=16)
        assert "8B" in model or "8b" in model.lower()

    def test_8gb_recommends_mistral_7b(self):
        model = hardware.recommend_model(ram_gb=8)
        assert "mistral" in model.lower() or "7b" in model.lower()

    def test_4gb_recommends_llama_3b(self):
        model = hardware.recommend_model(ram_gb=4)
        assert "3B" in model or "3b" in model.lower()

    def test_low_ram_recommends_tinyllama(self):
        model = hardware.recommend_model(ram_gb=2)
        assert "tiny" in model.lower() or "1.1b" in model.lower()

    def test_boundary_12gb(self):
        # Exactly 12 GB should get the 8B model
        model = hardware.recommend_model(ram_gb=12)
        assert "8B" in model or "8b" in model.lower()

    def test_boundary_8gb(self):
        model = hardware.recommend_model(ram_gb=8)
        # 8 GB → Mistral
        assert "mistral" in model.lower() or "7b" in model.lower()

    def test_returns_string(self):
        assert isinstance(hardware.recommend_model(4), str)

    def test_uses_system_ram_when_none(self):
        with patch.object(hardware, "get_ram_gb", return_value=16):
            model = hardware.recommend_model()
        assert isinstance(model, str)


class TestGetRamGb:
    def test_returns_positive_integer(self):
        ram = hardware.get_ram_gb()
        assert isinstance(ram, int)
        assert ram > 0

    def test_reasonable_range(self):
        ram = hardware.get_ram_gb()
        # Machines running tests have at least 1 GB and less than 10 TB
        assert 1 <= ram <= 10240


class TestGetCpuPercent:
    def test_returns_float(self):
        val = hardware.get_cpu_percent()
        assert isinstance(val, float)

    def test_range_0_to_100(self):
        val = hardware.get_cpu_percent()
        assert 0.0 <= val <= 100.0


class TestDetectGpu:
    def test_returns_dict(self):
        result = hardware.detect_gpu()
        assert isinstance(result, dict)

    def test_result_has_required_keys(self):
        result = hardware.detect_gpu()
        for key in ("available", "name", "vram_gb", "layers"):
            assert key in result

    def test_no_gpu_when_nvidia_smi_missing(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = hardware.detect_gpu()
        assert result["available"] is False

    def test_gpu_detected_when_nvidia_smi_succeeds(self):
        mock_output = b"NVIDIA GeForce RTX 3080, 10240\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
            )
            result = hardware.detect_gpu()
        assert result["available"] is True
        assert result["vram_gb"] == 10
        assert "3080" in result["name"]


class TestGetSystemInfo:
    def test_returns_dict(self):
        info = hardware.get_system_info()
        assert isinstance(info, dict)

    def test_has_ram_gb(self):
        info = hardware.get_system_info()
        assert "ram_gb" in info
        assert info["ram_gb"] > 0

    def test_has_gpu(self):
        info = hardware.get_system_info()
        assert "gpu" in info
        assert isinstance(info["gpu"], dict)


class TestGetNGpuLayers:
    def test_returns_int(self):
        val = hardware.get_n_gpu_layers()
        assert isinstance(val, int)

    def test_returns_zero_when_no_gpu(self):
        with patch.object(hardware, "detect_gpu",
                          return_value={"available": False, "name": "None",
                                        "vram_gb": 0, "layers": 0}):
            assert hardware.get_n_gpu_layers() == 0
