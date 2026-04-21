"""
测试脚本 - 验证搜索功能
"""

from main import NewsSearcher

if __name__ == '__main__':
    print("测试搜索功能...")
    searcher = NewsSearcher()
    
    # 只搜索一个关键词测试
    test_query = "fashion news"
    print(f"\n测试搜索: {test_query}")
    results = searcher.search_duckduckgo(test_query, max_results=5)
    
    print(f"\n找到 {len(results)} 条结果:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['title']}")
        print(f"   {r['url']}")
        print(f"   {r['snippet'][:100]}...")
