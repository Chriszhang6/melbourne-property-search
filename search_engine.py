from duckduckgo_search import DDGS
from datetime import datetime
import asyncio
from typing import Dict, List
import re
import logging
import time
import random

logger = logging.getLogger(__name__)

class PropertySearchEngine:
    def __init__(self):
        self.categories = {
            'schools': ['school', 'education', 'college', 'primary', 'secondary', 'ranking', 'performance'],
            'hospitals': ['hospital', 'medical', 'healthcare', 'clinic', 'emergency'],
            'infrastructure': ['development', 'council', 'infrastructure', 'community', 'upgrade', 'project', 'funding'],
            'crime': ['crime', 'safety', 'police', 'incident', 'statistics'],
            'property': ['property', 'house', 'price', 'market', 'real estate', 'median']
        }
        self.last_search_time = 0
        self.min_delay = 3  # 最小延迟秒数
    
    def _wait_before_search(self):
        """确保搜索之间有足够的延迟"""
        current_time = time.time()
        elapsed = current_time - self.last_search_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed + random.uniform(0.1, 0.5))
        self.last_search_time = time.time()

    def _safe_search(self, ddgs, query: str, max_results: int = 10, retries: int = 3) -> List[Dict]:
        """安全的搜索函数，包含重试逻辑"""
        for attempt in range(retries):
            try:
                self._wait_before_search()
                results = list(ddgs.text(query, max_results=max_results))
                return results
            except Exception as e:
                logger.warning(f"搜索失败 (尝试 {attempt + 1}/{retries}): {str(e)}")
                if attempt < retries - 1:
                    time.sleep((attempt + 1) * 2)  # 递增等待时间
                else:
                    logger.error(f"搜索失败，已达到最大重试次数: {query}")
                    return []
    
    def search_suburb(self, suburb: str) -> Dict:
        """执行综合搜索并返回结果"""
        logger.info(f"开始搜索区域: {suburb}")
        
        # 合并查询以减少API调用
        combined_results = {
            'schools': [],
            'hospitals': [],
            'infrastructure': [],
            'crime': [],
            'property': [],
            'timestamp': datetime.now().isoformat(),
            'suburb': suburb
        }
        
        with DDGS() as ddgs:
            # 教育资源（合并查询）
            education_query = f"{suburb} Melbourne schools education NAPLAN VCE public private catholic"
            results = self._safe_search(ddgs, education_query, max_results=20)
            for result in results:
                if self._is_relevant('schools', result.get('body', '')):
                    combined_results['schools'].append({
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'summary': result.get('body', '')[:800],
                        'date': self._extract_date(result.get('body', ''))
                    })
            
            # 医疗资源（合并查询）
            health_query = f"{suburb} Melbourne hospitals medical centers clinics healthcare facilities"
            results = self._safe_search(ddgs, health_query, max_results=20)
            for result in results:
                if self._is_relevant('hospitals', result.get('body', '')):
                    combined_results['hospitals'].append({
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'summary': result.get('body', '')[:800],
                        'date': self._extract_date(result.get('body', ''))
                    })
            
            # 基础设施（合并查询）
            infra_query = f"{suburb} Melbourne infrastructure development projects council budget"
            results = self._safe_search(ddgs, infra_query, max_results=20)
            for result in results:
                if self._is_relevant('infrastructure', result.get('body', '')):
                    combined_results['infrastructure'].append({
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'summary': result.get('body', '')[:800],
                        'date': self._extract_date(result.get('body', ''))
                    })
            
            # 治安状况（合并查询）
            crime_query = f"{suburb} Melbourne crime statistics safety police reports"
            results = self._safe_search(ddgs, crime_query, max_results=20)
            for result in results:
                if self._is_relevant('crime', result.get('body', '')):
                    combined_results['crime'].append({
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'summary': result.get('body', '')[:800],
                        'date': self._extract_date(result.get('body', ''))
                    })
            
            # 房产市场（合并查询）
            property_query = f"{suburb} Melbourne property market prices real estate trends"
            results = self._safe_search(ddgs, property_query, max_results=20)
            for result in results:
                if self._is_relevant('property', result.get('body', '')):
                    combined_results['property'].append({
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'summary': result.get('body', '')[:800],
                        'date': self._extract_date(result.get('body', ''))
                    })
        
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