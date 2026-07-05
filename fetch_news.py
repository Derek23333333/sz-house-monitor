#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B端思维·进阶工作台 - 资讯抓取脚本
从多个 ToB 行业资讯源抓取最新文章，输出 data.json。
由 GitHub Actions 每日定时运行。

数据源：
  1. 牛透社 (niutoushe.com) - SaaS/ToB 垂直媒体
  2. 36氪企服频道 (36kr.com) - 企服资讯
  3. 云头条 (IDC圈 cloud.idcquan.com) - 云计算/ToB 资讯

输出：仓库根目录的 data.json
"""

import json
import os
import sys
import time
import hashlib
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ---------- 配置 ----------
OUTPUT_FILE = "data.json"
REQUEST_TIMEOUT = 15  # 秒
REQUEST_INTERVAL = 2  # 请求间隔（秒）
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def fetch_html(url, timeout=REQUEST_TIMEOUT):
    """安全地获取网页 HTML"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text
    except Exception as e:
        print(f"  [WARN] 请求失败 {url}: {e}")
        return None


def extract_niutoushe():
    """
    抓取牛透社 (niutoushe.com) 首页资讯。
    页面结构：文章列表页, 标题在 <a> 标签内。
    """
    source = "牛透社"
    url = "https://www.niutoushe.com/"
    print(f"[抓取] {source}: {url}")

    html = fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    articles = []

    # 尝试多种选择器适配页面结构变化
    selectors = [
        "article", "div.post-item", "div.article-item",
        "li.news-item", "div.news-list-item", "div.content-item",
        "div.list-item", "div.post"
    ]

    items = []
    for sel in selectors:
        items = soup.select(sel)
        if items:
            print(f"    使用选择器: {sel}, 找到 {len(items)} 条")
            break

    if not items:
        # 回退：找所有带链接的标题
        print("    未找到结构化列表，使用通用提取...")
        links = soup.find_all("a", href=True)
        for a in links:
            text = a.get_text(strip=True)
            href = a.get("href", "")
            if len(text) > 8 and len(text) < 100 and href and "http" in href:
                articles.append({
                    "title": text,
                    "summary": "",
                    "source": source,
                    "link": href if href.startswith("http") else url.rstrip("/") + "/" + href.lstrip("/")
                })
        return articles

    for item in items:
        try:
            title_el = item.find("a") or item.find(["h2", "h3", "h4"])
            if not title_el:
                continue
            a_tag = title_el if title_el.name == "a" else title_el.find("a")
            title = a_tag.get_text(strip=True) if a_tag else title_el.get_text(strip=True)
            link = a_tag.get("href", "") if a_tag else ""
            if link and not link.startswith("http"):
                link = "https://www.niutoushe.com" + link

            summary_el = item.find(["p", "div.summary", "div.excerpt", "div.desc"])
            summary = summary_el.get_text(strip=True) if summary_el else ""

            if title and len(title) > 4:
                articles.append({
                    "title": title,
                    "summary": summary[:200] if summary else "",
                    "source": source,
                    "link": link
                })
        except Exception as e:
            continue

    return articles


def extract_36kr():
    """
    抓取 36氪 企服频道资讯。
    页面结构：信息流列表。
    """
    source = "36氪企服"
    url = "https://36kr.com/information/enterprise_service/"
    print(f"[抓取] {source}: {url}")

    html = fetch_html(url)
    if not html:
        # 尝试备用URL
        url2 = "https://www.36kr.com/information/enterprise_service/"
        print(f"[抓取] {source} 备用: {url2}")
        html = fetch_html(url2)
        if not html:
            return []

    soup = BeautifulSoup(html, "lxml")
    articles = []

    # 36氪页面结构：文章在 article-item 或信息流容器中
    selectors = [
        "div.article-item-wrapper", "div.article-item",
        "div.kr-flow-article-item", "div.newsflash-item",
        "div.information-list-item", "a.item-title"
    ]

    items = []
    for sel in selectors:
        items = soup.select(sel)
        if items:
            print(f"    使用选择器: {sel}, 找到 {len(items)} 条")
            break

    if not items:
        print("    未找到结构化列表，搜索 JSON 数据...")
        # 尝试从页面 script 标签中提取 JSON 数据
        scripts = soup.find_all("script")
        for script in scripts:
            text = script.string or ""
            if "itemList" in text or "articleList" in text or "newsList" in text:
                try:
                    # 尝试找 JSON 数据
                    import re
                    matches = re.findall(r'"title":"([^"]+)"', text)
                    link_matches = re.findall(r'"link":"([^"]+)"', text) or re.findall(r'"url":"([^"]+)"', text)
                    desc_matches = re.findall(r'"description":"([^"]+)"', text) or re.findall(r'"summary":"([^"]+)"', text)
                    for i, t in enumerate(matches[:10]):
                        articles.append({
                            "title": t,
                            "summary": desc_matches[i] if i < len(desc_matches) else "",
                            "source": source,
                            "link": link_matches[i] if i < len(link_matches) else ""
                        })
                    if articles:
                        break
                except Exception:
                    continue
        return articles

    for item in items:
        try:
            a_tag = item.find("a") if item.name != "a" else item
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            link = a_tag.get("href", "")
            if link and not link.startswith("http"):
                link = "https://36kr.com" + link

            if title and len(title) > 4:
                articles.append({
                    "title": title,
                    "summary": "",
                    "source": source,
                    "link": link
                })
        except Exception:
            continue

    return articles


