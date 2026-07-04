#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动爬取最新AI资讯并更新 newsData.json
支持多个数据源，带错误处理和去重
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re

def fetch_url(url, headers=None, timeout=10):
    """安全地获取URL内容"""
    try:
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except Exception as e:
        print(f"✗ 获取 {url} 失败: {e}")
        return None

def parse_date(date_str):
    """解析各种日期格式"""
    if not date_str:
        return datetime.now().strftime('%Y-%m-%d')
    
    # 尝试多种日期格式
    formats = [
        '%Y-%m-%d',
        '%Y年%m月%d日',
        '%m月%d日',
        '%Y/%m/%d',
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            if parsed.year == 1900:  # 只有月日的情况
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.strftime('%Y-%m-%d')
        except:
            continue
    
    return datetime.now().strftime('%Y-%m-%d')

def scrape_aitop100():
    """爬取 AITOP100 的AI日报"""
    news_list = []
    
    try:
        # 获取最近3天的日报
        base_url = "https://www.aitop100.cn/ai-daily"
        
        for days_ago in range(3):
            date = datetime.now() - timedelta(days=days_ago)
            date_str = date.strftime('%Y-%m-%d')
            url = f"{base_url}-{date_str}"
            
            print(f"  爬取 AITOP100: {url}")
            html = fetch_url(url)
            
            if not html:
                continue
            
            soup = BeautifulSoup(html, 'lxml')
            
            # 查找新闻条目（根据实际页面结构调整）
            articles = soup.select('.news-item, .article-item, .post-item')
            
            if not articles:
                # 尝试其他选择器
                articles = soup.find_all(['article', 'div'], class_=re.compile('news|article|post'))
            
            for article in articles[:10]:  # 每天最多10条
                try:
                    # 提取标题
                    title_elem = article.find(['h2', 'h3', 'h4']) or article.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    if not title or len(title) < 5:
                        continue
                    
                    # 提取链接
                    link_elem = article.find('a', href=True)
                    link = link_elem['href'] if link_elem else ""
                    if link and not link.startswith('http'):
                        link = "https://www.aitop100.cn" + link
                    
                    # 提取摘要
                    summary_elem = article.find(['p', 'div'], class_=re.compile('summary|excerpt|desc'))
                    summary = summary_elem.get_text(strip=True)[:150] if summary_elem else title
                    
                    # 提取来源
                    source_elem = article.find(['span', 'div'], class_=re.compile('source|author'))
                    source = source_elem.get_text(strip=True) if source_elem else "AITOP100"
                    
                    # 分类
                    category = "AI资讯"
                    if any(kw in title + summary for kw in ['大模型', 'GPT', 'Claude', 'Gemini']):
                        category = "大模型"
                    elif any(kw in title + summary for kw in ['工具', '应用', '平台']):
                        category = "新工具"
                    elif any(kw in title + summary for kw in ['行业', '医疗', '教育', '金融']):
                        category = "行业应用"
                    
                    news_list.append({
                        'title': title,
                        'summary': summary,
                        'source': source,
                        'date': date_str,
                        'category': category,
                        'link': link
                    })
                    
                except Exception as e:
                    print(f"    ✗ 解析文章失败: {e}")
                    continue
            
            time.sleep(1)  # 礼貌爬取
        
    except Exception as e:
        print(f"✗ 爬取 AITOP100 失败: {e}")
    
    return news_list

def scrape_36kr_ai():
    """爬取 36氪 AI频道"""
    news_list = []
    
    try:
        url = "https://36kr.com/newsflashes"
        print(f"  爬取 36氪: {url}")
        
        html = fetch_url(url)
        if not html:
            return news_list
        
        soup = BeautifulSoup(html, 'lxml')
        
        # 查找快讯条目
        items = soup.select('.newsflash-item, .article-item')
        
        for item in items[:15]:
            try:
                title_elem = item.find(['h2', 'h3']) or item.find('a')
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title or len(title) < 5:
                    continue
                
                # 检查是否是AI相关
                if not any(kw in title for kw in ['AI', '人工智能', '大模型', 'GPT', '智能']):
                    continue
                
                summary = title
                source = "36氪"
                date = datetime.now().strftime('%Y-%m-%d')
                category = "AI资讯"
                
                news_list.append({
                    'title': title,
                    'summary': summary,
                    'source': source,
                    'date': date,
                    'category': category,
                    'link': ""
                })
                
            except Exception as e:
                continue
        
    except Exception as e:
        print(f"✗ 爬取 36氪 失败: {e}")
    
    return news_list

def scrape_jiqizhixin():
    """爬取 机器之心"""
    news_list = []
    
    try:
        url = "https://www.jiqizhixin.com/"
        print(f"  爬取 机器之心: {url}")
        
        html = fetch_url(url)
        if not html:
            return news_list
        
        soup = BeautifulSoup(html, 'lxml')
        
        articles = soup.select('.article-item, .post-item')
        
        for article in articles[:10]:
            try:
                title_elem = article.find(['h2', 'h3'])
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title or len(title) < 5:
                    continue
                
                summary_elem = article.find(['p', 'div'], class_=re.compile('summary|excerpt'))
                summary = summary_elem.get_text(strip=True)[:150] if summary_elem else title
                
                news_list.append({
                    'title': title,
                    'summary': summary,
                    'source': '机器之心',
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'category': 'AI资讯',
                    'link': ""
                })
                
            except Exception as e:
                continue
        
    except Exception as e:
        print(f"✗ 爬取 机器之心 失败: {e}")
    
    return news_list

def fetch_ai_news():
    """爬取最新AI资讯 - 主函数"""
    
    all_news = []
    
    # 数据源1: AITOP100
    print("\n[1/3] 爬取 AITOP100...")
    news1 = scrape_aitop100()
    print(f"  ✓ 获取到 {len(news1)} 条")
    all_news.extend(news1)
    
    # 数据源2: 36氪
    print("\n[2/3] 爬取 36氪...")
    news2 = scrape_36kr_ai()
    print(f"  ✓ 获取到 {len(news2)} 条")
    all_news.extend(news2)
    
    # 数据源3: 机器之心
    print("\n[3/3] 爬取 机器之心...")
    news3 = scrape_jiqizhixin()
    print(f"  ✓ 获取到 {len(news3)} 条")
    all_news.extend(news3)
    
    # 去重（根据标题）
    seen_titles = set()
    unique_news = []
    for news in all_news:
        title = news.get('title', '')
        if title and title not in seen_titles:
            seen_titles.add(title)
            unique_news.append(news)
    
    print(f"\n✓ 总计获取到 {len(unique_news)} 条 unique AI资讯")
    
    return unique_news

def load_existing_news():
    """加载现有的新闻数据"""
    try:
        with open('data/newsData.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"✗ 加载现有数据失败: {e}")
        return []

def save_news(news_list):
    """保存新闻数据"""
    try:
        with open('data/newsData.json', 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)
        
        # 更新meta.json
        try:
            with open('data/meta.json', 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            now = datetime.now()
            meta['lastUpdated'] = now.strftime('%Y-%m-%d')
            meta['lastUpdatedTime'] = now.strftime('%Y-%m-%d %H:%M:%S')
            meta['version'] = meta.get('version', 1) + 1
            
            with open('data/meta.json', 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            
            print(f"✓ 已更新 meta.json (版本 {meta['version']})")
        except Exception as e:
            print(f"✗ 更新 meta.json 失败: {e}")
        
        print(f"✓ 已保存 {len(news_list)} 条资讯到 newsData.json")
    except Exception as e:
        print(f"✗ 保存失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("AI资讯自动更新脚本")
    print("=" * 60)
    
    # 爬取最新资讯
    print("\n▶ 开始爬取最新AI资讯...")
    new_news = fetch_ai_news()
    
    if not new_news:
        print("\n✗ 没有获取到新资讯，保持现有数据")
        return
    
    # 加载现有数据
    print("\n▶ 加载现有数据...")
    existing_news = load_existing_news()
    print(f"  现有 {len(existing_news)} 条资讯")
    
    # 合并数据（去重）
    print("\n▶ 合并数据...")
    existing_titles = {n.get('title', '') for n in existing_news}
    
    added_count = 0
    for news in new_news:
        title = news.get('title', '')
        if title and title not in existing_titles:
            existing_news.insert(0, news)
            existing_titles.add(title)
            added_count += 1
    
    print(f"  添加了 {added_count} 条新资讯")
    
    # 只保留最新30条
    existing_news = existing_news[:30]
    
    # 保存
    print("\n▶ 保存数据...")
    save_news(existing_news)
    
    print("\n" + "=" * 60)
    print("✓ 更新完成!")
    print("=" * 60)

if __name__ == '__main__':
    main()
