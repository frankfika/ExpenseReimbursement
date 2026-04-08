"""配置管理模块测试"""
import json
import pytest
from pathlib import Path


class TestSettingsManager:
    """SettingsManager 测试"""

    def test_load_default_settings(self, temp_dir):
        """测试加载默认配置"""
        from app.settings import SettingsManager, AppSettings

        manager = SettingsManager()
        settings = manager.load()

        assert isinstance(settings, AppSettings)
        assert settings.api.base_url == "https://api.siliconflow.cn"
        assert settings.processing.max_image_size == 1920

    def test_create_default_config(self, temp_dir):
        """测试创建默认配置文件"""
        from app.settings import SettingsManager

        manager = SettingsManager()
        manager.config_dir = Path(temp_dir)
        manager.yaml_path = Path(temp_dir) / "config.yaml"

        config_path = manager.create_default_config()

        assert config_path != ""
        assert Path(config_path).exists()

    def test_save_and_load_json(self, temp_dir):
        """测试保存和加载 JSON 配置"""
        from app.settings import SettingsManager

        manager = SettingsManager()
        manager.config_dir = Path(temp_dir)
        manager.yaml_path = Path(temp_dir) / "config.yaml"
        manager.json_path = Path(temp_dir) / "config.json"

        # 修改配置
        manager.settings.api.api_key = "test_key_123"
        manager.settings.processing.max_image_size = 1024

        # 保存为 JSON
        assert manager.save(format="json") is True
        assert manager.json_path.exists()

        # 重新加载
        new_manager = SettingsManager()
        new_manager.config_dir = Path(temp_dir)
        new_manager.yaml_path = Path(temp_dir) / "config.yaml"
        new_manager.json_path = Path(temp_dir) / "config.json"

        settings = new_manager.load()
        assert settings.api.api_key == "test_key_123"
        assert settings.processing.max_image_size == 1024


class TestReportConfig:
    """ReportConfig 测试"""

    def test_default_report_config(self):
        """测试默认报表配置"""
        from app.report import ReportConfig

        config = ReportConfig()

        assert config.company_name == ""
        assert config.department == ""
        assert config.include_charts is True
        assert config.currency_symbol == "¥"

    def test_custom_report_config(self):
        """测试自定义报表配置"""
        from app.report import ReportConfig

        config = ReportConfig(
            company_name="测试公司",
            department="技术部",
            submitter="张三",
            include_charts=False
        )

        assert config.company_name == "测试公司"
        assert config.department == "技术部"
        assert config.submitter == "张三"
        assert config.include_charts is False


class TestAppSettings:
    """AppSettings 测试"""

    def test_settings_structure(self):
        """测试配置结构"""
        from app.settings import AppSettings, APIConfig, ProcessingConfig

        settings = AppSettings()

        # 验证各个配置对象存在
        assert hasattr(settings, 'api')
        assert hasattr(settings, 'processing')
        assert hasattr(settings, 'classification')
        assert hasattr(settings, 'report')

        # 验证默认值
        assert settings.api.max_retries == 3
        assert settings.processing.jpeg_quality == 85

    def test_classification_categories(self):
        """测试分类配置包含所有新分类"""
        from app.settings import ClassificationConfig

        config = ClassificationConfig()

        assert "taxi" in config.categories
        assert "parking" in config.categories
        assert "fuel" in config.categories
        assert "office" in config.categories
        assert "telecom" in config.categories
        assert "express" in config.categories
        assert "medical" in config.categories
        assert "entertainment" in config.categories
