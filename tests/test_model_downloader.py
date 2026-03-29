"""Tests for core/model_downloader.py"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.model_downloader as dl


@pytest.fixture(autouse=True)
def use_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield


class TestListDownloaded:
    def test_returns_empty_when_dir_missing(self):
        result = dl.list_downloaded()
        assert result == []

    def test_returns_gguf_files(self, tmp_path):
        models = tmp_path / "models"
        models.mkdir()
        (models / "test.gguf").write_text("")
        # Redirect constant
        import core.model_downloader as dl2
        original = dl2.MODELS_DIR
        dl2.MODELS_DIR = str(models)
        result = dl2.list_downloaded()
        dl2.MODELS_DIR = original
        assert "test.gguf" in result

    def test_returns_bin_files(self, tmp_path):
        models = tmp_path / "models"
        models.mkdir()
        (models / "model.bin").write_text("")
        import core.model_downloader as dl2
        original = dl2.MODELS_DIR
        dl2.MODELS_DIR = str(models)
        result = dl2.list_downloaded()
        dl2.MODELS_DIR = original
        assert "model.bin" in result

    def test_ignores_other_extensions(self, tmp_path):
        models = tmp_path / "models"
        models.mkdir()
        (models / "readme.txt").write_text("")
        (models / "notes.md").write_text("")
        import core.model_downloader as dl2
        original = dl2.MODELS_DIR
        dl2.MODELS_DIR = str(models)
        result = dl2.list_downloaded()
        dl2.MODELS_DIR = original
        assert "readme.txt" not in result
        assert "notes.md" not in result


class TestStubs:
    def test_download_model_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            dl.download_model("http://example.com/model.gguf", "model.gguf")

    def test_cancel_download_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            dl.cancel_download()
