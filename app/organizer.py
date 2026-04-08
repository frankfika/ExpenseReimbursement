"""文件分类和配对模块 - 按出差时间段归档"""
import os
import shutil
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from .config import INVOICE_CATEGORIES, PENDING_CATEGORY, get_current_year
from .analyzer import InvoiceInfo


def _infer_year(month: int) -> int:
    """根据月份智能推断年份

    规则：
    - 如果月份在当前月的前后3个月内，使用当前年份
    - 如果月份比当前月晚6个月以上，使用去年
    - 如果月份比当前月早6个月以上，使用明年
    """
    current_year = get_current_year()
    current_month = datetime.now().month

    month_diff = month - current_month

    if abs(month_diff) <= 3:
        return current_year
    elif month_diff > 6:
        return current_year - 1
    elif month_diff < -6:
        return current_year + 1
    else:
        return current_year


def parse_trip_folders(output_dir: Path) -> List[Tuple[str, datetime, datetime]]:
    """
    解析输出目录中的出差时间段文件夹

    支持的格式：
    - 深圳广州出差3.3-3.6
    - 南沙出差3.15 - 3.20
    - 新加坡来访3.11
    - 2024-01-01 至 2024-01-05

    返回: [(文件夹名, 开始日期, 结束日期), ...]
    """
    trips = []

    if not output_dir.exists():
        return trips

    for folder in output_dir.iterdir():
        if not folder.is_dir():
            continue

        folder_name = folder.name

        # 尝试匹配各种日期格式
        # 格式1: 3.3-3.6 或 3.15 - 3.20
        match = re.search(r'(\d{1,2})\.\s*(\d{1,2})\s*[-至]\s*(\d{1,2})\.\s*(\d{1,2})', folder_name)
        if match:
            start_month, start_day = int(match.group(1)), int(match.group(2))
            end_month, end_day = int(match.group(3)), int(match.group(4))
            start_year = _infer_year(start_month)
            end_year = start_year if start_month <= end_month else _infer_year(end_month)
            start_date = datetime(start_year, start_month, start_day)
            end_date = datetime(end_year, end_month, end_day)
            trips.append((folder_name, start_date, end_date))
            continue

        # 格式2: 3.11 (单日)
        match = re.search(r'(\d{1,2})\.(\d{1,2})', folder_name)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            year = _infer_year(month)
            date = datetime(year, month, day)
            trips.append((folder_name, date, date))
            continue

        # 格式3: 2024-01-01 至 2024-01-05
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})\s*[-至]\s*(\d{4})-(\d{2})-(\d{2})', folder_name)
        if match:
            start_date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            end_date = datetime(int(match.group(4)), int(match.group(5)), int(match.group(6)))
            trips.append((folder_name, start_date, end_date))
            continue

        # 格式4: 2024-01-01 (单日)
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', folder_name)
        if match:
            date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            trips.append((folder_name, date, date))

    # 按开始日期排序
    trips.sort(key=lambda x: x[1])
    return trips


def find_trip_folder(invoice_date: str, trips: List[Tuple[str, datetime, datetime]]) -> Optional[str]:
    """
    根据发票日期找到对应的出差文件夹

    Args:
        invoice_date: 发票日期 (YYYY-MM-DD 格式)
        trips: 出差时间段列表

    Returns:
        对应的出差文件夹名，如果没有找到则返回 None
    """
    if not invoice_date:
        return None

    try:
        date = datetime.strptime(invoice_date, "%Y-%m-%d")
    except ValueError:
        return None

    for folder_name, start_date, end_date in trips:
        if start_date <= date <= end_date:
            return folder_name

    return None


