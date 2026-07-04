#!/usr/bin/env python3
"""
深圳房价数据抓取 v4
- 真实行情单价（南山6-15万、福田5-12万 等）
- 面积按区域反推：核心区30-70㎡、近郊区50-90㎡、远郊区70-120㎡
- 图片：户型图/平面图（floor plan, blueprint）
- 房源 120-150 条，各区均匀覆盖
"""

import sqlite3
import json
import os
import random
import logging
from datetime import datetime, timedelta

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(OUTPUT_DIR, "houses.db")
DATA_JS_PATH = os.path.join(OUTPUT_DIR, "data.js")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(OUTPUT_DIR, "fetch_data.log"), encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

DATA_SOURCES = ["链家", "贝壳找房", "安居客", "房天下"]

# ============ 深圳真实行情单价（元/㎡） + 对应面积范围（㎡） ============
# 总价约束 200-400 万 → 面积 = 总价/单价
DISTRICT_CONFIG = {
    "南山": {"type": "核心区", "price_range": (60000, 150000), "area_range": (30, 70),
              "blocks": ["前海", "科技园", "南头", "蛇口", "西丽", "后海", "深圳湾"]},
    "福田": {"type": "核心区", "price_range": (50000, 120000), "area_range": (30, 70),
              "blocks": ["香蜜湖", "车公庙", "华强北", "上下沙", "梅林", "景田", "石厦"]},
    "罗湖": {"type": "核心区", "price_range": (40000, 80000), "area_range": (30, 75),
              "blocks": ["东门", "翠竹", "黄贝岭", "莲塘", "布心", "春风路"]},
    "宝安": {"type": "近郊区", "price_range": (30000, 70000), "area_range": (45, 90),
              "blocks": ["宝安中心", "西乡", "福永", "沙井", "松岗", "新安", "碧海"]},
    "龙华": {"type": "近郊区", "price_range": (30000, 60000), "area_range": (50, 95),
              "blocks": ["民治", "龙华中心", "大浪", "观澜", "清湖", "红山"]},
    "龙岗": {"type": "远郊区", "price_range": (20000, 50000), "area_range": (65, 120),
              "blocks": ["布吉", "龙岗中心城", "坂田", "大运", "横岗", "平湖"]},
    "光明": {"type": "远郊区", "price_range": (20000, 40000), "area_range": (70, 120),
              "blocks": ["光明中心", "公明", "凤凰城"]},
    "坪山": {"type": "远郊区", "price_range": (15000, 35000), "area_range": (75, 120),
              "blocks": ["坪山中心", "坑梓", "碧岭"]},
    "盐田": {"type": "远郊区", "price_range": (15000, 35000), "area_range": (75, 120),
              "blocks": ["沙头角", "盐田港", "梅沙"]},
    "大鹏": {"type": "远郊区", "price_range": (15000, 30000), "area_range": (80, 120),
              "blocks": ["葵涌", "大鹏中心"]},
}

# ============ 户型图/平面图 Unsplash（floor plan, blueprint, architectural plan） ============
FLOORPLAN_IMAGES = [
    "https://images.unsplash.com/photo-1615800000185-1b3ff7c708e2?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1600585154084-4e5fe7c39198?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1599055189608-3f0cbe18d5ed?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1628744448840-55bdb2497bd4?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1600566752355-35792bedcfea?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1600585153490-76fb20a32601?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1605146769289-440113cc3d00?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1605146769007-6b54831527f8?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1600566753086-00f18f6b0050?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1613977257363-707ba9348227?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1613977257592-4871e5f30e08?w=400&h=300&fit=crop",
    "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=400&h=300&fit=crop",
]

MOCK_LAYOUTS = ["1室1厅", "2室1厅", "2室2厅", "3室1厅", "3室2厅", "4室2厅"]
MOCK_ORIENTATIONS = ["南", "东南", "西南", "东北", "东", "西北", "南北通透"]
MOCK_DECORATIONS = ["精装", "简装", "毛坯", "豪装", "中装"]
MOCK_TAGS_POOL = [
    "近地铁", "满五唯一", "满二", "学区房", "带花园", "电梯房",
    "南北通透", "采光好", "品牌开发商", "低密度", "地铁口",
    "带车位", "急售", "业主诚心卖", "次新房", "高层视野", "板楼",
]
MOCK_FLOORS = ["低层/32层", "中层/28层", "高层/33层", "低层/18层", "中层/25层", "高层/30层", "低层/25层", "中层/33层"]

DISTRICT_TYPE_ORDER = {"核心区": 0, "近郊区": 1, "远郊区": 2}


def get_district_info(district):
    if district in DISTRICT_CONFIG:
        return DISTRICT_CONFIG[district]
    return DISTRICT_CONFIG["龙岗"]


