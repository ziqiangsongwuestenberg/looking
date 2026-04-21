"""
Looking - Gay News Collector
功能二：每天搜索并收集5条 gay 相关新闻
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from dataclasses import dataclass, asdict
import yaml


@dataclass
class GayNewsItem:
    site_name: str
    site_url: str
    title: str
    link: str


class GayNewsSearcher:
    """Gay 新闻搜索器"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.output_dir = Path(self.config['output']['directory'])
        self.output_dir.mkdir(exist_ok=True)
        self.max_results = self.config.get('gay_news', {}).get('max_results', 5)
        self.keywords = self.config.get('gay_news', {}).get('keywords', [
            'gay news',
            'LGBTQ news',
            'gay rights news',
            'same-sex marriage news',
            'Pride news'
        ])

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def search_duckduckgo(self, query: str) -> list[GayNewsItem]:
        """使用 DuckDuckGo 搜索"""
        results = []
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'lxml')

            for result in soup.select('.result')[:self.max_results]:
                title_el = result.select_one('.result__a')
                snippet_el = result.select_one('.result__snippet')
                if title_el:
                    title = title_el.get_text(strip=True)
                    link = title_el.get('href', '')
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ''
                    results.append(GayNewsItem(
                        site_name=self._extract_domain(link),
                        site_url=link,
                        title=title,
                        link=link
                    ))
        except Exception as e:
            print(f"  搜索出错 ({query}): {e}")

        return results

    def _extract_domain(self, url: str) -> str:
        """从 URL 提取域名作为网站名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return url

    def run(self) -> list[GayNewsItem]:
        """执行搜索"""
        all_results = []
        seen_links = set()

        print(f"\n{'='*60}")
        print(f"Gay 新闻搜索 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        for keyword in self.keywords:
            print(f"\n搜索关键词: {keyword}")
            results = self.search_duckduckgo(keyword)
            added = 0
            for r in results:
                if r.link not in seen_links:
                    seen_links.add(r.link)
                    all_results.append(r)
                    added += 1
            print(f"  新增 {added} 条（累计 {len(all_results)} 条）")
            time.sleep(1)

            if len(all_results) >= self.max_results:
                break

        all_results = all_results[:self.max_results]
        print(f"\n总计获取: {len(all_results)} 条")
        self.save_results(all_results)
        return all_results

    def save_results(self, results: list[GayNewsItem]):
        """保存结果"""
        today = datetime.now().strftime('%Y-%m-%d')
        output_format = self.config['output'].get('format', 'both')

        if output_format in ['json', 'both']:
            json_path = self.output_dir / f"gay_news_{today}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
            print(f"已保存: {json_path}")

        if output_format in ['markdown', 'both']:
            md_path = self.output_dir / f"gay_news_{today}.md"
            md = self._generate_markdown(results, today)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"已保存: {md_path}")

    def _generate_markdown(self, results: list[GayNewsItem], today: str) -> str:
        md = f"# Gay News - {today}\n\n共 {len(results)} 条\n\n---\n\n"
        for i, r in enumerate(results, 1):
            md += f"## {i}. {r.title}\n\n"
            md += f"- **网站名**: {r.site_name}\n"
            md += f"- **网站地址**: [{r.site_url}]({r.site_url})\n"
            md += f"- **链接**: [点击阅读]({r.link})\n\n---\n\n"
        return md


def main():
    searcher = GayNewsSearcher()
    searcher.run()


if __name__ == '__main__':
    main()
