"""配置模块测试"""
import os
import tempfile
import pytest
from pathlib import Path


class TestConfig:
    """配置模块测试"""

    def test_is_configured_without_key(self, monkeypatch):
        """测试未配置时返回 False"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "")
        # 需要重新导入以获取新的环境变量
        import importlib
        import app.config as config_module
        importlib.reload(config_module)
        assert config_module.is_configured() is False

    def test_is_configured_with_placeholder(self, monkeypatch):
        """测试占位符 key 时返回 False"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "your_api_key_here")
        import importlib
        import app.config as config_module
        importlib.reload(config_module)
        assert config_module.is_configured() is False

    def test_is_configured_with_valid_key(self, monkeypatch):
        """测试有效 key 时返回 True"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-valid-api-key")
        import importlib
        import app.config as config_module
        importlib.reload(config_module)
        assert config_module.is_configured() is True


class TestSaveConfig:
    """save_config 函数测试"""

    def test_save_config_creates_file(self, temp_dir, monkeypatch):
        """测试保存配置创建文件"""
        # 临时修改配置目录
        env_file = Path(temp_dir) / ".env"

        import app.config as config_module
        monkeypatch.setattr(config_module, 'ENV_FILE', env_file)

        config_module.save_config("sk-test-key", "https://api.test.com", "test-model")

        assert env_file.exists()
        content = env_file.read_text()
        assert "sk-test-key" in content
        assert "https://api.test.com" in content
        assert "test-model" in content

    def test_save_config_sets_permissions(self, temp_dir, monkeypatch):
        """测试保存配置设置正确的文件权限"""
        import sys
        if sys.platform == 'win32':
            pytest.skip("权限测试在 Windows 上不适用")

        env_file = Path(temp_dir) / ".env"

        import app.config as config_module
        monkeypatch.setattr(config_module, 'ENV_FILE', env_file)

        config_module.save_config("sk-test-key")

        # 检查文件权限是否为 0o600
        file_mode = env_file.stat().st_mode & 0o777
        assert file_mode == 0o600


class TestInvoiceCategories:
    """发票分类常量测试"""

    def test_categories_exist(self):
        """测试所有必要的分类都存在"""
        from app.config import INVOICE_CATEGORIES

        expected_types = ["taxi", "train", "flight", "hotel", "meal", "other"]
        for type_key in expected_types:
            assert type_key in INVOICE_CATEGORIES

    def test_category_keywords_exist(self):
        """测试分类关键词存在"""
        from app.config import CATEGORY_KEYWORDS

        assert "taxi" in CATEGORY_KEYWORDS
        assert "train" in CATEGORY_KEYWORDS
        assert "hotel" in CATEGORY_KEYWORDS
        assert "meal" in CATEGORY_KEYWORDS
