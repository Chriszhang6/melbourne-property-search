from duckduckgo_search import DDGS
from datetime import datetime
import asyncio
from typing import Dict, List
import re
import logging

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
    
    def search_suburb(self, suburb: str) -> Dict:
        """执行综合搜索并返回结果"""
        logger.info(f"开始搜索区域: {suburb}")
        results = {
            'schools': self._search_schools(suburb),
            'hospitals': self._search_hospitals(suburb),
            'infrastructure': self._search_infrastructure(suburb),
            'crime': self._search_crime_stats(suburb),
            'property': self._search_property_trends(suburb),
            'timestamp': datetime.now().isoformat(),
            'suburb': suburb
        }
        logger.info(f"搜索完成，结果统计：")
        logger.info(f"- 学校相关: {len(results['schools'])} 条")
        logger.info(f"- 医院相关: {len(results['hospitals'])} 条")
        logger.info(f"- 基建相关: {len(results['infrastructure'])} 条")
        logger.info(f"- 治安相关: {len(results['crime'])} 条")
        logger.info(f"- 房产相关: {len(results['property'])} 条")
        return results
    
    def _search_schools(self, suburb: str) -> List[Dict]:
        """搜索该区域的学校信息"""
        results = []
        with DDGS() as ddgs:
            queries = [
                f"{suburb} Melbourne top public private schools ratings",
                f"{suburb} Melbourne catholic independent schools facilities",
                f"{suburb} Melbourne school NAPLAN VCE results achievements",
                f"{suburb} Melbourne school enrollment capacity facilities",
                f"{suburb} Melbourne kindergarten childcare centers"
            ]
            for query in queries:
                logger.info(f"学校搜索词: {query}")
                search_results = list(ddgs.text(query, max_results=10))
                logger.info(f"获取到 {len(search_results)} 条结果")
                
                for result in search_results:
                    if self._is_relevant('schools', result.get('body', '')):
                        results.append({
                            'title': result.get('title', ''),
                            'link': result.get('link', ''),
                            'summary': result.get('body', '')[:800],
                            'date': self._extract_date(result.get('body', ''))
                        })
        return results[:30]  # 限制最多30条结果
    
    def _search_hospitals(self, suburb: str) -> List[Dict]:
        """搜索该区域的医疗设施"""
        results = []
        with DDGS() as ddgs:
            queries = [
                f"{suburb} Melbourne hospital emergency department news",
                f"{suburb} Melbourne medical center expansion development",
                f"{suburb} Melbourne specialist clinic services updates",
                f"{suburb} Melbourne healthcare facility investment",
                f"{suburb} Melbourne hospital waiting times performance"
            ]
            for query in queries:
                logger.info(f"医院搜索词: {query}")
                search_results = list(ddgs.text(query, max_results=10))
                logger.info(f"获取到 {len(search_results)} 条结果")
                
                for result in search_results:
                    if self._is_relevant('hospitals', result.get('body', '')):
                        results.append({
                            'title': result.get('title', ''),
                            'link': result.get('link', ''),
                            'summary': result.get('body', '')[:800],
                            'date': self._extract_date(result.get('body', ''))
                        })
        return results[:30]
    
    def _search_infrastructure(self, suburb: str) -> List[Dict]:
        """搜索该区域的基础设施发展"""
        results = []
        with DDGS() as ddgs:
            queries = [
                f"{suburb} Melbourne infrastructure budget investment amount",
                f"{suburb} Melbourne road transport upgrade cost timeline",
                f"{suburb} Melbourne community facility construction budget",
                f"{suburb} Melbourne council development spending details",
                f"{suburb} Melbourne infrastructure project completion date"
            ]
            for query in queries:
                logger.info(f"基建搜索词: {query}")
                search_results = list(ddgs.text(query, max_results=10))
                logger.info(f"获取到 {len(search_results)} 条结果")
                
                for result in search_results:
                    if self._is_relevant('infrastructure', result.get('body', '')):
                        results.append({
                            'title': result.get('title', ''),
                            'link': result.get('link', ''),
                            'summary': result.get('body', '')[:800],
                            'date': self._extract_date(result.get('body', ''))
                        })
        return results[:30]
    
    def _search_crime_stats(self, suburb: str) -> List[Dict]:
        """搜索该区域的犯罪统计"""
        results = []
        with DDGS() as ddgs:
            queries = [
                f"{suburb} Melbourne crime rate statistics",
                f"{suburb} Melbourne police reports incidents",
                f"{suburb} Melbourne safety data analysis"
            ]
            for query in queries:
                logger.info(f"治安搜索词: {query}")
                search_results = list(ddgs.text(query, max_results=10))
                logger.info(f"获取到 {len(search_results)} 条结果")
                
                for result in search_results:
                    if self._is_relevant('crime', result.get('body', '')):
                        results.append({
                            'title': result.get('title', ''),
                            'link': result.get('link', ''),
                            'summary': result.get('body', '')[:800],
                            'date': self._extract_date(result.get('body', ''))
                        })
        return results[:30]
    
    def _search_property_trends(self, suburb: str) -> List[Dict]:
        """搜索该区域的房产市场信息"""
        results = []
        with DDGS() as ddgs:
            queries = [
                f"{suburb} Melbourne property price trends",
                f"{suburb} Melbourne real estate market analysis",
                f"{suburb} Melbourne house median price data"
            ]
            for query in queries:
                logger.info(f"房产搜索词: {query}")
                search_results = list(ddgs.text(query, max_results=10))
                logger.info(f"获取到 {len(search_results)} 条结果")
                
                for result in search_results:
                    if self._is_relevant('property', result.get('body', '')):
                        results.append({
                            'title': result.get('title', ''),
                            'link': result.get('link', ''),
                            'summary': result.get('body', '')[:800],
                            'date': self._extract_date(result.get('body', ''))
                        })
        return results[:30]
    
    def _is_relevant(self, category: str, text: str) -> bool:
        """检查文本是否与指定类别相关"""
        keywords = self.categories[category]
        return any(keyword.lower() in text.lower() for keyword in keywords)
    
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