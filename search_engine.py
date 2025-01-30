from duckduckgo_search import DDGS
from datetime import datetime
import asyncio
from typing import Dict, List
import re
import logging
import time
from collections import deque
from threading import Lock

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int = 20, time_window: float = 1.0):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = Lock()

    def acquire(self):
        """获取请求许可"""
        with self.lock:
            now = time.time()
            
            # 移除过期的请求记录
            while self.requests and now - self.requests[0] >= self.time_window:
                self.requests.popleft()
            
            # 如果当前请求数量达到限制，等待直到有空闲配额
            if len(self.requests) >= self.max_requests:
                sleep_time = self.requests[0] + self.time_window - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    now = time.time()
                    # 重新清理过期请求
                    while self.requests and now - self.requests[0] >= self.time_window:
                        self.requests.popleft()
            
            # 记录新的请求时间
            self.requests.append(now)

class PropertySearchEngine:
    def __init__(self):
        self.categories = {
            'schools': ['school', 'education', 'college', 'primary', 'secondary', 'ranking', 'performance'],
            'hospitals': ['hospital', 'medical', 'healthcare', 'clinic', 'emergency'],
            'infrastructure': ['development', 'council', 'infrastructure', 'community', 'upgrade', 'project', 'funding'],
            'crime': ['crime', 'safety', 'police', 'incident', 'statistics'],
            'property': ['property', 'house', 'price', 'market', 'real estate', 'median']
        }
        self.rate_limiter = RateLimiter(max_requests=18, time_window=1.0)  # 留一些余量
        self.results_cache = {}
        self.cache_ttl = 3600  # 缓存有效期1小时

    def _get_cached_results(self, query: str) -> List[Dict]:
        """获取缓存的搜索结果"""
        if query in self.results_cache:
            cache_time, results = self.results_cache[query]
            if time.time() - cache_time < self.cache_ttl:
                logger.info(f"使用缓存结果: {query}")
                return results
            else:
                del self.results_cache[query]
        return None

    def _cache_results(self, query: str, results: List[Dict]):
        """缓存搜索结果"""
        self.results_cache[query] = (time.time(), results)

    def _safe_search(self, ddgs, query: str, max_results: int = 10, retries: int = 3) -> List[Dict]:
        """安全的搜索函数，包含重试逻辑和速率限制"""
        # 首先检查缓存
        cached_results = self._get_cached_results(query)
        if cached_results is not None:
            return cached_results

        for attempt in range(retries):
            try:
                # 获取请求许可
                self.rate_limiter.acquire()
                
                results = list(ddgs.text(query, max_results=max_results))
                
                # 缓存结果
                self._cache_results(query, results)
                return results
            except Exception as e:
                logger.warning(f"搜索失败 (尝试 {attempt + 1}/{retries}): {str(e)}")
                if attempt < retries - 1:
                    time.sleep(1)  # 基础等待时间
                else:
                    logger.error(f"搜索失败，已达到最大重试次数: {query}")
                    return []

    def search_suburb(self, suburb: str) -> Dict:
        """执行综合搜索并返回结果"""
        logger.info(f"开始搜索区域: {suburb}")
        
        combined_results = {
            'schools': [],
            'hospitals': [],
            'infrastructure': [],
            'crime': [],
            'property': [],
            'timestamp': datetime.now().isoformat(),
            'suburb': suburb
        }
        
        search_queries = {
            'schools': [
                (f"{suburb} Melbourne public schools NAPLAN rankings", 10),
                (f"{suburb} Melbourne private schools VCE results", 10),
                (f"{suburb} Melbourne catholic schools facilities", 5)
            ],
            'hospitals': [
                (f"{suburb} Melbourne hospitals medical centers", 10),
                (f"{suburb} Melbourne healthcare facilities services", 10)
            ],
            'infrastructure': [
                (f"{suburb} Melbourne infrastructure development budget", 10),
                (f"{suburb} Melbourne council projects timeline", 10)
            ],
            'crime': [
                (f"{suburb} Melbourne crime statistics reports", 10),
                (f"{suburb} Melbourne safety police data", 10)
            ],
            'property': [
                (f"{suburb} Melbourne property market analysis", 10),
                (f"{suburb} Melbourne real estate prices trends", 10)
            ]
        }
        
        with DDGS() as ddgs:
            for category, queries in search_queries.items():
                for query, max_results in queries:
                    results = self._safe_search(ddgs, query, max_results=max_results)
                    for result in results:
                        if self._is_relevant(category, result.get('body', '')):
                            combined_results[category].append({
                                'title': result.get('title', ''),
                                'link': result.get('link', ''),
                                'summary': result.get('body', '')[:800],
                                'date': self._extract_date(result.get('body', ''))
                            })
        
        # 对每个类别的结果进行去重和限制
        for category in combined_results:
            if isinstance(combined_results[category], list):
                # 使用集合去重（基于链接）
                seen_links = set()
                unique_results = []
                for result in combined_results[category]:
                    if result['link'] not in seen_links:
                        seen_links.add(result['link'])
                        unique_results.append(result)
                combined_results[category] = unique_results[:20]  # 限制每个类别最多20条结果
        
        logger.info(f"搜索完成，结果统计：")
        for category, results in combined_results.items():
            if isinstance(results, list):
                logger.info(f"- {category}相关: {len(results)} 条")
        
        return combined_results

    def _is_relevant(self, category: str, text: str) -> bool:
        """检查文本是否与指定类别相关"""
        keywords = self.categories[category]
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)
    
    def _extract_date(self, text: str) -> str:
        """从文本中提取日期"""
        date_patterns = [
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',  # DD-MM-YYYY
            r'\d{4}'  # YYYY
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return '' 