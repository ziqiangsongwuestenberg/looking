"""
Looking - Fashion News Monitor
自动搜索并收集 fashion 相关新闻
"""

import os
import sys
import json
import yaml
import argparse
import schedule
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup


class FashionSearcher:
    """Fashion 新闻搜索器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.output_dir = Path(self.config['output']['directory'])
        self.output_dir.mkdir(exist_ok=True)

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def search_duckduckgo(self, query: str, max_results: int = 10) -> list:
        """使用 DuckDuckGo 搜索（无需 API key）"""
        results = []
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

            for result in soup.select('.result')[:max_results]:
                title_elem = result.select_one('.result__a')
                snippet_elem = result.select_one('.result__snippet')

                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                    results.append({
                        'title': title,
                        'url': link,
                        'snippet': snippet,
                        'source': 'DuckDuckGo',
                        'query': query,
                        'timestamp': datetime.now().isoformat()
                    })

        except Exception as e:
            print(f"搜索出错 ({query}): {e}")

        return results

    def search_all_keywords(self) -> list:
        """搜索所有关键词"""
        all_results = []
        keywords = self.config['keywords']
        max_results = self.config['search']['max_results_per_keyword']

        print(f"\n{'='*60}")
        print(f"Fashion 新闻搜索 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        for keyword in keywords:
            print(f"\n搜索关键词: {keyword}")
            results = self.search_duckduckgo(keyword, max_results)
            print(f"  找到 {len(results)} 条结果")
            all_results.extend(results)
            time.sleep(1)

        print(f"\n总计: {len(all_results)} 条新闻")
        return all_results

    def save_results(self, results: list):
        """保存搜索结果"""
        today = datetime.now().strftime('%Y-%m-%d')
        output_format = self.config['output']['format']

        if output_format in ['json', 'both']:
            json_path = self.output_dir / f"news_{today}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"已保存: {json_path}")

        if output_format in ['markdown', 'both']:
            md_path = self.output_dir / f"news_{today}.md"
            md_content = self._generate_markdown(results)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"已保存: {md_path}")

    def _generate_markdown(self, results: list) -> str:
        """生成 Markdown 报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        md = f"# Fashion News Monitor - {today}\n\n共找到 {len(results)} 条新闻\n\n---\n\n"
        for i, item in enumerate(results, 1):
            md += f"## {i}. {item['title']}\n\n- **来源**: {item['source']}\n- **关键词**: {item['query']}\n- **链接**: [{item['url']}]({item['url']})\n\n{item['snippet']}\n\n---\n\n"
        return md

    def cleanup_old_files(self):
        """清理旧文件"""
        keep_days = self.config['output'].get('keep_days', 30)
        cutoff = datetime.now().timestamp() - keep_days * 86400
        for file in self.output_dir.glob('news_*'):
            if file.stat().st_mtime < cutoff:
                file.unlink()
                print(f"已删除旧文件: {file}")

    def run_once(self) -> list:
        """执行一次搜索"""
        results = self.search_all_keywords()
        if results:
            self.save_results(results)
        self.cleanup_old_files()
        return results

    def run_scheduled(self):
        """启动定时任务"""
        schedule_time = self.config['schedule']['time']
        print(f"\n定时任务已启动")
        print(f"每天 {schedule_time} 执行搜索")
        print(f"按 Ctrl+C 停止\n")
        schedule.every().day.at(schedule_time).do(self.run_once)
        while True:
            schedule.run_pending()
            time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description='Fashion News Monitor')
    parser.add_argument('--schedule', action='store_true', help='启动定时任务')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    args = parser.parse_args()
    searcher = FashionSearcher(args.config)
    if args.schedule:
        searcher.run_scheduled()
    else:
        searcher.run_once()


if __name__ == '__main__':
    main()
