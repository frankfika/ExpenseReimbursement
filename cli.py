#!/usr/bin/env python3
"""
报销助手 - 命令行交互版
使用视觉模型直接分析发票，无需本地 OCR

使用方法:
    python cli.py --input ./发票 --output ./报销结果
    python cli.py  # 交互模式
"""
import argparse
import sys
from pathlib import Path
from typing import List

from app import get_api_key, setup_wizard, is_configured, INVOICE_CATEGORIES, PENDING_CATEGORY
from app import analyze_invoice_vision, InvoiceInfo
from app import FileOrganizer, generate_report
from app.ocr import is_supported_file


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def color_print(text: str, color: str = ""):
    """带颜色打印"""
    print(f"{color}{text}{Colors.END}")


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_success(text: str):
    color_print(f"✓ {text}", Colors.GREEN)


def print_warning(text: str):
    color_print(f"⚠ {text}", Colors.YELLOW)


def print_error(text: str):
    color_print(f"✗ {text}", Colors.RED)


def print_info(text: str):
    color_print(f"ℹ {text}", Colors.BLUE)


def scan_files(input_dir: str) -> List[str]:
    """扫描目录下所有支持的文件"""
    files = []
    input_path = Path(input_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"目录不存在: {input_dir}")

    for file_path in input_path.rglob("*"):
        if file_path.is_file() and is_supported_file(str(file_path)):
            files.append(str(file_path))

    return sorted(files)


def process_invoices(files: List[str], api_key: str, show_progress: bool = True) -> List[InvoiceInfo]:
    """处理所有发票文件"""
    results = []
    total = len(files)

    for idx, file_path in enumerate(files, 1):
        filename = Path(file_path).name
        if show_progress:
            print_info(f"[{idx}/{total}] 分析: {filename}")

        try:
            info = analyze_invoice_vision(file_path, api_key)
        except Exception as e:
            print_warning(f"分析失败: {e}")
            info = InvoiceInfo(
                type="other",
                subtype="未识别",
                amount=0.0,
                date="",
                service_date="",
                merchant="",
                invoice_number="",
                is_invoice=False,
                description=f"分析失败: {str(e)}",
                raw_text="",
                file_path=file_path,
                order_number=""
            )
        results.append(info)

        if show_progress:
            category = INVOICE_CATEGORIES.get(info.type, "其他")
            doc_type = "发票" if info.is_invoice else "凭证"
            amount_str = f"¥{info.amount:.2f}" if info.amount > 0 else "金额未知"
            date_str = info.service_date or info.date or "日期未知"
            print_success(f"  → [{category}] {info.subtype or info.merchant} | {amount_str} | {date_str}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="报销助手 - 智能发票识别与报销整理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cli.py --input ./发票 --output ./报销结果
  python cli.py  # 交互模式

环境变量:
  DEEPSEEK_API_KEY  DeepSeek API 密钥
        """
    )

    parser.add_argument("--input", "-i", help="发票文件夹路径")
    parser.add_argument("--output", "-o", help="输出目录路径")
    parser.add_argument("--copy", "-c", action="store_true", default=True, help="复制文件（默认）")
    parser.add_argument("--move", "-m", action="store_true", help="移动文件（不保留原文件）")
    parser.add_argument("--setup", "-s", action="store_true", help="配置 API Key")

    args = parser.parse_args()

    # 配置 API Key
    if args.setup:
        setup_wizard()
        return

    # 获取 API Key
    if not is_configured():
        print_header("首次使用需要配置 API Key")
        print("请到硅基流动获取 API Key:")
        print("👉 https://cloud.siliconflow.cn/i/Wd45d1wI")
        print()
        if not setup_wizard():
            sys.exit(1)

    api_key = get_api_key()

    # 获取输入目录
    input_dir = args.input
    if not input_dir:
        input_dir = input("请输入发票文件夹路径: ").strip()

    if not input_dir:
        print_error("未指定发票文件夹")
        sys.exit(1)

    input_path = Path(input_dir).absolute()
    if not input_path.exists():
        print_error(f"目录不存在: {input_path}")
        sys.exit(1)

    # 获取输出目录
    output_dir = args.output
    if not output_dir:
        default_output = input_path.parent / "报销结果"
        output_dir = input(f"请输入输出目录路径 [默认: {default_output}]: ").strip()
        if not output_dir:
            output_dir = str(default_output)

    output_path = Path(output_dir).absolute()

    print_header("报销助手")
    print(f"输入目录: {input_path}")
    print(f"输出目录: {output_path}")
    print(f"模式: {'复制' if args.copy and not args.move else '移动'}")

    # 扫描文件
    print_info("扫描发票文件...")
    try:
        files = scan_files(str(input_path))
    except Exception as e:
        print_error(f"扫描失败: {e}")
        sys.exit(1)

    if not files:
        print_warning("未找到支持的发票文件（jpg/png/pdf）")
        sys.exit(0)

    print_success(f"找到 {len(files)} 个文件")

    # 分析发票
    print_header("分析发票内容")
    invoice_infos = process_invoices(files, api_key)

    # 整理文件
    print_header("整理文件")
    copy_mode = not args.move
    organizer = FileOrganizer(str(output_path), copy_mode=copy_mode)
    categorized = organizer.organize(invoice_infos)

    # 生成报表
    print_info("生成统计报表...")
    report_path = generate_report(str(output_path), categorized)
    print_success(f"报表已生成: {report_path}")

    # 显示汇总
    print_header("处理完成！汇总如下")

    total_amount = 0.0
    total_count = 0

    for category_name in ['打车票', '火车飞机票', '住宿费', '餐费', '其他', PENDING_CATEGORY]:
        if category_name in categorized:
            infos = categorized[category_name]
            invoices = [i for i in infos if i.is_invoice]
            count = len(invoices)
            amount = sum(i.amount for i in invoices)
            if count > 0:
                print(f"  {category_name}: {count} 张, ¥{amount:.2f}")
                total_amount += amount
                total_count += count

    print("-" * 40)
    print(f"  总计: {total_count} 张, ¥{total_amount:.2f}")
    print("=" * 60)
    print()
    print_success(f"文件已整理到: {output_path}")
    print_success(f"统计报表: {report_path}")


if __name__ == "__main__":
    main()
