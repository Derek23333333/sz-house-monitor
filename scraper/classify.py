# -*- coding: utf-8 -*-
"""数据清洗与分类：推断健康标签、价位、类型、难度"""

import re
from config import (
    HEALTH_TAG_RULES, PRICE_LEVEL_RULES, TYPE_RULES,
    COOK_TIME_RULES, DIFFICULTY_BY_INGREDIENTS
)


def truncate_description(desc, max_len=50):
    """截断描述到指定长度"""
    if not desc:
        return ""
    desc = desc.strip()
    # 去掉多余空白
    desc = re.sub(r'\s+', ' ', desc)
    if len(desc) > max_len:
        desc = desc[:max_len - 1] + "..."
    return desc


def infer_health_tag(cuisine, name="", description=""):
    """推断健康标签"""
    text = name + " " + description
    # 特殊关键词优先
    if any(kw in text for kw in ["轻食", "沙拉", "减脂", "低卡", "健康"]):
        return "🟢轻食"
    if any(kw in text for kw in ["养生", "滋补", "炖汤", "老火汤"]):
        return "🔵滋补养生"
    if any(kw in text for kw in ["炸", "烤", "红烧", "肥"]):
        return "🟠热量炸弹"
    # 按菜系
    return HEALTH_TAG_RULES.get(cuisine, "🟡适中")


def infer_price_level(cuisine, avg_price=None):
    """推断价位分级"""
    if avg_price:
        if avg_price < 40:
            return "💰"
        elif avg_price < 100:
            return "💰💰"
        else:
            return "💰💰💰"
    return PRICE_LEVEL_RULES.get(cuisine, "💰💰")


def infer_type(cuisine, name="", description=""):
    """推断类型"""
    text = name + " " + description
    # 特殊关键词
    if any(kw in text for kw in ["外卖", "配送", "到家"]):
        return "外卖"
    if any(kw in text for kw in ["下午茶", "甜品店", "奶茶店", "糖水铺"]):
        return "下午茶"
    return TYPE_RULES.get(cuisine, "堂食")


def infer_cook_time(cuisine):
    """推断烹饪时间"""
    return COOK_TIME_RULES.get(cuisine, "30分钟")


def infer_difficulty(ingredients):
    """根据食材数量推断难度"""
    if not ingredients:
        return "简单"
    count = len(ingredients)
    if count <= 5:
        return DIFFICULTY_BY_INGREDIENTS["simple"]
    elif count <= 10:
        return DIFFICULTY_BY_INGREDIENTS["medium"]
    else:
        return DIFFICULTY_BY_INGREDIENTS["hard"]


def generate_id(source, seq):
    """生成唯一ID"""
    prefix_map = {
        "大众点评": "dp", "美团": "mt", "小红书": "xhs",
        "下厨房": "xc", "高德地图": "amap", "Bing搜索": "bing",
    }
    prefix = prefix_map.get(source, "fd")
    return f"{prefix}_{seq:04d}"


