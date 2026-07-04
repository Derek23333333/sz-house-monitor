# -*- coding: utf-8 -*-
"""
Bing 搜索聚合：
1. 搜索深圳美食推荐文章
2. 抓取文章页面提取真实餐厅名和描述
3. 从文章内容中检测来源平台标注
"""

import re
import time
import random
import requests
from bs4 import BeautifulSoup
from config import CUISINE_KEYWORDS, SOURCE_SITES, DESKTOP_USER_AGENTS, USER_AGENTS, BING_DELAY, MAX_BING_RESULTS, MAX_ARTICLES_PER_QUERY

# 已知的深圳餐厅品牌（用于辅助匹配）
KNOWN_BRANDS = {
    "火锅": ["海底捞", "八合里", "野妹火锅", "润园四季", "捞王", "大龙燚", "小龙坎", "蜀大侠",
             "巴奴", "凑凑", "怂火锅", "太二", "贤合庄", "德庄", "刘一手", "佩姐", "钢管厂五区",
             "渝味晓宇", "小龙坎老火锅", "大宅门", "陈记顺和", "潮汕牛肉火锅"],
    "烤肉": ["九田家", "汉拿山", "新罗宝", "姜虎东", "权金城", "赤坂亭", "萨莉亚", "烤肉竞技场",
             "水原城", "本家", "喜来稀肉", "姜虎东白丁", "八色烤肉", "犁寺烤肉"],
    "粤菜": ["客语", "点都德", "广州酒家", "陶陶居", "炳胜", "顺德人家", "潮江春", "新发烧腊",
             "利苑", "翠华", "太兴", "大家乐", "大快活", "美心", "稻香", "唐宫", "海港城",
             "利宝阁", "佳宁娜", "丹桂轩"],
    "日料": ["元气寿司", "藏寿司", "寿司郎", "一兰拉面", "味千拉面", "吉野家", "食其家",
             "松屋", "河源先生", "美浓吉", "隐泉", "江户前", "大渔", "将太",
             "合点寿司", "摩打食堂", "博多一幸舍"],
    "西餐": ["蓝蛙", "Wagas", "元素西餐厅", "帕萨卡", "必胜客", "达美乐", "棒约翰",
             "萨莉亚", "豪亨氏", "星期五", "硬石", "蓝樽", "Morton's", "Ruth's Chris"],
    "快餐": ["真功夫", "永和大王", "嘉旺", "大家乐", "麦当劳", "肯德基", "汉堡王",
             "华莱士", "德克士", "老乡鸡", "乡村基", "杨国福", "张亮"],
    "粉面": ["味千拉面", "博多一幸舍", "豚王", "蔡林记", "陈克明", "康师傅",
             "拉面说", "遇见小面", "天下粉面", "肥肠粉", "常德牛肉粉"],
    "茶点": ["点都德", "陶陶居", "广州酒家", "稻香", "利苑", "唐宫", "海港城",
             "美心皇宫", "翠园", "龙皇酒家", "利宝阁"],
    "烧腊": ["新发烧腊", "太兴", "大家乐", "大快活", "美心", "甘牌烧鹅",
             "新桂烧腊", "深井烧鹅", "龙津烧腊"],
    "自助": ["金钱豹", "四海一家", "亚马逊", "大渔铁板烧", "赤坂亭", "上井",
             "喜来登", "威斯汀", "香格里拉", "洲际酒店"],
    "糖水": ["许留山", "满记甜品", "鲜芋仙", "义顺牛奶", "糖水铺", "百花甜品",
             "玫瑰甜品", "双皮奶", "陈添记"],
    "奶茶": ["喜茶", "奈雪的茶", "茶颜悦色", "一点点", "CoCo", "蜜雪冰城",
             "茶百道", "书亦烧仙草", "古茗", "益禾堂", "鹿角巷", "台盖", "有茶"],
    "甜品": ["满记甜品", "许留山", "godiva", "哈根达斯", "DQ", "鲜芋仙",
             "巴黎贝甜", "85度C", "元祖", "好利来", "味多美"],
    "卤味": ["周黑鸭", "绝味", "煌上煌", "久久丫", "廖记棒棒肉", "紫燕百味鸡",
             "卤江南", "留夫鸭"],
    "川湘菜": ["太二酸菜鱼", "客语", "费大厨", "炊烟小炒黄牛肉", "坛宗剁椒鱼头",
               "佬麻雀", "蛙来哒", "蜀地源", "芙蓉楼", "毛家饭店", "玉楼东"],
    "东南亚": ["冬阴功", "泰蕉叶", "越南粉", "芽庄", "暹罗", "Lemongrass",
               "泰式厨房", "帕泰", "Sawasdee"],
}


