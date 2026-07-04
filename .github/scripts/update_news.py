#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动爬取最新AI资讯并更新 newsData.json
v3: 基于搜索引擎聚合（替代失效的固定站点爬虫）
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import urllib.parse

def fetch_url(url, headers=None, timeout=15):
    try:
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = 'utf-8'
        return resp.text
    except Exception as e:
        print(f"  ✗ {url[:60]}... 失败: {e}")
        return None

def search_bing_news(query, count=15, days_back=0):
    """通过Bing搜索AI新闻（实际搜索页面）"""
    news_list = []

    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.bing.com/news/search?q={encoded}&count={count}&qft=interval%3d%227%22"
        print(f"  Bing搜索: {query}")
        
        html = fetch_url(url)
        if not html:
            return news_list
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Bing新闻卡片
        cards = soup.select('.news-card, .newsitem, article')
        if not cards:
            cards = soup.find_all('div', class_=re.compile('news|card|item'))
        
        for card in cards[:count]:
            try:
                # 标题
                title_elem = card.find(['h2', 'h3', 'h4']) or card.find('a', class_=re.compile('title'))
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title or len(title) < 8:
                    continue
                
                # 链接
                link = ""
                link_elem = card.find('a', href=True)
                if link_elem:
                    link = link_elem['href']
                
                # 摘要
                snippet = card.find(['p', 'div'], class_=re.compile('snippet|desc|body|content'))
                summary = snippet.get_text(strip=True)[:200] if snippet else title
                
                # 来源
                source_elem = card.find(['span', 'cite'], class_=re.compile('source|provider|attribution'))
                source = source_elem.get_text(strip=True) if source_elem else "新闻"
                
                news_list.append({
                    'title': title,
                    'summary': summary,
                    'source': source,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'dateRaw': datetime.now().strftime('%Y-%m-%d'),
                    'category': 'AI资讯',
                    'link': link
                })
            except:
                continue
        
    except Exception as e:
        print(f"  ✗ Bing搜索失败: {e}")
    
    return news_list

def scrape_aitop100_info():
    """爬取 AITOP100 资讯列表页"""
    news_list = []
    
    try:
        # AITOP100的资讯列表页（注意URL拼写）
        urls = [
            "https://aitop100.cn/infomation/",
            "https://www.aitop100.cn/infomation/",
        ]
        
        for url in urls:
            print(f"  AITOP100: {url}")
            html = fetch_url(url)
            if not html:
                continue
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找文章列表
            articles = soup.select('.infomation-item, .article-item, .news-item, .post-item')
            if not articles:
                articles = soup.find_all(['article', 'div'], class_=re.compile('info|article|news|post'))
            
            for article in articles[:20]:
                try:
                    title_elem = article.find(['h2', 'h3', 'h4', 'a'], class_=re.compile('title'))
                    if not title_elem:
                        title_elem = article.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    if not title or len(title) < 5:
                        continue
                    
                    link = ""
                    link_elem = article.find('a', href=True)
                    if link_elem:
                        link = link_elem['href']
                        if link and not link.startswith('http'):
                            link = "https://www.aitop100.cn" + link
                    
                    summary_elem = article.find(['p', 'div'], class_=re.compile('desc|summary|excerpt'))
                    summary = summary_elem.get_text(strip=True)[:200] if summary_elem else title
                    
                    # 提取日期
                    date_elem = article.find(['span', 'time'], class_=re.compile('date|time'))
                    date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y-%m-%d')
                    
                    news_list.append({
                        'title': title,
                        'summary': summary,
                        'source': 'AITOP100',
                        'date': date_str if re.match(r'\d{4}-\d{2}-\d{2}', date_str) else datetime.now().strftime('%Y-%m-%d'),
                        'dateRaw': datetime.now().strftime('%Y-%m-%d'),
                        'category': 'AI资讯',
                        'link': link
                    })
                except:
                    continue
            
            if news_list:
                break
    
    except Exception as e:
        print(f"  ✗ AITOP100失败: {e}")
    
    return news_list

