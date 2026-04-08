"""文件组织模块测试"""
import os
import pytest
from pathlib import Path


class TestFileOrganizer:
    """FileOrganizer 类测试"""

    def test_init_creates_directories(self, temp_dir):
        """测试初始化扫描出差时间段目录"""
        from app.organizer import FileOrganizer

        # 创建一些出差时间段文件夹
        (Path(temp_dir) / "深圳出差3.15-3.18").mkdir()
        (Path(temp_dir) / "北京出差4.1").mkdir()

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        # 验证出差时间段被正确识别
        assert len(organizer.trips) == 2

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
        # 确保类型相同
        sample_invoice_info.type = "hotel"
        sample_voucher_info.type = "hotel"

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score >= 10  # 订单号匹配应该得到高分

    def test_partial_order_number_match(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试部分订单号匹配"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        sample_invoice_info.order_number = "ORDER123456"
        sample_voucher_info.order_number = "ORDER123"
        # 确保类型相同
        sample_invoice_info.type = "hotel"
        sample_voucher_info.type = "hotel"

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score >= 5  # 部分订单号匹配应该得到一定分数

    def test_amount_match_adds_score(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试金额匹配增加分数"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        sample_invoice_info.order_number = ""
        sample_voucher_info.order_number = ""
        sample_invoice_info.amount = 100.0
        sample_voucher_info.amount = 100.0
        # 确保类型相同
        sample_invoice_info.type = "hotel"
        sample_voucher_info.type = "hotel"

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score >= 3  # 金额完全匹配应该得到分数

    def test_amount_with_tax_match(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试含税金额匹配"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        sample_invoice_info.order_number = ""
        sample_voucher_info.order_number = ""
        # 凭证金额不含税，发票金额含税（13%税率）
        sample_invoice_info.amount = 113.0
        sample_voucher_info.amount = 100.0
        # 确保类型相同
        sample_invoice_info.type = "hotel"
        sample_voucher_info.type = "hotel"

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score >= 2  # 考虑含税后的匹配应该得到分数

    def test_type_match_adds_score(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试类型匹配增加分数"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        sample_invoice_info.type = "hotel"
        sample_voucher_info.type = "hotel"
        # 清空其他匹配条件，只保留类型
        sample_invoice_info.order_number = ""
        sample_voucher_info.order_number = ""
        sample_invoice_info.amount = 0
        sample_voucher_info.amount = 0

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score >= 1  # 类型匹配应该增加分数

    def test_different_type_no_match(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试不同类型不匹配"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        sample_invoice_info.type = "hotel"
        sample_voucher_info.type = "flight"

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score == 0  # 不同类型应该直接返回0

    def test_date_match_within_3_days(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试3天内日期匹配"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        # 确保类型相同，否则类型不兼容直接返回0
        sample_invoice_info.type = "hotel"
        sample_voucher_info.type = "hotel"
        sample_invoice_info.service_date = "2024-01-15"
        sample_voucher_info.service_date = "2024-01-17"  # 相差2天

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score >= 1  # 3天内日期匹配应该得到分数

    def test_merchant_similarity_match(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试商家相似度匹配"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        # 确保类型相同
        sample_invoice_info.type = "taxi"
        sample_voucher_info.type = "taxi"
        # 清空订单号，只测试商家匹配
        sample_invoice_info.order_number = ""
        sample_voucher_info.order_number = ""

        sample_invoice_info.merchant = "滴滴出行科技有限公司"
        sample_voucher_info.merchant = "滴滴出行"

        score = organizer._calculate_match_score(sample_voucher_info, sample_invoice_info)
        assert score >= 2  # 商家相似应该得到分数


class TestMerchantSimilarity:
    """商家相似度测试"""

    def test_exact_match(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试商家完全匹配"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        sample_invoice_info.merchant = "滴滴"
        sample_voucher_info.merchant = "滴滴"

        score = organizer._calculate_merchant_similarity(sample_voucher_info, sample_invoice_info)
        assert score >= 4

    def test_string_similarity(self, temp_dir):
        """测试字符串相似度计算"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)

        # 测试完全相同的字符串
        assert organizer._string_similarity("滴滴", "滴滴") == 1.0
        # 测试完全不同的字符串
        assert organizer._string_similarity("abc", "xyz") == 0.0
        # 测试部分相似的字符串
        sim = organizer._string_similarity("滴滴出行", "滴滴打车")
        assert 0 < sim < 1  # 部分相似应该在0和1之间


class TestTripSimilarity:
    """行程相似度测试"""

    def test_trip_exact_match(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试行程完全匹配"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)
        sample_invoice_info.type = "flight"
        sample_voucher_info.type = "flight"

        sample_invoice_info.description = "北京-上海"
        sample_voucher_info.description = "北京-上海"

        score = organizer._calculate_trip_similarity(sample_voucher_info, sample_invoice_info)
        assert score >= 3

    def test_trip_origin_match(self, temp_dir, sample_invoice_info, sample_voucher_info):
        """测试行程起点匹配"""
        from app.organizer import FileOrganizer

        organizer = FileOrganizer(temp_dir, copy_mode=True)
        sample_invoice_info.type = "train"
        sample_voucher_info.type = "train"

        sample_invoice_info.description = "北京-广州"
        sample_voucher_info.description = "北京-深圳"

        score = organizer._calculate_trip_similarity(sample_voucher_info, sample_invoice_info)
        assert score >= 2  # 起点相同应该得到分数


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


class TestNewCategories:
    """新发票类型分类测试"""

    def test_parking_category_keywords(self):
        """测试停车费分类关键词"""
        from app.config import CATEGORY_KEYWORDS

        assert "停车" in CATEGORY_KEYWORDS["parking"]
        assert "停车费" in CATEGORY_KEYWORDS["parking"]

    def test_fuel_category_keywords(self):
        """测试加油费分类关键词"""
        from app.config import CATEGORY_KEYWORDS

        assert "加油" in CATEGORY_KEYWORDS["fuel"]
        assert "中石油" in CATEGORY_KEYWORDS["fuel"]

    def test_office_category_keywords(self):
        """测试办公用品分类关键词"""
        from app.config import CATEGORY_KEYWORDS

        assert "办公" in CATEGORY_KEYWORDS["office"]
        assert "文具" in CATEGORY_KEYWORDS["office"]

    def test_all_categories_in_config(self):
        """测试所有分类都在配置中"""
        from app.config import INVOICE_CATEGORIES

        assert "parking" in INVOICE_CATEGORIES
        assert "fuel" in INVOICE_CATEGORIES
        assert "office" in INVOICE_CATEGORIES
        assert "telecom" in INVOICE_CATEGORIES
        assert "express" in INVOICE_CATEGORIES
        assert "medical" in INVOICE_CATEGORIES
        assert "entertainment" in INVOICE_CATEGORIES
