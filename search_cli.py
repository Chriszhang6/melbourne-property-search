#!/usr/bin/env python3
import argparse
from duckduckgo_search import DDGS
from rich.console import Console
from rich.table import Table

def search_duckduckgo(query, search_type='web', max_results=5):
    """
    使用DuckDuckGo API搜索并返回结果
    """
    try:
        with DDGS() as ddgs:
            if search_type == 'web':
                results = list(ddgs.text(query, max_results=max_results))
            elif search_type == 'news':
                results = list(ddgs.news(query, max_results=max_results))
            else:
                print(f"不支持的搜索类型: {search_type}")
                return []
            return results
    except Exception as e:
        print(f"搜索时发生错误: {str(e)}")
        return []

def display_results(results, search_type='web'):
    """
    使用rich库美化输出搜索结果
    """
    console = Console()
    table = Table(show_header=True)
    
    if search_type == 'web':
        table.add_column("标题", style="bold cyan", width=40)
        table.add_column("链接", style="blue", width=30)
        table.add_column("摘要", style="green", width=50)
    else:  # news
        table.add_column("标题", style="bold cyan", width=40)
        table.add_column("来源", style="blue", width=20)
        table.add_column("日期", style="yellow", width=20)
        table.add_column("摘要", style="green", width=40)

    for result in results:
        if not result:
            continue
            
        title = result.get('title', '')
        link = result.get('link', '')
        snippet = result.get('snippet', '')
        if not snippet:
            snippet = result.get('body', '')
            
        if search_type == 'web':
            if title or link or snippet:
                table.add_row(
                    (title[:37] + "..." if len(title) > 40 else title) if title else "N/A",
                    (link[:27] + "..." if len(link) > 30 else link) if link else "N/A",
                    (snippet[:47] + "..." if len(snippet) > 50 else snippet) if snippet else "N/A"
                )
        else:  # news
            source = result.get('source', '')
            date = result.get('date', '')
            if title or source or date or snippet:
                table.add_row(
                    (title[:37] + "..." if len(title) > 40 else title) if title else "N/A",
                    (source[:17] + "..." if len(source) > 20 else source) if source else "N/A",
                    date if date else "N/A",
                    (snippet[:37] + "..." if len(snippet) > 40 else snippet) if snippet else "N/A"
                )
    
    console.print(table)

def main():
    parser = argparse.ArgumentParser(description='DuckDuckGo命令行搜索工具')
    parser.add_argument('query', help='搜索关键词')
    parser.add_argument('-t', '--type', choices=['web', 'news'], default='web', help='搜索类型：web(网页) 或 news(新闻)，默认为web')
    parser.add_argument('-n', '--num', type=int, default=5, help='显示结果数量（默认为5）')
    
    args = parser.parse_args()
    
    results = search_duckduckgo(args.query, args.type, args.num)
    if results:
        display_results(results, args.type)
    else:
        print("未找到搜索结果")

if __name__ == "__main__":
    main() 