def extract_cloud_idc():
    """
    抓取中国IDC圈/云头条资讯 (cloud.idcquan.com)。
    页面结构：资讯列表。
    """
    source = "IDC圈"
    url = "https://cloud.idcquan.com/"
    print(f"[抓取] {source}: {url}")

    html = fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    articles = []

    selectors = [
        "div.news-list li", "div.list-item", "div.article-list-item",
        "div.news-item", "li.item", "div.text-list-item"
    ]

    items = []
    for sel in selectors:
        items = soup.select(sel)
        if items:
            print(f"    使用选择器: {sel}, 找到 {len(items)} 条")
            break

    if not items:
        links = soup.find_all("a", href=True)
        for a in links:
            text = a.get_text(strip=True)
            href = a.get("href", "")
            if len(text) > 6 and len(text) < 120:
                articles.append({
                    "title": text,
                    "summary": "",
                    "source": source,
                    "link": href if href.startswith("http") else "https://cloud.idcquan.com" + href
                })
        return articles

    for item in items:
        try:
            a_tag = item.find("a")
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            link = a_tag.get("href", "")
            if link and not link.startswith("http"):
                link = "https://cloud.idcquan.com" + link

            if title and len(title) > 4:
                articles.append({
                    "title": title,
                    "summary": "",
                    "source": source,
                    "link": link
                })
        except Exception:
            continue

    return articles


def extract_infoq():
    """
    抓取 InfoQ 中文站 云计算/AI 资讯。
    """
    source = "InfoQ"
    url = "https://www.infoq.cn/topic/cloud"
    print(f"[抓取] {source}: {url}")

    html = fetch_html(url)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    articles = []

    selectors = ["div.article-list-item", "div.article-item", "a.article-title", "a.card-title"]

    items = []
    for sel in selectors:
        items = soup.select(sel)
        if items:
            print(f"    使用选择器: {sel}, 找到 {len(items)} 条")
            break

    if not items:
        links = soup.find_all("a", href=True)
        for a in links:
            text = a.get_text(strip=True)
            href = a.get("href", "")
            if len(text) > 6 and ("cloud" in href.lower() or "article" in href.lower() or "news" in href.lower()):
                articles.append({
                    "title": text,
                    "summary": "",
                    "source": source,
                    "link": href if href.startswith("http") else "https://www.infoq.cn" + href
                })
        return articles

    for item in items:
        try:
            a_tag = item if item.name == "a" else item.find("a")
            if not a_tag:
                continue
            title = a_tag.get_text(strip=True)
            link = a_tag.get("href", "")
            if not link.startswith("http"):
                link = "https://www.infoq.cn" + link

            if title and len(title) > 4:
                articles.append({
                    "title": title,
                    "summary": "",
                    "source": source,
                    "link": link
                })
        except Exception:
            continue

    return articles


def dedup_articles(articles):
    """按标题去重"""
    seen = set()
    result = []
    for a in articles:
        key = hashlib.md5(a["title"].strip().encode("utf-8")).hexdigest()
        if key not in seen:
            seen.add(key)
            result.append(a)
    return result


def clean_title(title):
    """清洗标题：去掉前后空白、多余空格、特殊字符"""
    import re
    title = title.strip()
    title = re.sub(r"\s+", " ", title)
    return title


def filter_relevant(articles):
    """
    过滤：只保留与 ToB/SaaS/企业服务/云计算/AI企业应用 相关的文章。
    如果源本身就是 ToB 垂直媒体，则全部保留（最多20条）。
    """
    keywords = [
        "SaaS", "企业", "B端", "ToB", "数字化", "云", "AI", "软件",
        "平台", "服务", "管理", "协同", "办公", "ERP", "CRM", "HR",
        "财务", "采购", "供应链", "安全", "合规", "信创", "融资",
        "上线", "产品", "研发", "运维", "大模型", "低代码", "无代码",
        "自动化", "客户", "销售", "营销", "数据", "智能", "解决方案"
    ]

    def is_relevant(article):
        text = article["title"] + article.get("summary", "")
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)

    relevant = [a for a in articles if is_relevant(a)]

    # 如果过滤后太少（<3），放宽条件全部保留
    if len(relevant) < 3:
        return articles[:20]

    return relevant[:20]


def main():
    print("=" * 60)
    print(f"B端思维·进阶工作台 - 资讯抓取 [{datetime.now().isoformat()}]")
    print("=" * 60)

    all_articles = []

    # 依次抓取各个数据源
    sources = [extract_niutoushe, extract_36kr, extract_cloud_idc, extract_infoq]

    for i, extract_fn in enumerate(sources):
        try:
            articles = extract_fn()
            print(f"  -> 获取 {len(articles)} 条")
            all_articles.extend(articles)
        except Exception as e:
            print(f"  [ERROR] 抓取失败: {e}")

        # 请求间隔（最后一个不需要等）
        if i < len(sources) - 1:
            time.sleep(REQUEST_INTERVAL)

    print(f"\n总共获取: {len(all_articles)} 条（去重前）")

    # 清洗标题
    for a in all_articles:
        a["title"] = clean_title(a["title"])

    # 去重
    all_articles = dedup_articles(all_articles)
    print(f"去重后: {len(all_articles)} 条")

    # 过滤相关性
    all_articles = filter_relevant(all_articles)
    print(f"过滤后: {len(all_articles)} 条")

    # 构建输出
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    output = {
        "updateTime": now_str,
        "news": all_articles[:8]  # 最多保留8条
    }

    # 写入文件
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 已写入 {output_path}")
    print(f"   共 {len(output['news'])} 条资讯，更新时间: {now_str}")

    # GitHub Actions 环境下输出一些调试信息
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::notice title=抓取完成::共获取 {len(output['news'])} 条资讯")

    return 0


if __name__ == "__main__":
    sys.exit(main())
