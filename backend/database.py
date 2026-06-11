"""手机数据加载与查询"""

import json
import os
from typing import Optional


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PHONES_FILE = os.path.join(DATA_DIR, "phones.json")


def load_phones():
    """加载所有手机数据"""
    with open(PHONES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_phones():
    """获取全部机型列表"""
    return load_phones()


def get_phone_by_id(phone_id: int):
    """根据 ID 获取单个机型"""
    phones = load_phones()
    for p in phones:
        if p["id"] == phone_id:
            return p
    return None


def filter_phones(
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    need_nfc: Optional[bool] = None,
    need_35mm: Optional[bool] = None,
    need_ip68: Optional[bool] = None,
    brands: Optional[list[str]] = None,
):
    """按硬性条件过滤手机"""
    phones = load_phones()
    results = []

    for p in phones:
        if price_min is not None and p["price"] < price_min:
            continue
        if price_max is not None and p["price"] > price_max:
            continue
        if need_nfc and not p["has_nfc"]:
            continue
        if need_35mm and not p["has_35mm_jack"]:
            continue
        if need_ip68 and not p["has_ip68"]:
            continue
        if brands and p["brand"] not in brands:
            continue
        results.append(p)

    return results


def search_phones_by_name(query: str) -> list[dict]:
    """根据用户输入模糊匹配手机名称（支持中英文品牌名和简称）"""
    phones = load_phones()
    q = query.lower().replace(" ", "")

    # 品牌名中英文映射
    brand_aliases = {}
    for p in phones:
        b = p["brand"].lower()
        if b not in brand_aliases:
            brand_aliases[b] = []
    brand_aliases["小米"] = ["xiaomi"]
    brand_aliases["xiaomi"] = ["小米"]
    brand_aliases["华为"] = ["huawei"]
    brand_aliases["huawei"] = ["华为"]
    brand_aliases["荣耀"] = ["honor"]
    brand_aliases["honor"] = ["荣耀"]
    brand_aliases["三星"] = ["samsung"]
    brand_aliases["samsung"] = ["三星"]
    brand_aliases["vivo"] = ["vivo"]
    brand_aliases["oppo"] = ["oppo"]
    brand_aliases["一加"] = ["oneplus"]
    brand_aliases["oneplus"] = ["一加"]
    brand_aliases["真我"] = ["realme"]
    brand_aliases["realme"] = ["真我"]
    brand_aliases["魅族"] = ["meizu"]
    brand_aliases["meizu"] = ["魅族"]
    brand_aliases["红米"] = ["redmi"]
    brand_aliases["redmi"] = ["红米"]

    matched = []
    for p in phones:
        name = p["name"].lower().replace(" ", "")
        brand = p["brand"].lower()
        full = brand + name

        # 直接匹配（完整名称）
        if full in q or name in q:
            matched.append(p)
            continue

        # 提取名称中的数字部分（如 "Xiaomi 14" → "14"）
        digits = "".join(ch for ch in name if ch.isdigit())
        # 中文品牌名 + 数字（如 "小米14"）
        if digits and brand_aliases.get(brand):
            for alias in [brand] + brand_aliases[brand]:
                if (alias + digits) in q:
                    matched.append(p)
                    break

    # 同名同数字的只保留名称最短的（基础版，去掉 Pro/Ultra 等变体）
    seen = {}
    for p in matched:
        brand = p["brand"].lower()
        digits = "".join(ch for ch in p["name"].lower() if ch.isdigit())
        key = (brand, digits)
        if key not in seen or len(p["name"]) < len(seen[key]["name"]):
            seen[key] = p
    matched = list(seen.values())

    return matched


def calculate_score(phone: dict, weights: dict) -> float:
    """根据权重计算综合评分"""
    score = 0.0
    score += weights.get("gaming", 0.25) * phone["gaming_score"]
    score += weights.get("photo", 0.25) * phone["photo_score"]
    score += weights.get("battery", 0.25) * phone["battery_score"]
    score += weights.get("processor", 0.25) * phone["processor_score"]
    return score


def recommend(phones: list[dict], weights: dict, top_n: int = 3) -> list[dict]:
    """对候选机型按权重评分排序，返回 Top N"""
    scored = []
    for p in phones:
        p["_score"] = round(calculate_score(p, weights), 1)
        scored.append(p)

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored[:top_n]
