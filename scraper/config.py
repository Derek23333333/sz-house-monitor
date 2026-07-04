# -*- coding: utf-8 -*-
"""配置中心：菜系关键词、城市编码、UA池、来源站点"""

CITY = "深圳"

# 菜系 -> 搜索关键词映射（含平台名以获取美食文章）
CUISINE_KEYWORDS = {
    "火锅":     ["深圳 火锅 大众点评 推荐", "深圳 火锅 必吃 美团"],
    "烤肉":     ["深圳 烤肉 大众点评 推荐", "深圳 烤肉 必吃 美团"],
    "粤菜":     ["深圳 粤菜 大众点评 推荐", "深圳 粤菜 老字号 必吃"],
    "日料":     ["深圳 日料 大众点评 推荐", "深圳 日本料理 必吃"],
    "西餐":     ["深圳 西餐 大众点评 推荐", "深圳 西餐厅 必吃"],
    "快餐":     ["深圳 快餐 美团 推荐", "深圳 简餐 外卖 推荐"],
    "粉面":     ["深圳 粉面 大众点评 推荐", "深圳 拉面 米粉 必吃"],
    "茶点":     ["深圳 早茶 大众点评 推荐", "深圳 茶点 必吃"],
    "烧腊":     ["深圳 烧腊 大众点评 推荐", "深圳 烧鹅 必吃"],
    "自助":     ["深圳 自助餐 大众点评 推荐", "深圳 自助 必吃 美团"],
    "糖水":     ["深圳 糖水 大众点评 推荐", "深圳 糖水铺 必吃"],
    "奶茶":     ["深圳 奶茶 大众点评 推荐", "深圳 奶茶店 小红书"],
    "甜品":     ["深圳 甜品 大众点评 推荐", "深圳 甜品店 必吃"],
    "卤味":     ["深圳 卤味 推荐", "深圳 卤味 小吃 必吃"],
    "川湘菜":   ["深圳 川菜 大众点评 推荐", "深圳 湘菜 必吃"],
    "东南亚":   ["深圳 东南亚菜 大众点评 推荐", "深圳 泰国菜 越南菜 必吃"],
}

# 菜谱搜索关键词（下厨房）
RECIPE_KEYWORDS = [
    "粤菜", "川菜", "湘菜", "家常菜", "蒸菜",
    "糖水", "甜品", "汤", "快手菜", "减脂餐",
]

# 来源站点：平台名 -> 域名
SOURCE_SITES = {
    "大众点评": "dianping.com",
    "美团":     "meituan.com",
    "小红书":   "xiaohongshu.com",
}

# 移动端 User-Agent 池
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S908E) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; Redmi Note 10 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13;OPPO Find X6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Mobile Safari/537.36",
]

# 桌面端 User-Agent（Bing 搜索用）
DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# 请求间隔（秒）- 防止触发反爬
BING_DELAY = 2       # Bing 搜索间隔
XC_DELAY = 2         # 下厨房请求间隔
MAX_BING_RESULTS = 10  # 每次Bing搜索提取的最大结果数
MAX_ARTICLES_PER_QUERY = 0  # 每次搜索最多抓取的文章页面数（0=跳过文章抓取，只用摘要）

# 输出文件路径
OUTPUT_FILE = "food-data.js"

# 菜系 -> 健康标签 映射规则
HEALTH_TAG_RULES = {
    "火锅":     "🟠热量炸弹",
    "烤肉":     "🟠热量炸弹",
    "烧腊":     "🟠热量炸弹",
    "自助":     "🟠热量炸弹",
    "卤味":     "🟠热量炸弹",
    "奶茶":     "🟠热量炸弹",
    "甜品":     "🟡适中",
    "糖水":     "🟢轻食",
    "粉面":     "🟡适中",
    "快餐":     "🟡适中",
    "茶点":     "🟡适中",
    "粤菜":     "🟡适中",
    "川湘菜":   "🟠热量炸弹",
    "东南亚":   "🟡适中",
    "日料":     "🟡适中",
    "西餐":     "🟡适中",
}

# 菜系 -> 价位分级 映射规则
PRICE_LEVEL_RULES = {
    "快餐":     "💰",
    "粉面":     "💰",
    "茶点":     "💰",
    "烧腊":     "💰",
    "卤味":     "💰",
    "糖水":     "💰",
    "奶茶":     "💰",
    "甜品":     "💰",
    "粤菜":     "💰💰",
    "川湘菜":   "💰💰",
    "东南亚":   "💰💰",
    "日料":     "💰💰",
    "火锅":     "💰💰",
    "烤肉":     "💰💰",
    "西餐":     "💰💰💰",
    "自助":     "💰💰💰",
}

# 菜系 -> 类型 映射规则
TYPE_RULES = {
    "快餐":     "外卖",
    "粉面":     "外卖",
    "茶点":     "外卖",
    "烧腊":     "外卖",
    "卤味":     "外卖",
    "糖水":     "下午茶",
    "奶茶":     "下午茶",
    "甜品":     "下午茶",
    "火锅":     "堂食",
    "烤肉":     "堂食",
    "粤菜":     "堂食",
    "日料":     "堂食",
    "西餐":     "堂食",
    "自助":     "堂食",
    "川湘菜":   "堂食",
    "东南亚":   "堂食",
}

# 菜系 -> 烹饪时间估算（自己做）
COOK_TIME_RULES = {
    "粤菜": "45分钟", "川菜": "30分钟", "湘菜": "30分钟",
    "家常菜": "30分钟", "蒸菜": "40分钟", "糖水": "60分钟",
    "甜品": "40分钟", "汤": "90分钟", "快手菜": "15分钟",
    "减脂餐": "20分钟",
}

# 菜系 -> 难度估算（自己做）
DIFFICULTY_BY_INGREDIENTS = {
    "simple": "简单",    # <=5 食材
    "medium": "中等",    # 6-10 食材
    "hard": "复杂",      # >10 食材
}
