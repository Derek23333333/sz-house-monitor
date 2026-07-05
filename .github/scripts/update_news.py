#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI资讯聚合脚本 v4
国内直连RSS源聚合 + 严格质量过滤
"""

import json
import requests
from xml.etree import ElementTree as ET
from datetime import datetime
import re
import html as html_lib
import os
from email.utils import parsedate_to_datetime

# ============================================================
# 配置
# ============================================================
MAX_KEEP = 1000  # 保留上限

# 工作目录绝对路径
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE, 'temp', 'data')
DATA_FILE = os.path.join(DATA_DIR, 'newsData.json')
META_FILE = os.path.join(DATA_DIR, 'meta.json')

# AI 关键词（用于过滤 + 分类）
AI_KEYWORDS = [
    '人工智能', '大模型', 'LLM', 'GPT', 'Claude', 'ChatGPT', 'Gemini',
    '深度学习', '机器学习', '神经网络', '生成式', 'AIGC', 'Agent', '智能体',
    '具身智能', '人形机器人', '算力', 'GPU', '英伟达', 'NVIDIA', '训练', '推理',
    '多模态', '向量', 'RAG', '提示词', 'Prompt', '微调', 'Fine-tuning',
    'AI', 'Copilot', 'OpenAI', 'Anthropic', 'Stable Diffusion', 'Sora',
    '自动驾驶', '语音识别', '计算机视觉', 'NLP', '自然语言', 'Transformer',
    'QLoRA', 'LoRA', 'RLHF', 'Token', 'AI芯片', '智算', '智能',
    '模型', '算法', '数据标注', '知识图谱', 'AI原生',
]

# 可放宽的关键词（避免误过滤）
SOFT_KEYWORDS = ['AI', '智能', '模型', '算法']

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ============================================================
# 工具函数
# ============================================================

def clean_html(text):
    """去掉HTML标签，解码HTML实体"""
    if not text:
        return ''
    text = re.sub(r'<[^>]+>', '', text)
    text = html_lib.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_ai_related(title, summary=''):
    """判断是否AI相关"""
    text = f"{title} {summary}".lower()
    for kw in AI_KEYWORDS:
        if kw.lower() in text:
            return True
    return False

def assign_category(title, summary=''):
    """自动分配分类"""
    text = f"{title} {summary}"
    rules = [
        ('大模型', ['大模型', 'LLM', 'GPT', 'Claude', 'ChatGPT', 'Gemini', '参数', '开源', '微调', 'Fine-tun', 'LoRA', 'QLoRA']),
        ('新工具', ['发布', '开源', '上线', '推出', '更新', 'API', 'SDK', 'Copilot', '平台']),
        ('行业应用', ['落地', '应用', '产业', '企业', '商业化', '行业', '政务', '金融', '医疗', '教育', '制造']),
        ('政策', ['政策', '法规', '监管', '标准', '国家', '政府', '国务院', '工信部', '网信办']),
        ('新概念', ['趋势', '前沿', '研究', '论文', '科学', '概念', '突破', 'Meta', '未来']),
    ]
    for cat, kws in rules:
        for kw in kws:
            if kw in text:
                return cat
    return 'AI资讯'

def quality_check(title, summary, source=''):
    """质量过滤：返回 True 表示合格"""
    if not title or len(title) < 8:
        return False
    # 禁止标题含HTML标签
    if re.search(r'<[a-z/]', title):
        return False
    # 禁止标题是纯URL
    if title.startswith('http'):
        return False
    # 禁止摘要含原始URL碎片
    if summary and ('](http' in summary or summary.startswith('](')):
        return False
    # 禁止垃圾标题
    garbage_patterns = [
        r'^Trending now', r'^Top stories', r'^查看更多',
        r'^\d+天前', r'^今日AI快讯.*\d+天前',
    ]
    for pat in garbage_patterns:
        if re.search(pat, title):
            return False
    # 来源必须有意义
    if source in ('', '新闻', 'unknown', 'Unknown'):
        return False
    # 禁止纯开发工具版本发布（非AI内容）
    dev_tools = [
        r'^Memcached\s+\d', r'^TeamCity\s+\d', r'^Akka\s+\d',
        r'^Godot\s+', r'^GitHub\s.*原生\s?Stacked\s?PR',
    ]
    for pat in dev_tools:
        if re.search(pat, title):
            return False
    # 禁止比赛获奖名单/广告类
    if re.search(r'(获奖名单|大赛.*获奖|喜之郎)', title):
        return False
    return True

def parse_date(pubdate_str):
    """解析RSS发布日期"""
    if not pubdate_str:
        return datetime.now().strftime('%Y-%m-%d')
    try:
        dt = parsedate_to_datetime(pubdate_str)
        return dt.strftime('%Y-%m-%d')
    except:
        pass
    # 尝试常见格式
    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m月%d日']:
        try:
            return datetime.strptime(pubdate_str, fmt).strftime('%Y-%m-%d')
        except:
            pass
    return datetime.now().strftime('%Y-%m-%d')

# ============================================================
# RSS 源解析
# ============================================================

def scrape_infoq():
    """InfoQ 中文 RSS - RSS的description无实质内容，标题本身即为摘要"""
    items = []
    try:
        print("  [InfoQ] 抓取中...")
        r = requests.get('https://www.infoq.cn/feed', headers=HEADERS, timeout=15)
        root = ET.fromstring(r.content)
        for item in root.findall('.//item'):
            title = clean_html(item.findtext('title', ''))
            link = item.findtext('link', '')
            pubdate = item.findtext('pubDate', '')
            author = item.findtext('author', '')
            
            # InfoQ RSS的description仅为"点击查看原文>"，无实质内容
            # 用标题作为摘要，附加作者信息
            summary = title
            if author and author.startswith('作者：'):
                author_name = author[3:].strip()
                if author_name not in title:
                    summary = f"【{author_name}】{title}"
            
            if not quality_check(title, summary, 'InfoQ'):
                continue
            if not is_ai_related(title, summary):
                continue
            
            items.append({
                'title': title,
                'summary': summary[:200],
                'source': 'InfoQ',
                'link': link,
                'date': parse_date(pubdate),
                'category': assign_category(title, summary),
            })
        print(f"  [InfoQ] ✓ {len(items)} 条")
    except Exception as e:
        print(f"  [InfoQ] ✗ {e}")
    return items

def scrape_sspai():
    """少数派 RSS"""
    items = []
    try:
        print("  [少数派] 抓取中...")
        r = requests.get('https://sspai.com/feed', headers=HEADERS, timeout=15)
        root = ET.fromstring(r.content)
        for item in root.findall('.//item'):
            title = clean_html(item.findtext('title', ''))
            link = item.findtext('link', '')
            pubdate = item.findtext('pubDate', '')
            desc = clean_html(item.findtext('description', ''))
            
            if not quality_check(title, desc, '少数派'):
                continue
            if not is_ai_related(title, desc):
                continue
            
            items.append({
                'title': title,
                'summary': desc[:200] if desc else title,
                'source': '少数派',
                'link': link,
                'date': parse_date(pubdate),
                'category': assign_category(title, desc),
            })
        print(f"  [少数派] ✓ {len(items)} 条")
    except Exception as e:
        print(f"  [少数派] ✗ {e}")
    return items

def scrape_oschina():
    """开源中国 RSS - 加重试"""
    items = []
    try:
        print("  [开源中国] 抓取中...")
        for attempt in range(3):
            try:
                r = requests.get('https://www.oschina.net/news/rss', headers=HEADERS, timeout=15)
                break
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"    重试 {attempt+1}/3: {e}")
                import time
                time.sleep(2)
        root = ET.fromstring(r.content)
        for item in root.findall('.//item'):
            title = clean_html(item.findtext('title', ''))
            link = item.findtext('link', '')
            pubdate = item.findtext('pubDate', '')
            desc = clean_html(item.findtext('description', ''))
            
            if not quality_check(title, desc, '开源中国'):
                continue
            if not is_ai_related(title, desc):
                continue
            
            items.append({
                'title': title,
                'summary': desc[:200] if desc else title,
                'source': '开源中国',
                'link': link,
                'date': parse_date(pubdate),
                'category': assign_category(title, desc),
            })
        print(f"  [开源中国] ✓ {len(items)} 条")
    except Exception as e:
        print(f"  [开源中国] ✗ {e}")
    return items

def scrape_v2ex():
    """V2EX RSS - 技术社区，过滤无关内容后保留AI相关讨论"""
    items = []
    # 排除的标题模式（账号购买/被封/中转站等非资讯讨论）
    noise_patterns = [
        r'(被封|封号|封了|转中站|中转站|续费|里拉|plus\s*还是|渠道.*买|价廉物美|白嫖|注册.*送)',
        r'(被封|封禁|ban)',
    ]
    try:
        print("  [V2EX] 抓取中...")
        for tab in ['tech', 'creative']:
            try:
                r = requests.get(f'https://www.v2ex.com/feed/tab/{tab}.xml', headers=HEADERS, timeout=15)
                root = ET.fromstring(r.content)
                for item in root.findall('.//{http://www.w3.org/2005/Atom}entry'):
                    title = clean_html(item.findtext('{http://www.w3.org/2005/Atom}title', ''))
                    link_el = item.find('{http://www.w3.org/2005/Atom}link')
                    link = link_el.get('href', '') if link_el is not None else ''
                    pubdate = item.findtext('{http://www.w3.org/2005/Atom}updated', '')
                    
                    if not quality_check(title, title, 'V2EX'):
                        continue
                    if not is_ai_related(title):
                        continue
                    # 排除账号购买/被封/中转站类讨论
                    if any(re.search(pat, title) for pat in noise_patterns):
                        continue
                    
                    items.append({
                        'title': title,
                        'summary': title,
                        'source': 'V2EX',
                        'link': link,
                        'date': parse_date(pubdate),
                        'category': assign_category(title),
                    })
            except:
                pass
        print(f"  [V2EX] ✓ {len(items)} 条")
    except Exception as e:
        print(f"  [V2EX] ✗ {e}")
    return items

# ============================================================
# 数据处理
# ============================================================

def load_existing():
    """加载现有数据，只保留高质量条目"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            raw = json.load(f)
    except:
        return []
    
    clean = []
    for item in raw:
        title = item.get('title', '')
        summary = item.get('summary', '')
        source = item.get('source', '')
        
        # 保留有 audience 或 detail 字段的（手动录入的高质量条目）
        if item.get('audience') or item.get('detail'):
            item.pop('dateRaw', None)
            clean.append(item)
            continue
        
        # 质量检查通过的自动抓取条目也保留
        if quality_check(title, summary, source):
            item.pop('dateRaw', None)
            # 统一字段名：sourceUrl → link
            if 'sourceUrl' in item and 'link' not in item:
                item['link'] = item.pop('sourceUrl')
            clean.append(item)
    
    return clean

