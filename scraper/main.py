# -*- coding: utf-8 -*-
"""爬虫编排入口：依次调用各模块，增量合并，生成 food-data.js"""

import json
import os
import sys
from datetime import datetime

# 确保能导入同目录模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CITY, OUTPUT_FILE
from scrape_bing import scrape_all as scrape_bing_all
from scrape_xiachufang import scrape_all as scrape_xiachufang_all
from scrape_playwright import scrape_all as scrape_playwright_all
from classify import (
    classify_restaurant_items, classify_recipe_items, deduplicate
)
from merge import load_existing_data, merge_data


def generate_output(merged_items, stats):
    """生成 food-data.js 文件"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    output = {
        "generated_at": now,
        "city": CITY,
        "total": len(merged_items),
        "stats": stats,
        "items": merged_items,
    }

    # 写入 JS 文件
    js_content = f"var foodData = {json.dumps(output, ensure_ascii=False, indent=2)};\n"

    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        OUTPUT_FILE
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"\n  [Output] 已生成: {output_path}")
    print(f"  [Output] 总数据量: {len(merged_items)} 条")
    print(f"  [Output] 生成时间: {now}")

    return output_path


def main():
    print("=" * 60)
    print(f"  「今天吃啥？」深圳美食数据爬虫")
    print(f"  运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Bing 搜索聚合
    print("\n[Step 1] Bing 搜索聚合（大众点评/美团/小红书）...")
    bing_items = scrape_bing_all()

    # Step 2: 下厨房菜谱
    print("\n[Step 2] 下厨房菜谱抓取...")
    xc_recipes = scrape_xiachufang_all()

    # Step 3: Playwright 直爬（尽力而为）
    print("\n[Step 3] Playwright 直爬尝试...")
    pw_items = scrape_playwright_all()

    # Step 4: 分类清洗
    print("\n[Step 4] 数据分类清洗...")
    all_raw_items = bing_items + pw_items
    restaurant_items = classify_restaurant_items(all_raw_items)
    recipe_items = classify_recipe_items(xc_recipes)

    all_classified = restaurant_items + recipe_items
    all_classified = deduplicate(all_classified)
    print(f"  [Classify] 分类后总计: {len(all_classified)} 条 "
          f"(餐厅 {len(restaurant_items)} + 菜谱 {len(recipe_items)})")

    # Step 5: 增量合并
    print("\n[Step 5] 增量合并...")
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        OUTPUT_FILE
    )
    old_items = load_existing_data(output_path)
    merged_items, stats = merge_data(old_items, all_classified)

    # Step 6: 生成输出
    print("\n[Step 6] 生成 food-data.js...")
    generate_output(merged_items, stats)

    print("\n" + "=" * 60)
    print("  爬虫运行完成!")
    print("=" * 60)

    # 按来源统计
    source_counts = {}
    type_counts = {}
    for item in merged_items:
        s = item.get("source", "未知")
        source_counts[s] = source_counts.get(s, 0) + 1
        t = item.get("type", "未知")
        type_counts[t] = type_counts.get(t, 0) + 1

    print("\n  数据来源分布:")
    for s, c in sorted(source_counts.items(), key=lambda x: -x[1]):
        print(f"    {s}: {c} 条")

    print("\n  类型分布:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c} 条")


if __name__ == "__main__":
    main()
