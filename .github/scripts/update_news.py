#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动爬取最新AI资讯并更新 newsData.json
v2: 扩大回溯范围、提高保留上限、智能排序去重
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
    
    formats = [
        '%Y-%m-%d',
        '%Y年%m月%d日',
        '%m月%d日',
        '%Y/%m/%d',
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str.strip(), fmt)
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.strftime('%Y-%m-%d')
        except:
            continue
    
    return datetime.now().strftime('%Y-%m-%d')

def scrape_aitop100(days_back=30):
    """爬取 AITOP100 的AI日报，可配置回溯天数"""
    news_list = []
    
    try:
        base_url = "https://www.aitop100.cn/ai-daily"
        
        for days_ago in range(days_back):
            date = datetime.now() - timedelta(days=days_ago)
            date_str = date.strftime('%Y-%m-%d')
            url = f"{base_url}-{date_str}"
            
            print(f"  爬取 AITOP100 [{days_ago+1}/{days_back}]: {url}")
            html = fetch_url(url)
            
            if not html:
                continue
            
            soup = BeautifulSoup(html, 'lxml')
            
            articles = soup.select('.news-item, .article-item, .post-item')
            
            if not articles:
                articles = soup.find_all(['article', 'div'], class_=re.compile('news|article|post'))
            
            for article in articles[:10]:
                try:
                    title_elem = article.find(['h2', 'h3', 'h4']) or article.find('a')
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    if not title or len(title) < 5:
                        continue
                    
                    link_elem = article.find('a', href=True)
                    link = link_elem['href'] if link_elem else ""
                    if link and not link.startswith('http'):
                        link = "https://www.aitop100.cn" + link
                    
                    summary_elem = article.find(['p', 'div'], class_=re.compile('summary|excerpt|desc'))
                    summary = summary_elem.get_text(strip=True)[:150] if summary_elem else title
                    
                    source_elem = article.find(['span', 'div'], class_=re.compile('source|author'))
                    source = source_elem.get_text(strip=True) if source_elem else "AITOP100"
                    
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
            
            time.sleep(0.5)
        
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
        
        items = soup.select('.newsflash-item, .article-item')
        
        for item in items[:15]:
            try:
                title_elem = item.find(['h2', 'h3']) or item.find('a')
                title = title_elem.get_text(strip=True) if title_elem else ""
                
                if not title or len(title) < 5:
                    continue
                
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
    
    # 数据源1: AITOP100（回溯30天）
    print("\n[1/3] 爬取 AITOP100（回溯30天）...")
    news1 = scrape_aitop100(days_back=30)
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

def get_sortable_date(item):
    """从新闻条目中提取可排序的日期键"""
    date_val = item.get('date', '')
    # 标准化日期格式用于排序
    try:
        if re.match(r'\d{4}-\d{2}-\d{2}', date_val):
            return date_val
        elif re.match(r'\d{1,2}月\d{1,2}日', date_val):
            # "7月4日" → "2026-07-04"
            m = re.match(r'(\d{1,2})月(\d{1,2})日', date_val)
            if m:
                return f"2026-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        elif re.match(r'\d{4}/\d{2}/\d{2}', date_val):
            return date_val.replace('/', '-')
        # 特殊日期描述（如 "智源2026十大趋势"）
        return '2026-01-01'
    except:
        return '2026-01-01'

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
    print("AI资讯自动更新脚本 v2")
    print("=" * 60)
    
    # 爬取最新资讯
    print("\n▶ 开始爬取最新AI资讯...")
    new_news = fetch_ai_news()
    
    # 加载现有数据
    print("\n▶ 加载现有数据...")
    existing_news = load_existing_news()
    print(f"  现有 {len(existing_news)} 条资讯")
    
    # 合并数据（去重，基于标题）
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
    
    # 按日期降序排序，确保保留最新内容
    print("\n▶ 排序与裁剪...")
    existing_news.sort(key=get_sortable_date, reverse=True)
    
    # 提高保留上限至 200 条（覆盖约半年到全年的资讯量）
    max_keep = 200
    if len(existing_news) > max_keep:
        removed = len(existing_news) - max_keep
        existing_news = existing_news[:max_keep]
        print(f"  裁剪了 {removed} 条最旧资讯（保留上限 {max_keep}）")
    
    print(f"  最终保留 {len(existing_news)} 条资讯")
    
    # 保存
    print("\n▶ 保存数据...")
    save_news(existing_news)
    
    # 统计
    print("\n" + "=" * 60)
    print("✓ 更新完成!")
    print(f"  总计: {len(existing_news)} 条")
    
    # 日期范围
    dates = []
    for item in existing_news:
        d = get_sortable_date(item)
        if d and d != '2026-01-01':
            dates.append(d)
    if dates:
        dates.sort()
        print(f"  覆盖: {dates[0]} ~ {dates[-1]}")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