def scrape_google_news_rss():
    """通过 Google News RSS 获取AI资讯"""
    news_list = []
    
    try:
        # Google News RSS
        url = "https://news.google.com/rss/search?q=AI+人工智能+大模型&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
        print(f"  Google News RSS")
        
        html = fetch_url(url)
        if not html:
            return news_list
        
        soup = BeautifulSoup(html, 'xml')
        items = soup.find_all('item')[:20]
        
        for item in items:
            try:
                title = item.find('title').get_text(strip=True) if item.find('title') else ""
                if not title:
                    continue
                
                # 去掉来源后缀
                title = re.sub(r'\s*-\s*\S+$', '', title)
                
                link = item.find('link').get_text(strip=True) if item.find('link') else ""
                pub_date = item.find('pubDate')
                date_str = datetime.now().strftime('%Y-%m-%d')
                if pub_date:
                    try:
                        from email.utils import parsedate_to_datetime
                        date_str = parsedate_to_datetime(pub_date.get_text()).strftime('%Y-%m-%d')
                    except:
                        pass
                
                source_elem = item.find('source')
                source = source_elem.get_text(strip=True) if source_elem else "新闻"
                
                desc = item.find('description')
                summary = desc.get_text(strip=True)[:200] if desc else title
                
                news_list.append({
                    'title': title,
                    'summary': summary,
                    'source': source,
                    'date': date_str,
                    'dateRaw': datetime.now().strftime('%Y-%m-%d'),
                    'category': 'AI资讯',
                    'link': link
                })
            except:
                continue
        
    except Exception as e:
        print(f"  ✗ Google News失败: {e}")
    
    return news_list

def fetch_ai_news():
    """聚合所有数据源"""
    all_news = []
    
    # 源1: Google News RSS
    print("\n[1/3] Google News RSS...")
    n1 = scrape_google_news_rss()
    print(f"  ✓ {len(n1)} 条")
    all_news.extend(n1)
    
    # 源2: AITOP100 资讯列表
    print("\n[2/3] AITOP100 资讯列表...")
    n2 = scrape_aitop100_info()
    print(f"  ✓ {len(n2)} 条")
    all_news.extend(n2)
    
    # 源3: Bing搜索
    print("\n[3/3] Bing搜索...")
    n3 = search_bing_news("AI 人工智能 大模型 最新资讯")
    print(f"  ✓ {len(n3)} 条")
    all_news.extend(n3)
    
    # 去重
    seen = set()
    unique = []
    for n in all_news:
        t = n.get('title', '').strip()
        if t and t not in seen:
            seen.add(t)
            unique.append(n)
    
    print(f"\n总计 unique: {len(unique)} 条")
    return unique

def get_sortable_date(item):
    date_val = item.get('date', '')
    try:
        if re.match(r'\d{4}-\d{2}-\d{2}', date_val):
            return date_val
        elif re.match(r'\d{1,2}月\d{1,2}日', date_val):
            m = re.match(r'(\d{1,2})月(\d{1,2})日', date_val)
            if m:
                return f"2026-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        elif re.match(r'\d{4}/\d{2}/\d{2}', date_val):
            return date_val.replace('/', '-')
        return '2026-01-01'
    except:
        return '2026-01-01'

def load_existing_news():
    try:
        with open('data/newsData.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_news(news_list):
    try:
        with open('data/newsData.json', 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)
        
        try:
            with open('data/meta.json', 'r', encoding='utf-8') as f:
                meta = json.load(f)
            now = datetime.now()
            meta['lastUpdated'] = now.strftime('%Y-%m-%d')
            meta['lastUpdatedTime'] = now.strftime('%Y-%m-%d %H:%M:%S')
            meta['version'] = meta.get('version', 1) + 1
            with open('data/meta.json', 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        except:
            pass
        
        print(f"✓ 已保存 {len(news_list)} 条")
    except Exception as e:
        print(f"✗ 保存失败: {e}")

def main():
    print("=" * 60)
    print("AI资讯聚合脚本 v3 (搜索引擎聚合)")
    print("=" * 60)
    
    print("\n▶ 聚合最新AI资讯...")
    new_news = fetch_ai_news()
    
    print("\n▶ 加载现有数据...")
    existing = load_existing_news()
    print(f"  现有 {len(existing)} 条")
    
    # 合并去重
    existing_titles = {n.get('title', '') for n in existing}
    added = 0
    for news in new_news:
        title = news.get('title', '')
        if title and title not in existing_titles:
            existing.append(news)
            existing_titles.add(title)
            added += 1
    
    print(f"  新增 {added} 条")
    
    # 排序，保留200条
    existing.sort(key=get_sortable_date, reverse=True)
    if len(existing) > 200:
        removed = len(existing) - 200
        existing = existing[:200]
        print(f"  裁剪 {removed} 条（上限200）")
    
    # 清理内部字段
    for item in existing:
        item.pop('dateRaw', None)
    
    print(f"\n▶ 保存...")
    save_news(existing)
    
    dates = [get_sortable_date(x) for x in existing if x.get('date')]
    dates = sorted(set(d for d in dates if d != '2026-01-01'))
    
    print("\n" + "=" * 60)
    print(f"✓ 完成! 共 {len(existing)} 条")
    if dates:
        print(f"  覆盖: {dates[0]} ~ {dates[-1]}")
    print("=" * 60)

if __name__ == '__main__':
    main()
