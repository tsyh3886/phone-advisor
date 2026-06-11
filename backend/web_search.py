"""联网搜索：当数据库无匹配时，从网上获取手机推荐"""

from ddgs import DDGS


def search_phones(query: str, max_results: int = 5) -> list[dict]:
    """搜索手机相关信息"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [
                {"title": r.get("title", ""), "body": r.get("body", ""), "href": r.get("href", "")}
                for r in results
            ]
    except Exception as e:
        return [{"title": "搜索失败", "body": str(e), "href": ""}]


def build_search_query(price_min=None, price_max=None, use_cases=None, priorities=None) -> str:
    """根据用户需求构建搜索关键词（去重）"""
    parts = ["2025", "2026", "新款", "京东", "手机推荐"]
    seen = set()

    if price_min and price_max:
        parts.append(f"{price_min}元到{price_max}元")
    elif price_min:
        parts.append(f"{price_min}元以上")
    elif price_max:
        parts.append(f"{price_max}元以下")

    use_case_map = {"游戏": "游戏", "拍照": "拍照", "续航": "长续航", "日常": "日常使用"}
    priority_map = {"gaming": "游戏性能", "photo": "拍照", "battery": "续航"}

    keywords = []
    if use_cases:
        for u in use_cases:
            w = use_case_map.get(u, u)
            if w not in seen:
                keywords.append(w)
                seen.add(w)
    if priorities:
        for p in priorities[:2]:
            w = priority_map.get(p, p)
            if w not in seen:
                keywords.append(w)
                seen.add(w)

    parts.extend(keywords)
    return " ".join(parts)
