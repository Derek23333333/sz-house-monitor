# -*- coding: utf-8 -*-
"""下厨房搜索页爬虫：提取菜谱名、食材、评分、链接"""

import time
import random
import requests
from bs4 import BeautifulSoup
from config import RECIPE_KEYWORDS, XC_DELAY, USER_AGENTS


def search_xiachufang(keyword, page=1):
    """搜索下厨房菜谱"""
    url = "https://www.xiachufang.com/search/"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.xiachufang.com/",
    }
    params = {"keyword": keyword, "page": str(page)}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        recipes = []

        # 菜谱卡片
        cards = soup.select("div.recipe-normal, div.recipe-list-item, li[class*='recipe']")
        if not cards:
            # 尝试其他选择器
            cards = soup.select("div[class*='recipe']")

        for card in cards:
            recipe = {}

            # 菜谱名
            name_tag = card.select_one("a.name, p.name a, a[class*='name'], a[class*='title']")
            if not name_tag:
                name_tag = card.select_one("p a, a")
            if name_tag:
                recipe["name"] = name_tag.get_text(strip=True)
                href = name_tag.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://www.xiachufang.com" + href
                recipe["recipe_url"] = href
            else:
                continue

            if not recipe.get("name") or len(recipe["name"]) < 2:
                continue

            # 食材
            ingredients = []
            ing_tags = card.select("div.ing.ellipsis, div.ing, span.ing, p.ing")
            for ing_tag in ing_tags:
                ing_text = ing_tag.get_text(strip=True)
                if ing_text:
                    # 食材可能以逗号分隔
                    parts = [p.strip() for p in ing_text.split(",") if p.strip()]
                    parts += [p.strip() for p in ing_text.split("、") if p.strip()]
                    ingredients.extend(parts)

            # 去掉食材里的用量
            clean_ings = []
            skip_words = {"食材", "配料", "主料", "调料", "原料", "辅料", "", " "}
            for ing in ingredients:
                # 去掉括号里的用量
                ing = ing.split("(")[0].split("（")[0].strip()
                # 去掉数字+单位
                import re
                ing = re.sub(r'\d+\s*(克|g|ml|毫升|个|片|块|勺|适量|少许|根|条|只|把|瓣|斤|两)', '', ing).strip()
                # 去掉"食材、"等前缀
                for prefix in ["食材、", "食材:", "食材：", "配料、", "主料、", "调料、"]:
                    if ing.startswith(prefix):
                        ing = ing[len(prefix):].strip()
                # 过滤掉通用词和太长的文本
                if ing and len(ing) <= 8 and ing not in clean_ings and ing not in skip_words:
                    clean_ings.append(ing)

            recipe["ingredients"] = clean_ings[:10]  # 最多保留10个食材

            # 评分
            rating_tag = card.select_one("span.score, div.score, span[class*='score'], span[class*='rating']")
            if rating_tag:
                rating_text = rating_tag.get_text(strip=True)
                import re
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    recipe["rating"] = float(rating_match.group(1))
                else:
                    recipe["rating"] = None
            else:
                recipe["rating"] = None

            # 做过人数
            cooked_tag = card.select_one("span.cooked, div.cooked, span[class*='cooked'], a[class*='cooked']")
            if cooked_tag:
                cooked_text = cooked_tag.get_text(strip=True)
                import re
                cooked_match = re.search(r'(\d+)', cooked_text)
                recipe["cooked_count"] = int(cooked_match.group(1)) if cooked_match else 0
            else:
                recipe["cooked_count"] = 0

            recipe["cuisine"] = keyword
            recipe["source"] = "下厨房"
            recipes.append(recipe)

        return recipes
    except Exception as e:
        print(f"  [下厨房] 搜索失败: {keyword} -> {e}")
        return []


def scrape_all():
    """抓取所有关键词的菜谱数据"""
    all_recipes = []
    seen_names = set()

    for keyword in RECIPE_KEYWORDS:
        print(f"  [下厨房] 搜索: {keyword}")
        recipes = search_xiachufang(keyword)
        print(f"    -> 获取到 {len(recipes)} 条菜谱")

        for r in recipes:
            if r["name"] in seen_names:
                continue
            all_recipes.append(r)
            seen_names.add(r["name"])

        time.sleep(XC_DELAY)

    print(f"  [下厨房] 总计获取 {len(all_recipes)} 条菜谱数据")
    return all_recipes


if __name__ == "__main__":
    data = scrape_all()
    for d in data[:5]:
        print(f"  {d['name']} | {d.get('rating')} | 食材: {d.get('ingredients', [])[:5]}")