def search_bing(query, max_results=MAX_BING_RESULTS):
    """搜索 Bing 并返回结果列表"""
    url = "https://www.bing.com/search"
    headers = {
        "User-Agent": random.choice(DESKTOP_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    params = {"q": query, "count": str(max_results), "setlang": "zh-CN"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        results = []

        for item in soup.select("li.b_algo"):
            title_tag = item.select_one("h2 a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            link = title_tag.get("href", "")
            snippet_tag = item.select_one(".b_caption p, p.b_lineclamp4, p.b_lineclamp3, p.b_lineclamp2")
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            results.append({
                "title": title,
                "link": link,
                "snippet": snippet,
            })

        return results
    except Exception as e:
        print(f"  [Bing] 搜索失败: {query} -> {e}")
        return []


def fetch_article(url, timeout=10):
    """抓取文章页面内容"""
    if not url or not url.startswith("http"):
        return ""

    # 跳过非美食页面
    skip_domains = ["baike.baidu", "shenzhen.gov", "sz.gov", "baidu.com/link",
                    "zhihu.com", "douban.com", "weibo.com", "t.cn"]
    if any(d in url for d in skip_domains):
        return ""

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        # 移除脚本和样式
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # 提取正文
        article = soup.find("article") or soup.find("div", class_=re.compile("article|content|main|body"))
        if article:
            return article.get_text("\n", strip=True)
        return soup.get_text("\n", strip=True)
    except Exception as e:
        print(f"    [Article] 抓取失败: {url[:60]} -> {e}")
        return ""


def extract_restaurants_from_text(text, cuisine, source_hint=None):
    """从文章正文中提取餐厅信息"""
    items = []

    if not text or len(text) < 50:
        return items

    # 1. 先匹配已知品牌
    brands = KNOWN_BRANDS.get(cuisine, [])
    for brand in brands:
        if brand in text:
            # 提取品牌周围的描述文本
            idx = text.find(brand)
            start = max(0, idx - 20)
            end = min(len(text), idx + len(brand) + 80)
            context = text[start:end].replace("\n", " ").strip()

            # 清理描述
            desc = context.replace(brand, "").strip("，。、：； ").strip()
            if not desc or len(desc) < 5:
                desc = f"深圳{cuisine}知名品牌"

            items.append({
                "name": brand,
                "description": desc[:50],
                "cuisine": cuisine,
                "source": source_hint or "大众点评",
            })

    # 2. 用正则提取「店名+后缀」模式
    # 常见餐厅名后缀
    suffix_pattern = r'([\u4e00-\u9fa5]{2,8}(?:火锅|餐厅|饭店|食府|酒楼|茶餐厅|烧腊|粉店|面馆|茶饮|奶茶|甜品店|糖水铺|烤肉|日料|寿司|料理|西餐厅|自助餐|川菜馆|湘菜馆|粤菜馆))'
    matches = re.findall(suffix_pattern, text)
    for name in matches:
        name = name.strip()
        if len(name) < 3 or len(name) > 15:
            continue
        # 过滤掉非餐厅名
        if any(skip in name for skip in ["的是", "可以", "深圳", "这家", "一家", "很多", "非常", "怎么"]):
            continue

        # 提取描述
        idx = text.find(name)
        start = max(0, idx + len(name))
        end = min(len(text), start + 60)
        desc = text[start:end].replace("\n", " ").strip("，。、：； ").strip()

        if not desc or len(desc) < 5:
            desc = f"深圳{cuisine}推荐"

        items.append({
            "name": name,
            "description": desc[:50],
            "cuisine": cuisine,
            "source": source_hint or "大众点评",
        })

    # 3. 提取「《店名》」或「『店名』」或「「店名」」模式
    quote_pattern = r'[《「『【]([\u4e00-\u9fa5]{2,12})[》」』】]'
    for name in re.findall(quote_pattern, text):
        name = name.strip()
        if len(name) < 2:
            continue
        idx = text.find(name)
        start = max(0, idx + len(name))
        end = min(len(text), start + 60)
        desc = text[start:end].replace("\n", " ").strip("，。、：； ").strip()
        if not desc or len(desc) < 5:
            desc = f"深圳{cuisine}推荐"

        items.append({
            "name": name,
            "description": desc[:50],
            "cuisine": cuisine,
            "source": source_hint or "大众点评",
        })

    # 去重
    seen = set()
    unique_items = []
    for item in items:
        if item["name"] not in seen:
            seen.add(item["name"])
            unique_items.append(item)

    return unique_items


def detect_source_from_content(text):
    """从内容中检测来源平台"""
    if "大众点评" in text or "点评网" in text:
        return "大众点评"
    if "美团" in text:
        return "美团"
    if "小红书" in text or "红书" in text:
        return "小红书"
    return "大众点评"  # 默认


def extract_from_snippet(snippet, cuisine):
    """从搜索摘要中提取餐厅信息"""
    items = []

    if not snippet:
        return items

    # 匹配已知品牌
    brands = KNOWN_BRANDS.get(cuisine, [])
    for brand in brands:
        if brand in snippet:
            idx = snippet.find(brand)
            start = max(0, idx + len(brand))
            end = min(len(snippet), start + 50)
            desc = snippet[start:end].strip("，。、：； ").strip()
            if not desc or len(desc) < 5:
                desc = f"深圳{cuisine}知名品牌"

            source = detect_source_from_content(snippet)
            items.append({
                "name": brand,
                "description": desc[:50],
                "cuisine": cuisine,
                "source": source,
            })

    # 匹配餐厅名+后缀
    suffix_pattern = r'([\u4e00-\u9fa5]{2,8}(?:火锅|餐厅|饭店|食府|酒楼|茶餐厅|烧腊|粉店|面馆|茶饮|奶茶|甜品店|糖水铺|烤肉|日料|寿司|料理|西餐厅|自助餐|川菜馆|湘菜馆|粤菜馆))'
    for name in re.findall(suffix_pattern, snippet):
        name = name.strip()
        if len(name) < 3 or len(name) > 15:
            continue
        if any(skip in name for skip in ["的是", "可以", "深圳", "这家", "一家"]):
            continue
        idx = snippet.find(name)
        start = max(0, idx + len(name))
        end = min(len(snippet), start + 50)
        desc = snippet[start:end].strip("，。、：； ").strip()
        if not desc or len(desc) < 5:
            desc = f"深圳{cuisine}推荐"

        source = detect_source_from_content(snippet)
        items.append({
            "name": name,
            "description": desc[:50],
            "cuisine": cuisine,
            "source": source,
        })

    # 去重
    seen = set()
    unique_items = []
    for item in items:
        if item["name"] not in seen:
            seen.add(item["name"])
            unique_items.append(item)

    return unique_items


def scrape_all():
    """抓取所有菜系的餐厅数据"""
    all_items = []
    seen_names = set()

    for cuisine, queries in CUISINE_KEYWORDS.items():
        print(f"\n  [Bing] 正在抓取菜系: {cuisine}")

        for query in queries:
            print(f"    搜索: {query}")
            results = search_bing(query)

            article_count = 0
            for r in results:
                # 1. 先从 snippet 提取
                source_hint = detect_source_from_content(r["snippet"] + " " + r["title"])
                snippet_items = extract_from_snippet(r["snippet"] + " " + r["title"], cuisine)

                for item in snippet_items:
                    if item["name"] not in seen_names:
                        all_items.append(item)
                        seen_names.add(item["name"])
                        print(f"      [snippet] {item['name']} ({item['source']})")

                # 2. 抓取文章页面提取更多数据（只抓前N个结果）
                if article_count < MAX_ARTICLES_PER_QUERY and len(all_items) < 250:
                    article_text = fetch_article(r["link"])
                    if article_text:
                        article_items = extract_restaurants_from_text(article_text, cuisine, source_hint)
                        for item in article_items:
                            if item["name"] not in seen_names:
                                all_items.append(item)
                                seen_names.add(item["name"])
                                print(f"      [article] {item['name']} ({item['source']})")
                    article_count += 1

                time.sleep(1)  # 文章抓取间隔

            time.sleep(BING_DELAY)

    print(f"\n  [Bing] 总计获取 {len(all_items)} 条餐厅数据")

    # 保底：如果某些菜系没有数据，用已知品牌列表补充
    existing_cuisines = set(item["cuisine"] for item in all_items)
    for cuisine, brands in KNOWN_BRANDS.items():
        cuisine_items = [item for item in all_items if item["cuisine"] == cuisine]
        if len(cuisine_items) < 3:
            print(f"  [Bing] {cuisine} 数据不足({len(cuisine_items)}条)，用品牌列表补充")
            for brand in brands:
                if brand not in seen_names:
                    all_items.append({
                        "name": brand,
                        "description": f"深圳{cuisine}知名品牌",
                        "cuisine": cuisine,
                        "source": "大众点评",
                    })
                    seen_names.add(brand)

    print(f"  [Bing] 补充后总计: {len(all_items)} 条")
    return all_items


if __name__ == "__main__":
    data = scrape_all()
    for d in data[:10]:
        print(f"  {d['source']} | {d['cuisine']} | {d['name']} | {d['description'][:30]}")