class FileOrganizer:
    """文件组织器 - 负责按出差时间段分类、配对、移动/复制文件"""

    def __init__(self, output_dir: str, copy_mode: bool = False):
        self.output_dir = Path(output_dir)
        self.copy_mode = copy_mode  # True=复制, False=移动
        # 解析已有的出差文件夹
        self.trips = parse_trip_folders(self.output_dir)
        print(f"\n📅 发现 {len(self.trips)} 个出差时间段:")
        for name, start, end in self.trips:
            if start == end:
                print(f"  • {name}: {start.strftime('%m月%d日')}")
            else:
                print(f"  • {name}: {start.strftime('%m月%d日')} - {end.strftime('%m月%d日')}")

    def organize(self, invoice_infos: List[InvoiceInfo]) -> Dict[str, List[InvoiceInfo]]:
        """
        组织所有发票文件 - 按出差时间段归档

        Args:
            invoice_infos: 发票信息列表

        Returns:
            分类后的字典 {类别: [发票信息列表]}
        """
        # 1. 配对凭证和发票
        paired_groups = self._pair_vouchers_and_invoices(invoice_infos)

        # 2. 按出差时间段和类型组织文件
        categorized = defaultdict(list)

        for group in paired_groups:
            # 获取配对组的实际消费日期（优先从凭证/行程单获取）
            group_date = ""
            has_voucher = False
            for info in group:
                if not info.is_invoice:  # 凭证/行程单
                    group_date = info.get_actual_date()
                    has_voucher = True
                    break
            # 如果没有凭证，用发票的实际消费日期
            if not group_date:
                for info in group:
                    group_date = info.get_actual_date()
                    if group_date:
                        break

            # 判断是否需要放到"待确认"目录
            needs_confirmation = False
            if len(group) == 1 and group[0].is_invoice:
                if not group[0].service_date:
                    needs_confirmation = True

            # 获取类型分类
            if needs_confirmation:
                category_name = PENDING_CATEGORY
            else:
                category = self._get_category(group)
                category_name = INVOICE_CATEGORIES.get(category, "其他")

            # 找到对应的出差文件夹
            trip_folder = find_trip_folder(group_date, self.trips)

            if trip_folder:
                # 在出差文件夹内部按类型分类
                target_folder = self.output_dir / trip_folder / category_name
                trip_name = trip_folder
            else:
                # 未匹配到任何出差时间段
                # 餐饮票放到根目录，其他放到未分类
                if category_name == "餐费":
                    target_folder = self.output_dir / category_name
                    trip_name = "餐费"
                    print(f"  🍽️  餐饮票日期 {group_date} 未匹配出差时间段，放到根目录 {category_name}")
                else:
                    target_folder = self.output_dir / "未分类" / category_name
                    trip_name = "未分类"
                    print(f"  ⚠️  日期 {group_date} 未匹配出差时间段，放到未分类/{category_name}")

            # 创建子文件夹名称（按日期）
            folder_name = self._generate_folder_name(group)
            target_folder = target_folder / folder_name

            # 确保文件夹存在
            target_folder.mkdir(parents=True, exist_ok=True)

            # 移动文件
            for idx, info in enumerate(group, 1):
                new_filename = self._generate_filename(info, idx, len(group), group_date)
                target_path = target_folder / new_filename

                # 移动文件
                self._move_file(info.file_path, target_path)

                # 更新文件路径
                info.file_path = str(target_path)
                categorized[category_name].append(info)

        return dict(categorized)

    def _pair_vouchers_and_invoices(self, invoice_infos: List[InvoiceInfo]) -> List[List[InvoiceInfo]]:
        """
        配对凭证和发票

        规则：
        1. 同一平台/商家
        2. 日期相同或相近（±1天）
        3. 金额相同或相近（±1%）
        """
        # 分离发票和凭证，保留索引用于追踪
        invoices = [(idx, i) for idx, i in enumerate(invoice_infos) if i.is_invoice]
        vouchers = [(idx, i) for idx, i in enumerate(invoice_infos) if not i.is_invoice]

        paired_groups = []
        used_invoice_indices = set()

        # 尝试配对
        for voucher_idx, voucher in vouchers:
            best_match = None
            best_match_idx = None
            best_score = 0

            for invoice_idx, invoice in invoices:
                if invoice_idx in used_invoice_indices:
                    continue

                score = self._calculate_match_score(voucher, invoice)
                if score > best_score and score >= 2:  # 至少匹配2个条件
                    best_score = score
                    best_match = invoice
                    best_match_idx = invoice_idx

            if best_match:
                # 找到配对
                paired_groups.append([voucher, best_match])
                used_invoice_indices.add(best_match_idx)
            else:
                # 未配对的凭证单独一组
                paired_groups.append([voucher])

        # 未配对的发票单独一组
        for invoice_idx, invoice in invoices:
            if invoice_idx not in used_invoice_indices:
                paired_groups.append([invoice])

        return paired_groups

    def _calculate_match_score(self, voucher: InvoiceInfo, invoice: InvoiceInfo) -> int:
        """
        计算凭证和发票的匹配分数（优化版）

        配对逻辑：以凭证/行程单的实际消费日期为准（因为发票可能是后补开的）
        注意：同类发票（如多个打车票）不应互相配对，应该各自独立
        不同类型的发票和凭证（如酒店凭证+机票发票）也不应配对
        """
        score = 0

        # 0. 类型兼容性检查 - 不同类型不应该配对
        if voucher.type != invoice.type:
            return 0  # 酒店凭证不能和机票发票配对

        # 1. 同类型发票检查 - 如果两个都是发票且类型相同，不应该配对
        if voucher.is_invoice and invoice.is_invoice and voucher.type == invoice.type:
            if not (voucher.order_number and invoice.order_number and voucher.order_number == invoice.order_number):
                return 0

        # 2. 订单号匹配（最高优先级）
        if voucher.order_number and invoice.order_number:
            # 完全匹配
            if voucher.order_number == invoice.order_number:
                score += 15  # 订单号完全匹配，最高优先级
            # 部分匹配（包含关系）
            elif voucher.order_number in invoice.order_number or invoice.order_number in voucher.order_number:
                score += 8

        # 3. 商家相似度匹配（使用模糊匹配）
        merchant_score = self._calculate_merchant_similarity(voucher, invoice)
        score += merchant_score

        # 4. 日期匹配 - 以实际消费日期为准
        voucher_date = voucher.get_actual_date()
        invoice_service_date = invoice.service_date or invoice.date

        if voucher_date and invoice_service_date:
            try:
                v_date = datetime.strptime(voucher_date, "%Y-%m-%d")
                i_date = datetime.strptime(invoice_service_date, "%Y-%m-%d")
                days_diff = abs((v_date - i_date).days)
                if days_diff == 0:
                    score += 3  # 日期完全匹配
                elif days_diff <= 1:
                    score += 2  # 相差1天
                elif days_diff <= 3:
                    score += 1  # 相差3天内（可能是开票延迟）
            except ValueError:
                pass

        # 5. 金额匹配（考虑开票金额可能含税）
        if voucher.amount > 0 and invoice.amount > 0:
            # 计算含税后的可能金额（假设税率13%）
            voucher_with_tax = voucher.amount * 1.13
            invoice_with_tax = invoice.amount * 1.13

            # 原始金额匹配
            diff = abs(voucher.amount - invoice.amount)
            max_amount = max(voucher.amount, invoice.amount)

            if diff <= max_amount * 0.005:  # 0.5% 误差
                score += 5
            elif diff <= max_amount * 0.01:  # 1% 误差
                score += 3
            elif diff <= max_amount * 0.05:  # 5% 误差
                score += 1
            # 考虑含税后的匹配
            elif abs(voucher_with_tax - invoice.amount) <= invoice.amount * 0.01:
                score += 4  # 发票含了税
            elif abs(invoice_with_tax - voucher.amount) <= voucher.amount * 0.01:
                score += 4  # 凭证含了税

        # 6. 类型匹配
        if voucher.type == invoice.type:
            score += 2

        # 7. 行程信息匹配（针对交通类）
        if voucher.type in ["train", "flight", "taxi"]:
            trip_score = self._calculate_trip_similarity(voucher, invoice)
            score += trip_score

        # 8. 描述相似度匹配（用于辅助判断）
        if voucher.description and invoice.description:
            desc_sim = self._string_similarity(voucher.description, invoice.description)
            if desc_sim > 0.8:
                score += 2
            elif desc_sim > 0.5:
                score += 1

        return score

    def _calculate_merchant_similarity(self, voucher: InvoiceInfo, invoice: InvoiceInfo) -> int:
        """计算商家相似度得分"""
        score = 0

        # 商家名称标准化比较
        v_merchants = [
            self._normalize_merchant(voucher.subtype),
            self._normalize_merchant(voucher.merchant)
        ]
        i_merchants = [
            self._normalize_merchant(invoice.subtype),
            self._normalize_merchant(invoice.merchant)
        ]

        for v_m in v_merchants:
            if not v_m:
                continue
            for i_m in i_merchants:
                if not i_m:
                    continue
                # 完全匹配
                if v_m == i_m:
                    score += 4
                    return score
                # 包含关系
                if v_m in i_m or i_m in v_m:
                    score += 2
                # 相似度检查（简单实现）
                elif self._string_similarity(v_m, i_m) > 0.7:
                    score += 2

        return min(score, 4)  # 最高4分

    def _calculate_trip_similarity(self, voucher: InvoiceInfo, invoice: InvoiceInfo) -> int:
        """计算行程相似度（针对交通发票）"""
        score = 0

        # 从描述中提取行程信息
        v_trip = self._extract_trip_info(voucher.description) if voucher.description else ""
        i_trip = self._extract_trip_info(invoice.description) if invoice.description else ""

        if v_trip and i_trip:
            # 行程信息完全匹配
            if v_trip == i_trip:
                score += 3
            # 起点或终点匹配
            elif v_trip.split('-')[0] == i_trip.split('-')[0]:  # 起点相同
                score += 2
            elif len(v_trip.split('-')) > 1 and len(i_trip.split('-')) > 1:
                if v_trip.split('-')[1] == i_trip.split('-')[1]:  # 终点相同
                    score += 2

        # 航班号/车次号匹配
        if voucher.invoice_number and invoice.invoice_number:
            if voucher.invoice_number == invoice.invoice_number:
                score += 5

        return score

    def _string_similarity(self, s1: str, s2: str) -> float:
        """计算两个字符串的相似度（0-1）"""
        if not s1 or not s2:
            return 0.0

        # 使用简单的 Jaccard 相似度
        set1 = set(s1.lower())
        set2 = set(s2.lower())

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def _normalize_merchant(self, name: str) -> str:
        """标准化商家名称"""
        if not name:
            return ""
        # 移除常见后缀和特殊字符
        name = re.sub(r'[（）()【】\[\]有限公司科技股份]', '', name)
        return name.strip().lower()

    def _get_category(self, group: List[InvoiceInfo]) -> str:
        """获取组的分类"""
        # 优先使用发票的分类
        for info in group:
            if info.is_invoice and info.type != "other":
                return info.type

        # 其次使用凭证的分类
        for info in group:
            if info.type != "other":
                return info.type

        return "other"

    def _generate_folder_name(self, group: List[InvoiceInfo]) -> str:
        """生成文件夹名称 - 以实际消费日期为准"""
        # 优先使用凭证/行程单的信息（因为它有准确的消费日期）
        # 其次使用发票的信息
        voucher_info = None
        invoice_info = None

        for info in group:
            if info.is_invoice:
                invoice_info = info
            else:
                voucher_info = info

        # 日期优先用凭证的实际消费日期
        actual_date = ""
        if voucher_info:
            actual_date = voucher_info.get_actual_date()
        if not actual_date and invoice_info:
            actual_date = invoice_info.get_actual_date()
        if not actual_date:
            actual_date = datetime.now().strftime("%Y-%m-%d")

        # 金额和商家优先用发票的（更正式）
        main_info = invoice_info or voucher_info or group[0]

        # 构建文件夹名
        parts = []

        # 日期（实际消费日期）
        parts.append(actual_date)

        # 商家/平台
        merchant = main_info.subtype or main_info.merchant or "未知"
        merchant = self._sanitize_filename(merchant)[:20]  # 限制长度
        parts.append(merchant)

        # 金额
        if main_info.amount > 0:
            parts.append(f"{main_info.amount:.2f}元")

        return "_".join(parts)

    def _generate_filename(self, info: InvoiceInfo, index: int, total: int, group_date: str = "") -> str:
        """
        生成明确的文件名
        格式: [序号_]日期_类型_商家_金额_描述.扩展名
        例如: 2024-01-15_发票_滴滴出行_35.00元_北京-上海.pdf

        Args:
            info: 发票信息
            index: 在配对组中的序号
            total: 配对组总数
            group_date: 配对组的实际消费日期（优先使用）
        """
        original_path = Path(info.file_path)
        suffix = original_path.suffix

        parts = []

        # 序号（如果是配对组）
        if total > 1:
            parts.append(f"{index:02d}")

        # 日期 - 优先使用配对组的日期（来自凭证/行程单），其次用自己的实际消费日期
        actual_date = group_date or info.get_actual_date()
        if actual_date:
            parts.append(actual_date)

        # 发票/凭证标识
        doc_type = "发票" if info.is_invoice else "凭证"
        parts.append(doc_type)

        # 商家/平台
        merchant = info.subtype or info.merchant
        if merchant:
            merchant = self._sanitize_filename(merchant)[:12]
            parts.append(merchant)

        # 金额
        if info.amount > 0:
            parts.append(f"{info.amount:.2f}元")

        # 行程描述（从 description 中提取有用信息）
        if info.description:
            # 提取行程信息（如 北京-上海、xxx到xxx）
            desc = self._extract_trip_info(info.description)
            if desc:
                desc = self._sanitize_filename(desc)[:15]
                parts.append(desc)

        filename = "_".join(parts) if parts else "未知文件"
        return f"{filename}{suffix}"

    def _extract_trip_info(self, description: str) -> str:
        """从描述中提取行程信息"""
        if not description:
            return ""

        # 尝试匹配常见的行程描述模式
        patterns = [
            r'从(.+?)到(.+?)(?:的|$)',  # 从A到B
            r'(.+?)[至到\-→](.+?)(?:的|$)',  # A至B, A到B, A-B, A→B
            r'(.+?)出发',  # A出发
        ]

        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    return f"{groups[0].strip()}-{groups[1].strip()}"
                elif len(groups) == 1:
                    return groups[0].strip()

        # 如果没有匹配到行程，返回简短描述
        desc = description[:20] if len(description) > 20 else description
        return desc

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除文件名非法字符
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        # 移除多余空格
        name = re.sub(r'\s+', ' ', name).strip()
        return name

    def _move_file(self, src: str, dst: Path):
        """移动或复制文件"""
        src_path = Path(src)
        action = "复制" if self.copy_mode else "移动"
        # 使用 try/except 而不是预检查（避免 TOCTOU 竞态）
        try:
            # 尝试直接操作
            if self.copy_mode:
                shutil.copy2(str(src_path), str(dst))
            else:
                shutil.move(str(src_path), str(dst))
        except FileExistsError:
            # 目标已存在，添加序号
            stem = dst.stem
            suffix = dst.suffix
            counter = 1
            while dst.exists():
                dst = dst.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            if self.copy_mode:
                shutil.copy2(str(src_path), str(dst))
            else:
                shutil.move(str(src_path), str(dst))
        print(f"  {action}: {src_path.name} -> {dst.relative_to(self.output_dir)}")
