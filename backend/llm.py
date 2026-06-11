"""LLM 调用封装与 Prompt 设计"""

import json
import os
from openai import OpenAI


def _get_client():
    """创建 LLM 客户端，兼容 OpenAI / DeepSeek / 通义千问"""
    base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("LLM_API_KEY", "")
    return OpenAI(base_url=base_url, api_key=api_key)


def _get_model():
    return os.getenv("LLM_MODEL", "gpt-4o-mini")


# ============================================================
# Prompt 1: 需求理解（Intent Parsing）
# ============================================================

SYSTEM_PROMPT_PARSE = """你是一名专业的手机导购助手，语气简洁、专业、有礼貌。像 Siri 一样高效地帮助用户找到合适的手机。

对话原则：
1. 快速识别用户意图。如果用户在打招呼或闲聊，礼貌回应后立即引导回选手机的正题。
2. 信息不足时只追问最关键的一个问题（预算或用途），不要同时问多个。
3. 追问次数控制在 2 次以内，2 次后即使信息不全也应开始推荐。
4. 如果用户表达了价格和用途需求，请将 need_more_info 设为 false，直接进入推荐环节，不必追问细节。
5. 回答简洁，不要多余寒暄。
6. 如果用户提到两款机型的对比（如"哪个好"、"谁更强"、"有什么区别"、"vs"、"对比"等），将 user_intent 设为 "compare"。
7. 如果用户表达调整预算或需求的意图（如"太贵了"、"便宜点"、"换个贵的"、"要好点的"等），将 user_intent 设为 "adjust"。
8. 如果用户想要查看更多推荐（如"还有吗"、"其他的呢"、"再多推荐几款"、"还有别的吗"等），在 JSON 中将 need_more_info 设为 false，并将 more_recommendations 设为 true。

当前对话历史：
{history}

用户最新消息：{message}

价格解析规则：当用户给出一个精确价格（如"4000元"），直接设为 price_min=price_max=该价格，不要扩展。后续数据库搜索会自动扩展范围。

输出 JSON 格式：{{"price_min": 数字或null, "price_max": 数字或null, "use_cases": ["游戏","拍照","续航","日常","视频"], "priorities": ["gaming","photo","battery","performance"], "must_haves": ["nfc","ip68","耳机孔"], "deal_breakers": [], "brand_preference": ["品牌名"], "need_more_info": true/false, "more_recommendations": false, "next_question": "追问内容（一句话）", "user_intent": "normal|compare|adjust"}}

只输出 JSON，不要额外文字。"""


def parse_intent(message: str, session_state: dict) -> dict:
    """用 LLM 解析用户输入，返回结构化需求"""
    history_str = json.dumps(session_state, ensure_ascii=False)
    prompt = SYSTEM_PROMPT_PARSE.format(history=history_str, message=message)
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=_get_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        return {
            "error": str(e),
            "need_more_info": True,
            "next_question": "请告诉我你的预算和主要用途，我来推荐合适的手机。",
        }


# ============================================================
# Prompt 2: 推荐理由生成
# ============================================================

SYSTEM_PROMPT_RECOMMEND = """你是一名专业的手机导购助手，语气简洁、专业、可靠，就像 Siri 一样清晰直接。

用户需求：{user_requirement}

{phones_json}

请根据用户的需求，推荐 3 款最合适的机型。用简洁的卡片格式输出，每款机型包含：
- 机型名称和价格
- 一句话核心亮点
- 适合用户的理由

格式如下（不要使用 # 符号）：

① {{机型名称}} — ¥{{价格}}
{{一句话核心亮点}}

适合你的理由：{{为什么这款适合该用户}}

规则：
- **必须推荐 3 款**，按匹配度排序，最推荐的那款标注 ⭐
- 亮点之间用 ｜ 分隔，每款选 3 个核心卖点（评分/特性/功能）
- 理由用一句话说清楚"为什么这款适合该用户"
- 不要多余寒暄，直接给出推荐内容
- **如果用户没有指定用途，不要猜测或默认"打游戏"，改为从综合性能、屏幕、续航等角度推荐，用途统一写"综合使用"**
- **如果用户需求中包含"京东等电商平台获取的实时价格信息"，请以此为准作为机型的最新售价，确保价格准确且是最新的**
- **只推荐 2025、2026 年发布的最新机型，不要推荐 2024 年及以前的旧款**
"""


def generate_recommendation(user_requirement: str, phones: list[dict]) -> str:
    """生成推荐理由"""
    phones_json = json.dumps(
        [
            {
                "name": p["name"],
                "brand": p["brand"],
                "price": p["price"],
                "summary": p["summary"],
                "gaming_score": p["gaming_score"],
                "photo_score": p["photo_score"],
                "battery_score": p["battery_score"],
                "tags": p["tags"],
            }
            for p in phones
        ],
        ensure_ascii=False,
        indent=2,
    )
    prompt = SYSTEM_PROMPT_RECOMMEND.format(
        user_requirement=user_requirement,
        phones_json=phones_json,
    )
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=_get_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"生成推荐时出错：{str(e)}"


# ============================================================
# Prompt 3: 横向对比
# ============================================================

SYSTEM_PROMPT_COMPARE = """你是一名专业的手机导购助手。以下两款机型供你对比分析。

{phones_json}

请从核心差异出发，用简洁的表格输出对比（不要使用 # 符号）：

参数对比
| 参数 | {name_a} | {name_b} |
|---|---|---|
| 价格 | ... | ... |
| 处理器 | ... | ... |
| 电池 | ... | ... |
| 游戏性能 | ... | ... |
| 拍照能力 | ... | ... |
| 续航表现 | ... | ... |

总结：{{最核心的区别和选购建议}}"""


def compare_phones(phones: list[dict]) -> str:
    """生成两款机型的对比分析"""
    phones_json = json.dumps(
        [
            {
                "name": p["name"],
                "price": p["price"],
                "processor": p["processor"],
                "ram": p["ram"],
                "storage": p["storage"],
                "battery": p["battery"],
                "weight": p["weight"],
                "gaming_score": p["gaming_score"],
                "photo_score": p["photo_score"],
                "battery_score": p["battery_score"],
                "summary": p["summary"],
            }
            for p in phones
        ],
        ensure_ascii=False,
        indent=2,
    )

    names = [p["name"] for p in phones]
    prompt = SYSTEM_PROMPT_COMPARE.format(
        phones_json=phones_json,
        name_a=names[0] if len(names) > 0 else "",
        name_b=names[1] if len(names) > 1 else "",
    )
    try:
        client = _get_client()
        resp = client.chat.completions.create(
            model=_get_model(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"生成对比时出错：{str(e)}"
