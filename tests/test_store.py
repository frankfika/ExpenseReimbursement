"""Tests for app/store.py"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.store import (
    get_active_provider,
    get_providers_path,
    get_store_dir,
    load_providers_config,
)


class TestGetStoreDir:
    """测试获取存储目录"""

    def test_returns_path(self):
        result = get_store_dir()
        assert isinstance(result, Path)
        assert result == Path.home() / ".expense-helper"


class TestGetProvidersPath:
    """测试获取 providers.json 路径"""

    def test_returns_correct_path(self):
        result = get_providers_path()
        assert isinstance(result, Path)
        assert result.name == "providers.json"
        assert result.parent == Path.home() / ".expense-helper"


class TestLoadProvidersConfig:
    """测试加载 providers 配置"""

    def test_file_not_exists_returns_empty(self):
        with patch.object(Path, "exists", return_value=False):
            result = load_providers_config()
            assert result == {}

    def test_loads_valid_json(self, tmp_path):
        config_path = tmp_path / "providers.json"
        test_data = {"active_id": "provider1", "providers": [{"id": "provider1", "name": "Test"}]}
        config_path.write_text(json.dumps(test_data), encoding="utf-8")

        with patch("app.store.get_providers_path", return_value=config_path):
            result = load_providers_config()
            assert result == test_data

    def test_invalid_json_returns_empty(self, tmp_path):
        config_path = tmp_path / "providers.json"
        config_path.write_text("not valid json", encoding="utf-8")

        with patch("app.store.get_providers_path", return_value=config_path):
            result = load_providers_config()
            assert result == {}

    def test_empty_file_returns_empty(self, tmp_path):
        config_path = tmp_path / "providers.json"
        config_path.write_text("", encoding="utf-8")

        with patch("app.store.get_providers_path", return_value=config_path):
            result = load_providers_config()
            assert result == {}

    def test_os_error_returns_empty(self, tmp_path):
        config_path = tmp_path / "providers.json"
        config_path.write_text('{"test": true}', encoding="utf-8")
        config_path.chmod(0o000)  # Remove read permissions

        try:
            with patch("app.store.get_providers_path", return_value=config_path):
                result = load_providers_config()
                assert result == {}
        finally:
            config_path.chmod(0o644)


class TestGetActiveProvider:
    """测试获取当前激活的 provider"""

    def test_no_config_returns_none(self):
        with patch("app.store.load_providers_config", return_value={}):
            result = get_active_provider()
            assert result is None

    def test_active_id_matches(self):
        test_data = {
            "active_id": "p2",
            "providers": [
                {"id": "p1", "name": "Provider 1"},
                {"id": "p2", "name": "Provider 2"},
            ],
        }
        with patch("app.store.load_providers_config", return_value=test_data):
            result = get_active_provider()
            assert result == {"id": "p2", "name": "Provider 2"}

    def test_active_id_not_found_returns_first(self):
        test_data = {
            "active_id": "nonexistent",
            "providers": [
                {"id": "p1", "name": "Provider 1"},
                {"id": "p2", "name": "Provider 2"},
            ],
        }
        with patch("app.store.load_providers_config", return_value=test_data):
            result = get_active_provider()
            assert result == {"id": "p1", "name": "Provider 1"}

    def test_no_active_id_returns_first(self):
        test_data = {
            "providers": [
                {"id": "p1", "name": "Provider 1"},
            ],
        }
        with patch("app.store.load_providers_config", return_value=test_data):
            result = get_active_provider()
            assert result == {"id": "p1", "name": "Provider 1"}

    def test_empty_providers_returns_none(self):
        test_data = {"active_id": "p1", "providers": []}
        with patch("app.store.load_providers_config", return_value=test_data):
            result = get_active_provider()
            assert result is None

    def test_providers_key_missing_returns_none(self):
        test_data = {"active_id": "p1"}
        with patch("app.store.load_providers_config", return_value=test_data):
            result = get_active_provider()
            assert result is None
