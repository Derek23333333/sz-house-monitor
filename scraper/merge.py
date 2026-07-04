# -*- coding: utf-8 -*-
"""增量合并：新爬数据与已有 food-data.js 对比合并（只增不减，有变动才更新）"""

import json
import os
import re
from datetime import datetime, date


def load_existing_data(filepath):
    """读取已有的 food-data.js，返回 items 列表"""
    if not os.path.exists(filepath):
        print("  [Merge] 未找到已有数据文件，首次运行")
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # 提取 JSON 对象：var foodData = {...};
        match = re.search(r'var\s+foodData\s*=\s*(\{.*?\})\s*;', content, re.DOTALL)
        if not match:
            print("  [Merge] 已有文件格式异常，当作首次运行")
            return []

        data = json.loads(match.group(1))
        items = data.get("items", [])
        print(f"  [Merge] 读取已有数据: {len(items)} 条")
        return items
    except Exception as e:
        print(f"  [Merge] 读取已有数据失败: {e}，当作首次运行")
        return []


def get_today_str():
    """获取今天的日期字符串"""
    return date.today().strftime("%Y-%m-%d")


def items_equal(old_item, new_item):
    """比较两个条目的关键字段是否有变化"""
    compare_fields = ["name", "description", "cuisine", "health_tag",
                      "price_level", "type", "source", "rating",
                      "avg_price", "tag", "ingredients"]

    for field in compare_fields:
        old_val = old_item.get(field)
        new_val = new_item.get(field)
        if old_val != new_val:
            return False

    return True


def merge_data(old_items, new_items):
    """
    增量合并：
    - 新条目（旧数据没有）→ 新增
    - 已存在条目，关键字段有变化 → 更新
    - 已存在条目，无变化 → 保留旧数据
    - 旧数据有但本次没爬到 → 保留不动
    """
    today = get_today_str()

    # 以 name 为键建立旧数据索引
    old_by_name = {item["name"]: item for item in old_items if "name" in item}
    new_by_name = {item["name"]: item for item in new_items if "name" in item}

    merged = []
    stats = {"new": 0, "updated": 0, "kept": 0, "total_old": len(old_items)}

    # 1. 先处理旧数据中的条目
    for old_item in old_items:
        name = old_item.get("name")
        if not name:
            merged.append(old_item)
            continue

        if name in new_by_name:
            new_item = new_by_name[name]
            if items_equal(old_item, new_item):
                # 无变化，保留旧数据
                merged.append(old_item)
                stats["kept"] += 1
            else:
                # 有变化，更新（保留 first_seen，刷新 updated_at）
                merged_item = dict(new_item)
                merged_item["first_seen"] = old_item.get("first_seen", today)
                merged_item["updated_at"] = today
                # 保留旧数据中有的但新数据没有的字段
                for k, v in old_item.items():
                    if k not in merged_item:
                        merged_item[k] = v
                merged.append(merged_item)
                stats["updated"] += 1
        else:
            # 旧数据有但本次没爬到 → 保留不动
            merged.append(old_item)

    # 2. 处理新条目（旧数据没有的）
    for new_item in new_items:
        name = new_item.get("name")
        if not name or name in old_by_name:
            continue  # 已经在上面处理过了

        # 新增条目
        merged_item = dict(new_item)
        merged_item["first_seen"] = today
        merged_item["updated_at"] = today
        merged.append(merged_item)
        stats["new"] += 1

    stats["total_new"] = len(merged)
    print(f"  [Merge] 新增 {stats['new']} 条, 更新 {stats['updated']} 条, "
          f"保留 {stats['kept']} 条, 总计 {stats['total_new']} 条")
    return merged, stats
