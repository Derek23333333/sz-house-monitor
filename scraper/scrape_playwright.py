# -*- coding: utf-8 -*-
"""Playwright 直爬大众点评/美团（尽力而为，被反爬则返回空）"""

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

from config import CITY, USER_AGENTS
import random


def scrape_dianping_playwright():
    """用 Playwright 尝试直爬大众点评 H5"""
    if not HAS_PLAYWRIGHT:
        print("  [Playwright] 未安装，跳过直爬")
        return []

    items = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 375, "height": 812},
                locale="zh-CN",
            )
            page = context.new_page()

            # 尝试访问大众点评搜索页
            url = f"https://m.dianping.com/searchlist?cityId=7&keyword=火锅"
            print(f"  [Playwright] 尝试: {url}")
            page.goto(url, timeout=15000, wait_until="domcontentloaded")

            # 等待页面加载
            page.wait_for_timeout(3000)

            # 检查是否被重定向到登录页
            current_url = page.url
            if "login" in current_url or "mlogin" in current_url:
                print("  [Playwright] 大众点评: 被重定向到登录页，跳过")
                browser.close()
                return []

            # 尝试提取餐厅卡片
            cards = page.query_selector_all(".shoplist-item, .shop-item, .list-item, div[class*='shop']")
            for card in cards[:20]:
                try:
                    name_el = card.query_selector(".shopname, .name, .title, a[class*='name']")
                    name = name_el.inner_text().strip() if name_el else ""

                    if not name or len(name) < 2:
                        continue

                    desc_el = card.query_selector(".shopdesc, .desc, .info, p[class*='desc']")
                    desc = desc_el.inner_text().strip() if desc_el else ""

                    items.append({
                        "name": name,
                        "description": desc[:50] if desc else f"深圳美食推荐",
                        "cuisine": "火锅",
                        "source": "大众点评",
                    })
                except Exception:
                    continue

            browser.close()
            print(f"  [Playwright] 大众点评: 获取到 {len(items)} 条")
    except Exception as e:
        print(f"  [Playwright] 大众点评爬取失败: {e}")

    return items


def scrape_meituan_playwright():
    """用 Playwright 尝试直爬美团"""
    if not HAS_PLAYWRIGHT:
        return []

    items = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 375, "height": 812},
                locale="zh-CN",
            )
            page = context.new_page()

            url = "https://i.meituan.com/s/%E7%81%AB%E9%94%85"
            print(f"  [Playwright] 尝试: {url}")
            page.goto(url, timeout=15000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            current_url = page.url
            if "verify" in current_url or "captcha" in current_url:
                print("  [Playwright] 美团: 触发验证码，跳过")
                browser.close()
                return []

            cards = page.query_selector_all("div[class*='shop'], div[class*='item'], li[class*='shop']")
            for card in cards[:20]:
                try:
                    name_el = card.query_selector("a, .title, .name, h3")
                    name = name_el.inner_text().strip() if name_el else ""
                    if not name or len(name) < 2:
                        continue
                    items.append({
                        "name": name,
                        "description": f"深圳美食推荐",
                        "cuisine": "火锅",
                        "source": "美团",
                    })
                except Exception:
                    continue

            browser.close()
            print(f"  [Playwright] 美团: 获取到 {len(items)} 条")
    except Exception as e:
        print(f"  [Playwright] 美团爬取失败: {e}")

    return items


def scrape_all():
    """Playwright 直爬入口"""
    print("  [Playwright] 开始直爬尝试...")
    items = scrape_dianping_playwright()
    items += scrape_meituan_playwright()
    print(f"  [Playwright] 总计获取 {len(items)} 条数据")
    return items
