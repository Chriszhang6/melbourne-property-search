#!/usr/bin/env python3

import asyncio
import argparse
from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table
import re
from datetime import datetime

async def fetch_property_data(suburb: str, context) -> dict:
    """抓取特定区域的房产数据"""
    page = await context.new_page()
    try:
        # 构建搜索URL
        url = f"https://www.realestate.com.au/buy/in-point+cook,+vic+3030/list-1"
        print(f"正在获取 {url} 的数据...")
        
        # 设置更长的超时时间
        await page.goto(url, wait_until='networkidle', timeout=30000)
        
        # 等待页面加载完成
        await page.wait_for_load_state('networkidle')
        
        # 打印页面标题，用于调试
        title = await page.title()
        print(f"页面标题: {title}")
        
        # 获取房产列表
        # 尝试多个可能的选择器
        selectors = [
            '[data-testid="residential-card"]',
            '.residential-card',
            '.property-card',
            '.property-listing'
        ]
        
        properties = []
        for selector in selectors:
            try:
                print(f"尝试使用选择器: {selector}")
                properties = await page.query_selector_all(selector)
                if properties:
                    print(f"找到 {len(properties)} 个房产信息")
                    break
            except Exception as e:
                print(f"选择器 {selector} 失败: {str(e)}")
                continue
        
        if not properties:
            print("未能找到任何房产信息，可能需要更新选择器")
            return []
        
        results = []
        for prop in properties[:10]:  # 只获取前10个结果
            try:
                # 获取价格
                price = ""
                for price_selector in ['.property-price', '[data-testid="listing-price"]', '.price']:
                    price_elem = await prop.query_selector(price_selector)
                    if price_elem:
                        price = await price_elem.inner_text()
                        break
                
                # 获取地址
                address = ""
                for addr_selector in ['.property-address', '[data-testid="address"]', '.address']:
                    addr_elem = await prop.query_selector(addr_selector)
                    if addr_elem:
                        address = await addr_elem.inner_text()
                        break
                
                # 获取详情
                details = ""
                for details_selector in ['.property-features', '[data-testid="property-features"]', '.features']:
                    details_elem = await prop.query_selector(details_selector)
                    if details_elem:
                        details = await details_elem.inner_text()
                        break
                
                if price or address or details:
                    results.append({
                        "price": price or "价格未公布",
                        "address": address or "地址未知",
                        "details": details or "详情未知"
                    })
                    
            except Exception as e:
                print(f"处理房产信息时出错: {str(e)}")
                continue
        
        return results
    except Exception as e:
        print(f"获取数据时出错: {str(e)}")
        return []
    finally:
        await page.close()

def display_results(results: list):
    """显示房产搜索结果"""
    console = Console()
    table = Table(show_header=True)
    
    table.add_column("价格", style="bold cyan", width=30)
    table.add_column("地址", style="blue", width=40)
    table.add_column("详情", style="green", width=50)
    
    for result in results:
        table.add_row(
            result.get("price", "N/A"),
            result.get("address", "N/A"),
            result.get("details", "N/A")
        )
    
    console.print(table)

async def main():
    parser = argparse.ArgumentParser(description='获取特定区域的房产信息')
    parser.add_argument('suburb', help='区域名称（例如：Point Cook）')
    
    args = parser.parse_args()
    
    async with async_playwright() as p:
        # 启动浏览器，设置为有头模式以便调试
        browser = await p.chromium.launch(headless=False)
        try:
            # 创建新的上下文并设置用户代理
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            results = await fetch_property_data(args.suburb, context)
            if results:
                print(f"\n{args.suburb}区域的房产信息：")
                display_results(results)
            else:
                print("未找到房产信息")
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(main()) 