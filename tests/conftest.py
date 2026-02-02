"""Pytest 配置和共享 fixtures"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """创建临时目录用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_invoice_info():
    """创建示例发票信息"""
    from app.analyzer import InvoiceInfo
    return InvoiceInfo(
        type="taxi",
        subtype="滴滴出行",
        amount=35.50,
        date="2024-01-15",
        service_date="2024-01-15",
        merchant="滴滴出行科技有限公司",
        invoice_number="12345678901234567890",
        is_invoice=True,
        description="从北京到上海的打车费用",
        raw_text="滴滴出行 电子发票 金额：35.50元",
        file_path="/tmp/test_invoice.pdf",
        order_number="DD202401150001"
    )


@pytest.fixture
def sample_voucher_info():
    """创建示例凭证信息"""
    from app.analyzer import InvoiceInfo
    return InvoiceInfo(
        type="taxi",
        subtype="滴滴出行",
        amount=35.50,
        date="2024-01-15",
        service_date="2024-01-15",
        merchant="滴滴出行",
        invoice_number="",
        is_invoice=False,
        description="滴滴出行行程单",
        raw_text="滴滴出行 行程单 金额：35.50元",
        file_path="/tmp/test_voucher.pdf",
        order_number="DD202401150001"
    )


@pytest.fixture
def mock_env(monkeypatch):
    """Mock 环境变量"""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test_api_key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.test.com")
    monkeypatch.setenv("DEEPSEEK_MODEL", "test-model")