def deduplicate(items):
    """去重：按标题相似度"""
    seen = set()
    unique = []
    for item in items:
        # 标准化标题用于去重
        norm = re.sub(r'\s+', '', item.get('title', '')).lower()
        # 取前30个字符做模糊去重
        key = norm[:30]
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique

def get_sortable_date(item):
    """获取可排序的日期字符串"""
    date_val = item.get('date', '')
    try:
        if re.match(r'\d{4}-\d{2}-\d{2}', date_val):
            return date_val
        elif re.match(r'\d{1,2}月\d{1,2}日', date_val):
            m = re.match(r'(\d{1,2})月(\d{1,2})日', date_val)
            if m:
                return f"2026-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
        return '2026-01-01'
    except:
        return '2026-01-01'

def save_news(items):
    """保存到 newsData.json"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 已保存 {len(items)} 条")
    except Exception as e:
        print(f"  ✗ 保存失败: {e}")

def update_meta(count):
    """更新 meta.json"""
    try:
        try:
            with open(META_FILE, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except:
            meta = {}
        now = datetime.now()
        meta['lastUpdated'] = now.strftime('%Y-%m-%d')
        meta['lastUpdatedTime'] = now.strftime('%Y-%m-%d %H:%M:%S')
        raw_ver = meta.get('version', '0')
        try:
            meta['version'] = int(raw_ver) + 1
        except (ValueError, TypeError):
            meta['version'] = 1
        meta['totalCount'] = count
        with open(META_FILE, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"  ✓ meta 已更新")
    except Exception as e:
        print(f"  ✗ meta 更新失败: {e}")

# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("AI资讯聚合脚本 v4 (国内 RSS 聚合)")
    print("=" * 60)
    
    # 1. 抓取新数据
    print("\n▶ 抓取中...")
    new_items = []
    for scraper in [scrape_infoq, scrape_sspai, scrape_oschina, scrape_v2ex]:
        new_items.extend(scraper())
    
    # 去重
    new_items = deduplicate(new_items)
    print(f"\n  抓取去重后: {len(new_items)} 条")
    
    # 2. 加载并清洗现有数据
    print("\n▶ 清洗现有数据...")
    existing = load_existing()
    manual_count = sum(1 for item in existing if item.get('audience'))
    print(f"  保留手动录入: {manual_count} 条")
    print(f"  保留合格抓取: {len(existing) - manual_count} 条")
    
    # 3. 合并
    print("\n▶ 合并...")
    existing_titles = {item.get('title', '') for item in existing}
    added = 0
    for item in new_items:
        title = item.get('title', '')
        if title and title not in existing_titles:
            existing.append(item)
            existing_titles.add(title)
            added += 1
    print(f"  新增: {added} 条")
    
    # 4. 排序 & 裁剪
    existing.sort(key=get_sortable_date, reverse=True)
    before_cut = len(existing)
    if len(existing) > MAX_KEEP:
        existing = existing[:MAX_KEEP]
        print(f"  裁剪: {before_cut - MAX_KEEP} 条 (上限 {MAX_KEEP})")
    
    # 5. 分类统计
    cats = {}
    for item in existing:
        cat = item.get('category', '未知')
        cats[cat] = cats.get(cat, 0) + 1
    print(f"  分类: {cats}")
    
    # 6. 保存
    print("\n▶ 保存...")
    save_news(existing)
    update_meta(len(existing))
    
    # 7. 日期范围
    dates = [get_sortable_date(x) for x in existing if x.get('date')]
    dates = sorted(set(d for d in dates if d > '2026-01-01'))
    
    print("\n" + "=" * 60)
    print(f"✓ 完成! 共 {len(existing)} 条")
    if dates:
        print(f"  覆盖: {dates[0]} ~ {dates[-1]}")
    print("=" * 60)

if __name__ == '__main__':
    main()
