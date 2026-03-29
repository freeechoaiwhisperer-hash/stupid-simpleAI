"""Tests for core/model_manager.py — non-Llama logic"""

import sys
import os
import time
import glob
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.model_manager as mm


@pytest.fixture(autouse=True)
def reset_model_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mm._model = None
    mm._current_model = None
    yield
    mm._model = None
    mm._current_model = None


class TestPersonalities:
    def test_personalities_dict_has_expected_keys(self):
        assert "normal" in mm.PERSONALITIES
        assert "unhinged" in mm.PERSONALITIES
        assert "focused" in mm.PERSONALITIES

    def test_all_personality_prompts_are_strings(self):
        for key, prompt in mm.PERSONALITIES.items():
            assert isinstance(prompt, str), f"Personality '{key}' is not a string"
            assert len(prompt) > 0


class TestGetModelList:
    def test_returns_list(self, tmp_path):
        os.makedirs(mm.MODELS_DIR, exist_ok=True)
        result = mm.get_model_list()
        assert isinstance(result, list)

    def test_returns_gguf_files(self, tmp_path):
        os.makedirs(mm.MODELS_DIR, exist_ok=True)
        model_path = os.path.join(mm.MODELS_DIR, "test_model.gguf")
        open(model_path, "w").close()
        result = mm.get_model_list()
        assert "test_model.gguf" in result

    def test_ignores_non_gguf_files(self, tmp_path):
        os.makedirs(mm.MODELS_DIR, exist_ok=True)
        open(os.path.join(mm.MODELS_DIR, "readme.txt"), "w").close()
        result = mm.get_model_list()
        assert "readme.txt" not in result

    def test_returns_sorted_list(self, tmp_path):
        os.makedirs(mm.MODELS_DIR, exist_ok=True)
        for name in ["z_model.gguf", "a_model.gguf", "m_model.gguf"]:
            open(os.path.join(mm.MODELS_DIR, name), "w").close()
        result = mm.get_model_list()
        assert result == sorted(result)

    def test_empty_list_when_no_models(self, tmp_path):
        os.makedirs(mm.MODELS_DIR, exist_ok=True)
        result = mm.get_model_list()
        assert result == []


class TestIsModelLoaded:
    def test_false_when_no_model(self):
        assert mm.is_model_loaded() is False

    def test_true_when_model_set(self):
        mm._model = MagicMock()
        assert mm.is_model_loaded() is True


class TestGetCurrentModel:
    def test_returns_none_when_no_model(self):
        assert mm.get_current_model() is None

    def test_returns_model_name_when_set(self):
        mm._current_model = "my_model.gguf"
        assert mm.get_current_model() == "my_model.gguf"


class TestUnloadModel:
    def test_unload_clears_model(self):
        mm._model = MagicMock()
        mm._current_model = "some_model.gguf"
        mm.unload_model()
        assert mm._model is None
        assert mm._current_model is None

    def test_unload_when_no_model_is_safe(self):
        mm._model = None
        mm.unload_model()  # should not raise
        assert mm._model is None


class TestLoadModel:
    def test_load_nonexistent_file_calls_on_complete_false(self, tmp_path):
        os.makedirs(mm.MODELS_DIR, exist_ok=True)
        results = []
        mm.load_model("nonexistent.gguf",
                      on_complete=lambda ok, msg: results.append((ok, msg)))
        time.sleep(0.5)
        assert len(results) == 1
        ok, msg = results[0]
        assert ok is False
        assert msg  # error message is present

    def test_load_without_llama_calls_on_complete_false(self, tmp_path):
        os.makedirs(mm.MODELS_DIR, exist_ok=True)
        model_path = os.path.join(mm.MODELS_DIR, "fake.gguf")
        open(model_path, "w").close()

        with patch.object(mm, "LLAMA_AVAILABLE", False):
            results = []
            mm.load_model("fake.gguf",
                          on_complete=lambda ok, msg: results.append((ok, msg)))
            time.sleep(0.5)
        assert len(results) == 1
        ok, msg = results[0]
        assert ok is False
