"""
Looking - 全功能入口
支持以下模式：
  python main.py --all      # 运行全部（fashion + 网站监控 + gay新闻）
  python main.py --fashion  # 仅 fashion 新闻
  python main.py --monitor  # 仅网站监控
  python main.py --gay      # 仅 gay 新闻
  python main.py --schedule # 定时任务（每天自动运行 --all）
"""

import argparse
from datetime import datetime

from main_fashion import FashionSearcher
from monitor import MonitorRunner
from gay_news import GayNewsSearcher


def run_all():
    print(f"\n{'#'*60}")
    print(f"Looking 全量运行 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")

    results = {}
    results['fashion'] = FashionSearcher().run_once()
    results['monitor'] = MonitorRunner().run()
    results['gay'] = GayNewsSearcher().run()

    print(f"\n{'='*60}")
    print(f"全部完成！")
    print(f"  Fashion 新闻: {len(results['fashion'])} 条")
    print(f"  网站监控:     {len(results['monitor'])} 条")
    print(f"  Gay 新闻:     {len(results['gay'])} 条")
    print(f"{'='*60}")


def run_schedule():
    import schedule, time
    import threading

    def _run():
        t = threading.Thread(target=run_all)
        t.start()
        t.join()

    schedule.every().day.at("08:00").do(_run)
    schedule.every().day.at("20:00").do(_run)

    print("Looking 定时任务已启动")
    print("每天 08:00 和 20:00 自动运行全量搜索")
    print("按 Ctrl+C 停止\n")

    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description='Looking - 全功能新闻监控')
    parser.add_argument('--all', action='store_true', help='运行全部功能')
    parser.add_argument('--fashion', action='store_true', help='仅运行 Fashion 新闻')
    parser.add_argument('--monitor', action='store_true', help='仅运行网站监控')
    parser.add_argument('--gay', action='store_true', help='仅运行 Gay 新闻')
    parser.add_argument('--schedule', action='store_true', help='启动定时任务')
    args = parser.parse_args()

    if args.schedule:
        run_schedule()
    elif args.all:
        run_all()
    elif args.fashion:
        FashionSearcher().run_once()
    elif args.monitor:
        MonitorRunner().run()
    elif args.gay:
        GayNewsSearcher().run()
    else:
        run_all()


if __name__ == '__main__':
    main()
