"""
Looking - Custom Website Monitor
功能一：监控用户提供的网站列表（需登录），每天抓取最受欢迎的10条内容
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from dataclasses import dataclass, asdict
from typing import Optional
import yaml


@dataclass
class ArticleItem:
    site_name: str
    site_url: str
    title: str
    link: str


class SiteMonitor:
    """单站点监控器"""

    def __init__(self, config: dict):
        self.name = config['name']
        self.base_url = config['url']
        self.login_url = config['login_url']
        self.username = config['username']
        self.password = config['password']
        self.username_field = config.get('username_field', 'username')
        self.password_field = config.get('password_field', 'password')
        self.submit_button = config.get('submit_button', '')
        self.article_list_selector = config.get('article_list_selector', 'a.article-title, a.post-title, h2 a, h3 a')
        self.article_link_selector = config.get('article_link_selector', 'a[href]')
        self.article_title_selector = config.get('article_title_selector', 'a, h2, h3, .title')
        self.max_items = config.get('max_items', 10)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def login(self) -> bool:
        """登录网站"""
        try:
            resp = self.session.get(self.base_url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'lxml')

            login_data = {
                self.username_field: self.username,
                self.password_field: self.password,
            }
            if self.submit_button:
                login_data[self.submit_button] = ''

            resp2 = self.session.post(self.login_url, data=login_data, timeout=15, allow_redirects=True)
            resp2.raise_for_status()

            if 'login' in resp2.url.lower() or 'signin' in resp2.url.lower():
                return False
            return True

        except Exception as e:
            print(f"  [{self.name}] 登录失败: {e}")
            return False

    def fetch_articles(self) -> list[ArticleItem]:
        """抓取文章列表"""
        results = []
        try:
            resp = self.session.get(self.base_url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'lxml')

            items_found = []
            seen_links = set()

            if self.article_list_selector:
                items = soup.select(self.article_list_selector)
                for item in items:
                    link_el = item if item.name == 'a' else item.find('a', href=True)
                    if link_el:
                        href = link_el.get('href', '')
                        title = link_el.get_text(strip=True)
                        if href and title and href not in seen_links:
                            seen_links.add(href)
                            items_found.append((title, self._abs_url(href)))

            if not items_found:
                link_els = soup.select(self.article_link_selector)
                title_els = soup.select(self.article_title_selector)
                title_map = {el.get_text(strip=True): el for el in title_els if el.get_text(strip=True)}

                for link_el in link_els:
                    href = link_el.get('href', '')
                    if href and href not in seen_links:
                        href = self._abs_url(href)
                        title = link_el.get_text(strip=True)
                        if not title and href in title_map:
                            title = title_map[href].get_text(strip=True)
                        if title:
                            seen_links.add(href)
                            items_found.append((title, href))

            for title, link in items_found[:self.max_items]:
                results.append(ArticleItem(
                    site_name=self.name,
                    site_url=self.base_url,
                    title=title,
                    link=link
                ))

        except Exception as e:
            print(f"  [{self.name}] 抓取失败: {e}")

        return results

    def _abs_url(self, href: str) -> str:
        if href.startswith('http'):
            return href
        return urljoin(self.base_url, href)


class MonitorRunner:
    """全量监控运行器"""

    def __init__(self, config_path: str = "config_monitor.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.output_dir = Path(self.config['output']['directory'])
        self.output_dir.mkdir(exist_ok=True)

    def _load_config(self) -> dict:
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def run(self) -> list[ArticleItem]:
        """执行全量监控"""
        all_results = []
        sites = self.config.get('sites', [])

        print(f"\n{'='*60}")
        print(f"网站监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")

        if not sites:
            print("配置文件中没有站点，请编辑 config_monitor.yaml 添加站点。")
            return []

        for site_cfg in sites:
            name = site_cfg.get('name', site_cfg['url'])
            print(f"\n正在监控: {name}")
            monitor = SiteMonitor(site_cfg)

            if not monitor.login():
                print(f"  [{name}] 登录失败，跳过")
                continue

            print(f"  [{name}] 登录成功，开始抓取...")
            articles = monitor.fetch_articles()
            print(f"  [{name}] 获取到 {len(articles)} 条")
            all_results.extend(articles)
            time.sleep(1)

        print(f"\n总计获取: {len(all_results)} 条")
        self.save_results(all_results)
        return all_results

    def save_results(self, results: list[ArticleItem]):
        """保存结果"""
        today = datetime.now().strftime('%Y-%m-%d')
        output_format = self.config['output'].get('format', 'both')

        if output_format in ['json', 'both']:
            json_path = self.output_dir / f"monitor_{today}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump([asdict(r) for r in results], f, ensure_ascii=False, indent=2)
            print(f"已保存: {json_path}")

        if output_format in ['markdown', 'both']:
            md_path = self.output_dir / f"monitor_{today}.md"
            md = self._generate_markdown(results, today)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md)
            print(f"已保存: {md_path}")

    def _generate_markdown(self, results: list[ArticleItem], today: str) -> str:
        md = f"# Website Monitor - {today}\n\n共 {len(results)} 条\n\n---\n\n"
        for i, r in enumerate(results, 1):
            md += f"## {i}. {r.title}\n\n"
            md += f"- **网站名**: {r.site_name}\n"
            md += f"- **网站地址**: {r.site_url}\n"
            md += f"- **链接**: [{r.link}]({r.link})\n\n---\n\n"
        return md


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Website Monitor')
    parser.add_argument('--config', default='config_monitor.yaml', help='配置文件路径')
    args = parser.parse_args()

    runner = MonitorRunner(args.config)
    runner.run()


if __name__ == '__main__':
    main()