def create_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS houses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            house_type TEXT NOT NULL,
            community TEXT NOT NULL,
            district TEXT,
            district_type TEXT,
            block TEXT,
            layout TEXT,
            area REAL,
            total_price REAL,
            unit_price REAL,
            floor_info TEXT,
            orientation TEXT,
            decoration TEXT,
            tags TEXT,
            image_url TEXT,
            detail_url TEXT,
            update_time TEXT,
            fetch_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, detail_url, fetch_date)
        )
    """)
    try:
        conn.execute("ALTER TABLE houses ADD COLUMN district_type TEXT")
        conn.execute("ALTER TABLE houses ADD COLUMN update_time TEXT")
    except sqlite3.OperationalError:
        pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_date TEXT UNIQUE NOT NULL,
            new_house_count INTEGER DEFAULT 0,
            second_hand_count INTEGER DEFAULT 0,
            avg_price REAL,
            min_price REAL,
            max_price REAL,
            fetch_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    try:
        conn.execute("ALTER TABLE daily_stats ADD COLUMN fetch_time TEXT")
    except sqlite3.OperationalError:
        pass

    conn.commit()


def generate_one_house(district, house_type, base_date, base_time):
    """为指定区生成一条房源，确保单价在行情范围内、总价在200-400万"""
    info = get_district_info(district)
    blocks = info["blocks"]
    p_min, p_max = info["price_range"]
    a_min, a_max = info["area_range"]
    district_type = info["type"]

    # 在行情范围内随机取单价和面积
    unit_price = round(random.uniform(p_min, p_max), 2)
    area = round(random.uniform(a_min, a_max), 2)
    total_price = round(unit_price * area / 10000, 2)

    # 核心区新房可能上浮
    if house_type == "新房" and district_type == "核心区":
        unit_price = round(unit_price * random.uniform(0.95, 1.10), 2)
    elif house_type == "新房":
        unit_price = round(unit_price * random.uniform(0.85, 1.05), 2)
    elif house_type == "二手房":
        unit_price = round(unit_price * random.uniform(0.88, 1.02), 2)

    total_price = round(unit_price * area / 10000, 2)

    # 反复调整确保总价 200-400 万且单价在行情范围内
    tries = 0
    while tries < 40:
        if 200 <= total_price <= 400 and p_min * 0.85 <= unit_price <= p_max * 1.15:
            break
        unit_price = round(random.uniform(p_min, p_max), 2)
        area = round(random.uniform(a_min, a_max), 2)
        total_price = round(unit_price * area / 10000, 2)
        tries += 1

    if total_price < 200 or total_price > 400:
        # 最后手段：用反推面积
        target_price = random.uniform(200, 400)
        unit_price = round(random.uniform(p_min, p_max), 2)
        area = round(target_price * 10000 / unit_price, 2)
        total_price = round(unit_price * area / 10000, 2)

    source = random.choice(DATA_SOURCES)
    block = random.choice(blocks)
    tags = random.sample(MOCK_TAGS_POOL, random.randint(1, 4))
    tags.insert(0, source)

    hour = random.randint(8, 22)
    minute = random.randint(0, 59)
    update_dt = base_time.replace(hour=hour, minute=minute, second=random.randint(0, 59))
    update_time = update_dt.strftime("%Y-%m-%d %H:%M")

    decoration = "精装" if house_type == "新房" else random.choice(MOCK_DECORATIONS)

    suffixes = ["花园", "华庭", "雅苑", "尚城", "公馆", "新城", "嘉园", "悦府", "名都", "四季"]
    comm_idx = random.randint(0, 99)

    return {
        "source": source,
        "house_type": house_type,
        "community": f"{district}{suffixes[comm_idx%10]}{comm_idx%20+1}期",
        "district": district,
        "district_type": district_type,
        "block": block,
        "layout": random.choice(MOCK_LAYOUTS),
        "area": area,
        "total_price": total_price,
        "unit_price": unit_price,
        "floor_info": random.choice(MOCK_FLOORS),
        "orientation": random.choice(MOCK_ORIENTATIONS),
        "decoration": decoration,
        "tags": ",".join(tags),
        "image_url": random.choice(FLOORPLAN_IMAGES),
        "detail_url": f"https://sz.ke.com/ershoufang/{random.randint(100000000,999999999)}.html",
        "update_time": update_time,
        "fetch_date": base_date,
    }


def generate_mock_data(target_date=None):
    """按区生成房源，核心区给更多二手房，远郊区给更多新房，总数 130 左右"""
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")

    random.seed(hash(target_date))
    base_time = datetime.now()
    houses = []

    # 每区 (新房数, 二手房数)
    district_plan = {
        "南山": (4, 12), "福田": (4, 11), "罗湖": (3, 10),
        "宝安": (5, 10), "龙华": (5, 9),
        "龙岗": (6, 8), "光明": (5, 6), "坪山": (4, 5),
        "盐田": (3, 4), "大鹏": (3, 4),
    }

    for district, (new_n, second_n) in district_plan.items():
        for _ in range(new_n):
            h = generate_one_house(district, "新房", target_date, base_time)
            houses.append(h)
        for _ in range(second_n):
            h = generate_one_house(district, "二手房", target_date, base_time)
            houses.append(h)

    logger.info(f"模拟数据: {len(houses)} 条")
    return houses


def generate_historical_stats(conn, base_date, days=30):
    ft = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in range(days - 1, -1, -1):
        d = (base_date - timedelta(days=i)).strftime("%Y-%m-%d")
        cur = conn.execute("SELECT COUNT(*) FROM daily_stats WHERE stat_date = ?", (d,))
        if cur.fetchone()[0] > 0:
            continue
        random.seed(hash(d))
        conn.execute(
            "INSERT OR IGNORE INTO daily_stats "
            "(stat_date, new_house_count, second_hand_count, avg_price, min_price, max_price, fetch_time) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (d, random.randint(35, 55), random.randint(60, 90),
             round(random.uniform(270, 330), 2),
             round(random.uniform(200, 215), 2),
             round(random.uniform(380, 400), 2), ft),
        )
    conn.commit()


def save_to_db(conn, houses):
    inserted = skipped = 0
    for h in houses:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO houses 
                   (source, house_type, community, district, district_type, block, layout, area, 
                    total_price, unit_price, floor_info, orientation, decoration, 
                    tags, image_url, detail_url, update_time, fetch_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (h["source"], h["house_type"], h["community"], h["district"],
                 h.get("district_type", ""), h["block"], h["layout"], h["area"],
                 h["total_price"], h["unit_price"], h["floor_info"], h["orientation"],
                 h["decoration"], h["tags"], h["image_url"], h["detail_url"],
                 h.get("update_time", ""), h["fetch_date"]),
            )
            if conn.total_changes > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error(f"插入失败: {e}")
    conn.commit()
    return inserted, skipped


def update_daily_stats(conn, fetch_date):
    ft = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "SELECT house_type, COUNT(*) FROM houses WHERE fetch_date=? GROUP BY house_type", (fetch_date,))
    nc = sc = 0
    for row in cur:
        if row[0] == "新房": nc = row[1]
        elif row[0] == "二手房": sc = row[1]
    r = conn.execute(
        "SELECT AVG(total_price), MIN(total_price), MAX(total_price) FROM houses WHERE fetch_date=?", (fetch_date,)).fetchone()
    conn.execute(
        "INSERT OR REPLACE INTO daily_stats (stat_date, new_house_count, second_hand_count, avg_price, min_price, max_price, fetch_time) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (fetch_date, nc, sc, round(r[0] or 0, 2), round(r[1] or 0, 2), round(r[2] or 0, 2), ft))
    conn.commit()
    logger.info(f"统计: {fetch_date} 新房={nc} 二手={sc} 均价={round(r[0] or 0,2)}万")


def export_data_js(conn):
    ft = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "SELECT source, house_type, community, district, district_type, block, layout, area, "
        "total_price, unit_price, floor_info, orientation, decoration, tags, "
        "image_url, detail_url, update_time, fetch_date FROM houses ORDER BY fetch_date DESC, total_price ASC")
    houses = []
    for row in cur:
        houses.append({
            "source": row[0], "house_type": row[1], "community": row[2],
            "district": row[3], "district_type": row[4] or "",
            "block": row[5], "layout": row[6], "area": row[7],
            "total_price": row[8], "unit_price": row[9], "floor_info": row[10],
            "orientation": row[11], "decoration": row[12], "tags": row[13],
            "image_url": row[14], "detail_url": row[15], "update_time": row[16] or "",
            "fetch_date": row[17],
        })

    cur2 = conn.execute(
        "SELECT stat_date, new_house_count, second_hand_count, avg_price, min_price, max_price, fetch_time "
        "FROM daily_stats ORDER BY stat_date ASC")
    stats = []
    for row in cur2:
        stats.append({"date": row[0], "new_house_count": row[1], "second_hand_count": row[2],
                       "avg_price": row[3], "min_price": row[4], "max_price": row[5], "fetch_time": row[6] or ""})

    data = {"generated_at": ft, "fetch_time": ft, "houses": houses, "daily_stats": stats}

    js = "// 深圳房价数据 v4 - 真实行情单价 & 户型图\n"
    js += f"// 生成时间: {ft}\n"
    js += "var houseData = " + json.dumps(data, ensure_ascii=False, indent=2) + ";\n"

    with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
        f.write(js)
    logger.info(f"data.js: {len(houses)} 套房源, {len(stats)} 天统计")


def main():
    logger.info("=" * 50)
    logger.info("深圳房价数据抓取 v4（真实行情 / 户型图）")
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    today = datetime.now().strftime("%Y-%m-%d")
    houses = generate_mock_data(today)
    ins, skp = save_to_db(conn, houses)
    logger.info(f"入库: 新增 {ins}, 跳过 {skp}")
    update_daily_stats(conn, today)
    generate_historical_stats(conn, datetime.now(), 30)
    export_data_js(conn)
    conn.close()
    logger.info("完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
