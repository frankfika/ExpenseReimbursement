"""配置管理模块 - 支持 YAML/JSON 配置文件"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from .config import get_config_dir


@dataclass
class APIConfig:
    """API 配置"""
    api_key: str = ""
    base_url: str = "https://api.siliconflow.cn"
    text_model: str = "deepseek-ai/DeepSeek-V3"
    vision_model: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    max_retries: int = 3
    timeout: int = 60


@dataclass
class ProcessingConfig:
    """处理配置"""
    max_image_size: int = 1920
    jpeg_quality: int = 85
    confidence_threshold: float = 0.6
    enable_ocr: bool = True
    enable_vision: bool = True
    copy_mode: bool = False


@dataclass
class ClassificationConfig:
    """分类配置"""
    categories: Dict[str, str] = field(default_factory=lambda: {
        "taxi": "打车票",
        "train": "火车飞机票",
        "flight": "火车飞机票",
        "hotel": "住宿费",
        "meal": "餐费",
        "parking": "停车费",
        "fuel": "加油费",
        "office": "办公用品",
        "telecom": "通讯费",
        "express": "快递费",
        "medical": "医疗费用",
        "entertainment": "业务招待",
        "other": "其他"
    })
    keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        "taxi": ["滴滴", "高德", "美团打车", "曹操", "首汽", "出租车", "网约车"],
        "train": ["12306", "火车票", "高铁", "动车", "铁路"],
        "flight": ["航空", "机票", "登机牌", "航班", "飞机"],
        "hotel": ["酒店", "宾馆", "住宿", "客房", "民宿"],
        "meal": ["餐饮", "餐厅", "饭店", "美团", "饿了么", "外卖"]
    })


@dataclass
class ReportConfig:
    """报表配置"""
    template: str = "default"
    include_charts: bool = True
    currency_symbol: str = "¥"
    date_format: str = "%Y-%m-%d"
    company_name: str = ""
    department: str = ""


@dataclass
class AppSettings:
    """应用配置"""
    api: APIConfig = field(default_factory=APIConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    classification: ClassificationConfig = field(default_factory=ClassificationConfig)
    report: ReportConfig = field(default_factory=ReportConfig)


class SettingsManager:
    """配置管理器"""

    def __init__(self):
        self.config_dir = get_config_dir()
        self.yaml_path = self.config_dir / "config.yaml"
        self.json_path = self.config_dir / "config.json"
        self.settings = AppSettings()

    def load(self) -> AppSettings:
        """加载配置，优先使用 YAML，其次 JSON"""
        if self.yaml_path.exists() and YAML_AVAILABLE:
            return self._load_yaml()
        elif self.json_path.exists():
            return self._load_json()
        return self.settings

    def _load_yaml(self) -> AppSettings:
        """从 YAML 加载配置"""
        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return self._dict_to_settings(data)
        except Exception as e:
            print(f"⚠️  加载 YAML 配置失败: {e}")
            return self.settings

    def _load_json(self) -> AppSettings:
        """从 JSON 加载配置"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._dict_to_settings(data)
        except Exception as e:
            print(f"⚠️  加载 JSON 配置失败: {e}")
            return self.settings

    def _dict_to_settings(self, data: Dict[str, Any]) -> AppSettings:
        """将字典转换为配置对象"""
        try:
            api_config = APIConfig(**data.get('api', {}))
            processing_config = ProcessingConfig(**data.get('processing', {}))
            classification_config = ClassificationConfig(**data.get('classification', {}))
            report_config = ReportConfig(**data.get('report', {}))

            return AppSettings(
                api=api_config,
                processing=processing_config,
                classification=classification_config,
                report=report_config
            )
        except Exception as e:
            print(f"⚠️  解析配置失败: {e}")
            return self.settings

    def save(self, format: str = "yaml") -> bool:
        """保存配置"""
        data = asdict(self.settings)

        if format.lower() == "yaml" and YAML_AVAILABLE:
            return self._save_yaml(data)
        else:
            return self._save_json(data)

    def _save_yaml(self, data: Dict[str, Any]) -> bool:
        """保存为 YAML"""
        try:
            with open(self.yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            print(f"⚠️  保存 YAML 配置失败: {e}")
            return False

    def _save_json(self, data: Dict[str, Any]) -> bool:
        """保存为 JSON"""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️  保存 JSON 配置失败: {e}")
            return False

    def create_default_config(self) -> str:
        """创建默认配置文件"""
        config_content = """# 报销助手配置文件
# 修改此文件即可自定义应用行为，无需修改代码

# API 配置
api:
  api_key: ""  # 从 https://cloud.siliconflow.cn 获取
  base_url: "https://api.siliconflow.cn"
  text_model: "deepseek-ai/DeepSeek-V3"
  vision_model: "Qwen/Qwen2.5-VL-7B-Instruct"
  max_retries: 3
  timeout: 60

# 处理配置
processing:
  max_image_size: 1920  # 图片最大尺寸
  jpeg_quality: 85      # JPEG 压缩质量
  confidence_threshold: 0.6  # 置信度阈值
  enable_ocr: true      # 启用 OCR
  enable_vision: true   # 启用视觉模型
  copy_mode: false      # true=复制文件, false=移动文件

# 分类配置
classification:
  categories:
    taxi: "打车票"
    train: "火车飞机票"
    flight: "火车飞机票"
    hotel: "住宿费"
    meal: "餐费"
    parking: "停车费"
    fuel: "加油费"
    office: "办公用品"
    telecom: "通讯费"
    express: "快递费"
    medical: "医疗费用"
    entertainment: "业务招待"
    other: "其他"

# 报表配置
report:
  template: "default"
  include_charts: true
  currency_symbol: "¥"
  date_format: "%Y-%m-%d"
  company_name: ""  # 公司名称
  department: ""    # 部门名称
"""
        config_path = self.config_dir / "config.yaml"
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            return str(config_path)
        except Exception as e:
            print(f"⚠️  创建默认配置失败: {e}")
            return ""

    def update_from_env(self):
        """从环境变量更新配置（用于兼容现有 .env 配置）"""
        from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, VISION_MODEL

        if DEEPSEEK_API_KEY:
            self.settings.api.api_key = DEEPSEEK_API_KEY
        if DEEPSEEK_BASE_URL:
            self.settings.api.base_url = DEEPSEEK_BASE_URL
        if DEEPSEEK_MODEL:
            self.settings.api.text_model = DEEPSEEK_MODEL
        if VISION_MODEL:
            self.settings.api.vision_model = VISION_MODEL


# 全局配置实例
_settings_manager = None


def get_settings() -> AppSettings:
    """获取配置实例"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
        _settings_manager.load()
        _settings_manager.update_from_env()
    return _settings_manager.settings


def reload_settings() -> AppSettings:
    """重新加载配置"""
    global _settings_manager
    _settings_manager = SettingsManager()
    _settings_manager.load()
    _settings_manager.update_from_env()
    return _settings_manager.settings