def is_valid_restaurant_name(name):
    """检查是否是有效的餐厅名（过滤掉描述性文字误提取）"""
    if not name or len(name) < 2 or len(name) > 15:
        return False

    # 含有句子结构词的不是餐厅名
    sentence_words = [
        "的", "了", "是", "在", "有", "等", "和", "与", "或", "可", "能",
        "会", "要", "就", "也", "都", "还", "只", "最", "更", "很", "太",
        "非常", "为", "以", "对", "让", "被", "把", "给", "向", "从", "到",
        "之", "其", "此", "该", "本", "这", "那", "某", "各", "每", "任",
        "些", "适合", "源于", "源自", "知名", "专注", "品牌", "推荐",
        "选择", "选", "吃", "做", "去", "来", "位居", "偶", "凭", "净",
        "超", "创", "高", "中", "我", "业", "并且", "而且", "就是",
        "都是", "也是", "便是", "而非", "并称", "号称", "值得", "必吃",
        "提供", "拥有", "具备", "呈现", "展现", "代表", "成为", "属于",
        "具有", "包含", "涉及", "覆盖", "包括", "分布", "遍布", "开设",
    ]
    for word in sentence_words:
        if word in name:
            return False

    # 以动词/形容词开头的通常不是餐厅名
    bad_starts = [
        "选", "推", "吃", "做", "去", "来", "是", "有", "位", "居",
        "适", "品", "知", "多", "享", "偶", "凭", "食", "净", "超",
        "创", "高", "中", "我", "业", "潮", "蜀", "源", "最", "更",
        "很", "太", "非", "为", "以", "对", "让", "被", "把", "给",
        "向", "从", "到", "之", "其", "此", "该", "本", "这", "那",
        "某", "各", "每", "值", "必", "提", "拥", "具", "呈", "展",
        "代", "成", "属", "包", "涉", "覆", "包", "分", "遍", "开",
        "合", "味", "好", "大", "小", "老", "新", "正", "真", "多",
        "少", "一", "二", "三", "四", "五", "六", "七", "八", "九",
        "十", "百", "千", "万", "亿",
    ]
    # 注意：小/老/大 开头的可能是合法餐厅名（如小肥羊、老房子），需要特殊处理
    # 只有当后面跟的不是品牌名时才过滤
    if name[0] in bad_starts:
        # 允许一些以"老"/"小"/"大"开头的知名品牌
        allowed_prefixes = ["老", "小", "大"]
        if name[0] in allowed_prefixes and len(name) <= 6:
            pass  # 允许
        else:
            return False

    # 全是数字的跳过
    if name.isdigit():
        return False

    return True


def classify_restaurant_items(items):
    """分类餐厅数据"""
    classified = []
    seq = 1
    seen_names = set()

    for item in items:
        name = item.get("name", "").strip()
        if not name or name in seen_names:
            continue
        # 过滤无效的餐厅名
        if not is_valid_restaurant_name(name):
            continue
        seen_names.add(name)

        cuisine = item.get("cuisine", "粤菜")
        description = truncate_description(item.get("description", ""), 50)
        source = item.get("source", "大众点评")
        avg_price = item.get("avg_price")
        rating = item.get("rating")

        classified_item = {
            "id": generate_id(source, seq),
            "name": name,
            "description": description,
            "cuisine": cuisine,
            "health_tag": infer_health_tag(cuisine, name, description),
            "price_level": infer_price_level(cuisine, avg_price),
            "type": infer_type(cuisine, name, description),
            "source": source,
        }

        if rating is not None:
            classified_item["rating"] = rating
        if avg_price is not None:
            classified_item["avg_price"] = avg_price
        if item.get("tag"):
            classified_item["tag"] = item["tag"]

        classified.append(classified_item)
        seq += 1

    return classified


def classify_recipe_items(recipes):
    """分类菜谱数据（自己做）"""
    classified = []
    seq = 1
    seen_names = set()

    for recipe in recipes:
        name = recipe.get("name", "").strip()
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        cuisine = recipe.get("cuisine", "家常菜")
        ingredients = recipe.get("ingredients", [])
        description = truncate_description(
            recipe.get("description") or f"{'、'.join(ingredients[:5])}等食材制作的家常菜",
            50
        )

        classified_item = {
            "id": generate_id("下厨房", seq),
            "name": name,
            "description": description,
            "cuisine": cuisine,
            "health_tag": infer_health_tag(cuisine, name, description),
            "price_level": "💰",
            "type": "自己做",
            "source": "下厨房",
            "ingredients": ingredients,
            "cook_time": infer_cook_time(cuisine),
            "difficulty": infer_difficulty(ingredients),
        }

        if recipe.get("rating"):
            classified_item["rating"] = recipe["rating"]
        if recipe.get("recipe_url"):
            classified_item["recipe_url"] = recipe["recipe_url"]

        classified.append(classified_item)
        seq += 1

    return classified


def deduplicate(items):
    """去重：按 name 字段去重，保留第一个（评分更高或更完整的）"""
    seen = {}
    for item in items:
        name = item.get("name", "")
        if name not in seen:
            seen[name] = item
        else:
            # 保留字段更完整的
            existing = seen[name]
            if len(item.keys()) > len(existing.keys()):
                seen[name] = item

    return list(seen.values())
