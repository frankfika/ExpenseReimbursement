"""文件组织模块测试"""
import os
import pytest
from pathlib import Path


class TestFileOrganizer:
    """FileOrganizer 类测试"""

    def test_init_creates_directories(self, temp_dir):
        """测试初始化创建分类目录"""
        from app.organizer import FileOrganizer
        from app.config import INVOICE_CATEGORIES, PENDING_CATEGORY

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        # 检查所有分类目录是否创建
        for category_name in INVOICE_CATEGORIES.values():
            category_dir = Path(temp_dir) / category_name
            assert category_dir.exists()

        # 检查待确认目录
        pending_dir = Path(temp_dir) / PENDING_CATEGORY
        assert pending_dir.exists()

    def test_sanitize_filename(self, temp_dir):
        """测试文件名清理"""
        from app.organizer import FileOrganizer
        organizer = FileOrganizer(temp_dir)

        # 测试移除非法字符
        assert organizer._sanitize_filename("test<file>name") == "testfilename"
        assert organizer._sanitize_filename("test:file/name") == "testfilename"

        # 测试保留正常字符
        assert organizer._sanitize_filename("正常文件名") == "正常文件名"

        # 测试移除多余空格
        assert organizer._sanitize_filename("test  file") == "test file"

    def test_normalize_merchant(self, temp_dir):
        """测试商家名称标准化"""
        from app.organizer import FileOrganizer
        organizer = FileOrganizer(temp_dir)

        # 测试移除后缀
        assert organizer._normalize_merchant("滴滴出行科技有限公司") == "滴滴出行"
        assert organizer._normalize_merchant("如家（北京）酒店") == "如家北京酒店"

        # 测试空值处理
        assert organizer._normalize_merchant("") == ""
        assert organizer._normalize_merchant(None) == ""


class TestPairVouchersAndInvoices:
    """配对凭证和发票测试"""

    def test_pair_by_order_number(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试通过订单号配对"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        # 设置相同的订单号
        sample_invoice_info.order_number = "ORDER123"
        sample_voucher_info.order_number = "ORDER123"

        pairs = organizer._pair_vouchers_and_invoices([sample_invoice_info, sample_voucher_info])

        # 应该配对在一起
        assert len(pairs) == 1
        assert len(pairs[0]) == 2

    def test_pair_by_amount_and_date(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试通过金额和日期配对"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        # 清空订单号，使用金额和日期配对
        sample_invoice_info.order_number = ""
        sample_voucher_info.order_number = ""
        sample_invoice_info.amount = 100.0
        sample_voucher_info.amount = 100.0

        pairs = organizer._pair_vouchers_and_invoices([sample_invoice_info, sample_voucher_info])

        assert len(pairs) == 1
        assert len(pairs[0]) == 2

    def test_unpaired_invoice_standalone(self, temp_dir, sample_invoice_info):
        """测试未配对的发票独立一组"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        pairs = organizer._pair_vouchers_and_invoices([sample_invoice_info])

        assert len(pairs) == 1
        assert len(pairs[0]) == 1
        assert pairs[0][0].is_invoice is True


class TestCalculateMatchScore:
    """匹配分数计算测试"""

    def test_order_number_match_high_score(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试订单号匹配得高分"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        sample_invoice_info.order_number = "ORDER123"
        sample_voucher_info.order_number = "ORDER123"

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score >= 10  # 订单号匹配应该得到高分

    def test_amount_match_adds_score(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试金额匹配增加分数"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        sample_invoice_info.order_number = ""
        sample_voucher_info.order_number = ""
        sample_invoice_info.amount = 100.0
        sample_voucher_info.amount = 100.0

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score >= 3  # 金额完全匹配应该得到分数

    def test_type_match_adds_score(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试类型匹配增加分数"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        sample_invoice_info.type = "taxi"
        sample_voucher_info.type = "taxi"

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score >= 1  # 类型匹配应该增加分数


class TestGenerateFilename:
    """文件名生成测试"""

    def test_filename_includes_date(self, temp_dir, sample_invoice_info):
        """测试文件名包含日期"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)
        sample_invoice_info.file_path = "/tmp/test.pdf"

        filename = organizer._generate_filename(sample_invoice_info, 1, 1, "2024-01-15")

        assert "2024-01-15" in filename

    def test_filename_includes_type(self, temp_dir, sample_invoice_info):
        """测试文件名包含类型标识"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)
        sample_invoice_info.file_path = "/tmp/test.pdf"

        filename = organizer._generate_filename(sample_invoice_info, 1, 1)

        assert "发票" in filename

    def test_filename_includes_amount(self, temp_dir, sample_invoice_info):
        """测试文件名包含金额"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)
        sample_invoice_info.file_path = "/tmp/test.pdf"
        sample_invoice_info.amount = 35.50

        filename = organizer._generate_filename(sample_invoice_info, 1, 1)

        assert "35.50元" in filename
