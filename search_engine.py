from duckduckgo_search import DDGS
from datetime import datetime
import asyncio
from typing import Dict, List
import re

class PropertySearchEngine:
    def __init__(self):
        self.categories = {
            'infrastructure': ['development', 'projects', 'infrastructure', 'railway', 'school', 'hospital', 'road'],
            'crime': ['crime', 'safety', 'security', 'incident', 'police'],
            'property': ['property', 'house', 'price', 'market', 'real estate']
        }
    
    def search_suburb(self, suburb: str) -> Dict:
        """执行综合搜索并返回结果"""
        results = {
            'infrastructure': self._search_infrastructure(suburb),
            'crime': self._search_crime_stats(suburb),
            'property': self._search_property_trends(suburb),
            'timestamp': datetime.now().isoformat(),
            'suburb': suburb
        }
        return results
    
    def _search_infrastructure(self, suburb: str) -> List[Dict]:
        """搜索基础设施发展项目"""
        results = []
        with DDGS() as ddgs:
            # 构建搜索查询
            query = f"{suburb} Melbourne infrastructure development projects past 10 years"
            search_results = list(ddgs.text(query, max_results=10))
            
            # 处理结果
            for result in search_results:
                if self._is_relevant_infrastructure(result.get('body', '')):
                    results.append({
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'summary': result.get('body', '')[:200] + '...',
                        'date': self._extract_date(result.get('body', ''))
                    })
        return results
    
    def _search_crime_stats(self, suburb: str) -> List[Dict]:
        """搜索犯罪率统计"""
        results = []
        with DDGS() as ddgs:
            query = f"{suburb} Melbourne crime rate statistics safety past 10 years"
            search_results = list(ddgs.text(query, max_results=10))
            
            for result in search_results:
                if self._is_relevant_crime(result.get('body', '')):
                    results.append({
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'summary': result.get('body', '')[:200] + '...',
                        'date': self._extract_date(result.get('body', ''))
                    })
        return results
    
    def _search_property_trends(self, suburb: str) -> List[Dict]:
        """搜索房价走势"""
        results = []
        with DDGS() as ddgs:
            query = f"{suburb} Melbourne property price trends market analysis past 10 years"
            search_results = list(ddgs.text(query, max_results=10))
            
            for result in search_results:
                if self._is_relevant_property(result.get('body', '')):
                    results.append({
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'summary': result.get('body', '')[:200] + '...',
                        'date': self._extract_date(result.get('body', ''))
                    })
        return results
    
    def _is_relevant_infrastructure(self, text: str) -> bool:
        """检查是否为相关的基础设施信息"""
        keywords = self.categories['infrastructure']
        return any(keyword.lower() in text.lower() for keyword in keywords)
    
    def _is_relevant_crime(self, text: str) -> bool:
        """检查是否为相关的犯罪统计信息"""
        keywords = self.categories['crime']
        return any(keyword.lower() in text.lower() for keyword in keywords)
    
    def _is_relevant_property(self, text: str) -> bool:
        """检查是否为相关的房产信息"""
        keywords = self.categories['property']
        return any(keyword.lower() in text.lower() for keyword in keywords)
    
    def _extract_date(self, text: str) -> str:
        """从文本中提取日期"""
        # 简单的日期提取示例
        date_pattern = r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
        match = re.search(date_pattern, text)
        return match.group(0) if match else '' 