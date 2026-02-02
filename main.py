#!/usr/bin/env python3
"""
报销助手 - 统一入口

使用方法:
    python main.py              # 桌面版（默认）
    python main.py --web        # 网页版
    python main.py --cli        # 命令行版
    python main.py --cli -i ./发票 -o ./结果
"""
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="报销助手 - 智能发票识别与报销整理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py              # 启动桌面版
  python main.py --web        # 启动网页版
  python main.py --cli        # 启动命令行版
  python main.py --cli -i ./发票 -o ./结果  # 命令行处理
        """
    )

    parser.add_argument(
        '--web', '-w',
        action='store_true',
        help='启动网页版'
    )
    parser.add_argument(
        '--cli', '-c',
        action='store_true',
        help='启动命令行版'
    )
    parser.add_argument(
        '--input', '-i',
        help='发票文件夹路径（仅CLI模式）'
    )
    parser.add_argument(
        '--output', '-o',
        help='输出目录路径（仅CLI模式）'
    )
    parser.add_argument(
        '--copy',
        action='store_true',
        help='复制文件而非移动（仅CLI模式）'
    )
    parser.add_argument(
        '--api-key', '-k',
        help='API 密钥'
    )

    args = parser.parse_args()

    # 默认启动桌面版
    if not args.web and not args.cli:
        # 桌面版
        import desktop_app
        desktop_app.main()
        return

    # 网页版
    if args.web:
        import web_app
        web_app.main()
        return

    # 命令行版
    if args.cli:
        import reimbursement
        # 构建命令行参数
        cli_args = []
        if args.input:
            cli_args.extend(['--input', args.input])
        if args.output:
            cli_args.extend(['--output', args.output])
        if args.copy:
            cli_args.append('--copy')
        if args.api_key:
            cli_args.extend(['--api-key', args.api_key])

        # 修改 sys.argv
        sys.argv = ['reimbursement.py'] + cli_args
        reimbursement.main()
        return


if __name__ == '__main__':
    main()
