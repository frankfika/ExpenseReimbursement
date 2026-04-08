#!/usr/bin/env python3
"""报销助手 - 命令行入口（简化版）

使用方法:
    python main.py --input ./发票 --output ./报销结果
    python main.py -i ./发票 -o ./报销结果

环境变量:
    DEEPSEEK_API_KEY  API 密钥（必需）
    DEEPSEEK_MODEL    模型名称（默认: deepseek-ai/DeepSeek-V3）
"""
import sys
import argparse
from pathlib import Path

from app import is_configured, get_api_key
from app import FileOrganizer, generate_report
from app.config import INVOICE_CATEGORIES, PENDING_CATEGORY
from app.ui import print_header, print_success, print_error
from cli import scan_files, process_invoices


def main():
    parser = argparse.ArgumentParser(
        description="报销助手 - 智能发票识别与报销整理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py -i ./发票 -o ./报销结果
  python main.py --input ./发票            # 输出默认为发票文件夹同级的"报销结果"

环境变量:
  DEEPSEEK_API_KEY  API 密钥（必需）
        """
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="发票文件夹路径"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出目录路径（默认: 发票文件夹同级的 '报销结果' 目录）"
    )
    parser.add_argument(
        "--move", "-m",
        action="store_true",
        help="移动文件（默认为复制，保留原文件）"
    )

    args = parser.parse_args()

    # 检查 API Key
    if not is_configured():
        print_error("未配置 API Key，请设置环境变量 DEEPSEEK_API_KEY")
        sys.exit(1)

    api_key = get_api_key()

    # 输入目录
    input_path = Path(args.input).absolute()
    if not input_path.exists():
        print_error(f"目录不存在: {input_path}")
        sys.exit(1)

    # 输出目录
    if args.output:
        output_path = Path(args.output).absolute()
    else:
        output_path = input_path.parent / "报销结果"

    print_header("📝 报销助手")
    print(f"  📁 输入: {input_path}")
    print(f"  📁 输出: {output_path}")
    print(f"  🔄 模式: {'复制' if not args.move else '移动'}")
    print("=" * 60)

    # 扫描文件
    print(f"\n🔍 正在扫描发票文件...")
    try:
        files = scan_files(str(input_path))
    except Exception as e:
        print_error(f"扫描失败: {e}")
        sys.exit(1)

    if not files:
        print_error("未找到支持的发票文件（jpg/png/pdf）")
        sys.exit(0)

    print_success(f"找到 {len(files)} 个文件")

    # 分析发票
    print_header("🧠 分析发票内容")
    invoice_infos = process_invoices(files, api_key)

    # 整理文件
    print_header("🗂️ 整理文件")
    organizer = FileOrganizer(str(output_path), copy_mode=not args.move)
    categorized = organizer.organize(invoice_infos)

    # 生成报表
    print(f"\n📊 正在生成统计报表...")
    report_path = generate_report(str(output_path), categorized)
    print_success(f"报表已生成: {report_path}")

    # 显示汇总
    print_header("✅ 处理完成！")

    total_amount = 0.0
    total_count = 0

    for category_key, category_name in INVOICE_CATEGORIES.items():
        if category_name in categorized:
            infos = categorized[category_name]
            invoices = [i for i in infos if i.is_invoice]
            count = len(invoices)
            amount = sum(i.amount for i in invoices)
            if count > 0:
                print(f"  {category_name}: {count} 张, ¥{amount:.2f}")
                total_amount += amount
                total_count += count

    if PENDING_CATEGORY in categorized:
        pending = categorized[PENDING_CATEGORY]
        pending_invoices = [i for i in pending if i.is_invoice]
        if pending_invoices:
            print(f"  ⚠️  {PENDING_CATEGORY}: {len(pending_invoices)} 张需要手动确认")

    print("-" * 40)
    print(f"  💰 总计: {total_count} 张, ¥{total_amount:.2f}")
    print("=" * 60)
    print(f"\n📄 文件已整理到: {output_path}")


if __name__ == "__main__":
    main()
