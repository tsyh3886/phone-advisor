"""手机智能导购 Agent - FastAPI 后端入口"""

import json
import asyncio
import re
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import uvicorn

from database import (
    get_all_phones,
    get_phone_by_id,
    filter_phones,
    search_phones_by_name,
    recommend as score_recommend,
)
from state import get_or_create_session, update_session_from_llm
from llm import parse_intent, generate_recommendation, compare_phones
from web_search import search_phones, build_search_query
from faq import match_faq, OFFTOPIC_RESPONSE, is_offtopic

app = FastAPI(title="手机智能导购 Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/phones")
def list_phones():
    """获取所有机型列表"""
    return {"total": 30, "phones": get_all_phones()}


@app.get("/api/phones/filter")
def filter_phones_api(
    price_min: float = None,
    price_max: float = None,
    need_nfc: bool = None,
    need_35mm: bool = None,
    need_ip68: bool = None,
):
    """按条件过滤机型"""
    results = filter_phones(
        price_min=price_min,
        price_max=price_max,
        need_nfc=need_nfc,
        need_35mm=need_35mm,
        need_ip68=need_ip68,
    )
    return {"total": len(results), "phones": results}


@app.get("/api/phones/{phone_id}")
def phone_detail(phone_id: int):
    """获取单个机型详情"""
    phone = get_phone_by_id(phone_id)
    if not phone:
        return {"error": "机型不存在"}, 404
    return phone


# 价格快捷查询
def handle_price_query(text: str):
    """检查用户是否在询问价格，返回 (类型, 内容) 或 (None, None)"""
    m = re.search(r'(.+?)多少钱\??$', text.strip())
    if not m:
        m = re.search(r'(.+?)什么?价格\??$', text.strip())
    if not m:
        return None, None
    name_part = m.group(1).strip()
    phones = search_phones_by_name(name_part)
    if phones:
        phone = phones[0]
        return "result", f"📱 {phone['name']} 当前参考价：**¥{phone['price']}**（{phone['summary']}）"
    # 数据库没有，需要联网搜索
    return "search", name_part


@app.post("/api/chat/message")
async def chat_message(request: Request):
    """对话接口 - SSE 流式响应"""
    body = await request.json()
    session_id = body.get("session_id", "default")
    message = body.get("message", "").strip()

    if not message:
        return {"error": "消息不能为空"}

    session = get_or_create_session(session_id)

    async def event_generator():
        # 0. FAQ 快速匹配（闲聊/问候等，跳过 LLM 调用）
        faq_reply = match_faq(message)
        if faq_reply:
            session.message_history.append({"role": "user", "content": message})
            session.message_history.append({"role": "assistant", "content": faq_reply})
            yield {"event": "message", "data": json.dumps(
                {"type": "text", "content": faq_reply}
            )}
            yield {"event": "message", "data": json.dumps({"type": "done"})}
            return

        # 0.5. 价格快捷查询
        price_type, price_reply = handle_price_query(message)
        if price_type == "result":
            session.message_history.append({"role": "user", "content": message})
            session.message_history.append({"role": "assistant", "content": price_reply})
            yield {"event": "message", "data": json.dumps(
                {"type": "text", "content": price_reply}
            )}
            yield {"event": "message", "data": json.dumps({"type": "done"})}
            return
        elif price_type == "search":
            # 数据库中没找到，联网搜索价格
            yield {"event": "message", "data": json.dumps(
                {"type": "reasoning", "content": f"正在查询「{price_reply}」的价格..."}
            )}
            await asyncio.sleep(0.3)

            # 尝试多个搜索词提高命中率
            search_queries = [
                f"{price_reply} 价格 京东 2025",
                f"{price_reply} 手机 价格",
            ]
            web_results = None
            for q in search_queries:
                web_results = search_phones(q)
                if web_results and web_results[0].get("title") != "搜索失败":
                    break
            if web_results and web_results[0].get("title") != "搜索失败":
                from llm import _get_client, _get_model
                client = _get_client()
                model = _get_model()
                prompt = f"用户想知道「{price_reply}」的价格。根据以下搜索结果，直接给出价格信息。只输出价格和必要说明，不要加「根据搜索结果」「搜索显示」等前缀，不要解释搜索过程。如果搜索结果中没有价格信息，只输出「暂未查到该机型价格」。\n\n搜索结果：\n" + "\n".join(
                    f"- {r.get('title','')}: {r.get('body','')[:200]}"
                    for r in web_results[:3]
                )
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )
                result_text = resp.choices[0].message.content
            else:
                result_text = f"暂未查到「{price_reply}」的价格。"

            session.message_history.append({"role": "user", "content": message})
            session.message_history.append({"role": "assistant", "content": result_text})
            yield {"event": "message", "data": json.dumps(
                {"type": "text", "content": result_text}
            )}
            yield {"event": "message", "data": json.dumps({"type": "done"})}
            return

        # 0.6. 无关话题检测
        if is_offtopic(message):
            yield {"event": "message", "data": json.dumps(
                {"type": "text", "content": OFFTOPIC_RESPONSE}
            )}
            yield {"event": "message", "data": json.dumps({"type": "done"})}
            return

        # 1. LLM 解析用户意图
        parsed = parse_intent(message, session.to_dict())

        if "error" in parsed:
            yield {"event": "message", "data": json.dumps(
                {"type": "error", "content": "抱歉，我现在有点忙，请稍后再试。"}
            )}
            return

        # 2. 更新会话状态（先保存旧价格，用于 adjust 检测）
        old_min, old_max = session.price_min, session.price_max
        update_session_from_llm(session, parsed)

        # 3. 判断意图类型
        intent = parsed.get("user_intent", "normal")

        if intent == "compare":
            # 对比模式：优先从用户输入匹配机型
            phones_to_compare = search_phones_by_name(message)[:2]

            # 未找到两款，尝试从最近推荐里补齐
            if len(phones_to_compare) < 2 and session.last_recommended_ids:
                phone_ids = session.last_recommended_ids[:2]
                for pid in phone_ids:
                    p = get_phone_by_id(pid)
                    if p and p not in phones_to_compare:
                        phones_to_compare.append(p)
                        if len(phones_to_compare) >= 2:
                            break

            # 仍不够两款，直接提示
            if len(phones_to_compare) >= 2:
                yield {"event": "message", "data": json.dumps(
                    {"type": "reasoning", "content": "好的，我来对比这两款机型。"}
                )}
                await asyncio.sleep(0.3)
                result = compare_phones(phones_to_compare)
                yield {"event": "message", "data": json.dumps(
                    {"type": "comparison", "content": result}
                )}
            else:
                yield {"event": "message", "data": json.dumps(
                    {"type": "text", "content": "抱歉，没有找到可对比的机型。请明确两款机型的名称。"}
                )}
            yield {"event": "message", "data": json.dumps({"type": "done"})}
            return

        # 3.5. 查看更多推荐
        more_rec = parsed.get("more_recommendations", False)
        if more_rec and session.all_candidate_ids:
            offset = session.recommend_offset
            next_ids = session.all_candidate_ids[offset:offset+5]
            if not next_ids:
                yield {"event": "message", "data": json.dumps(
                    {"type": "text", "content": "已为你展示所有可选机型，如果都不满意，可以告诉我新的需求，我帮你重新筛选。"}
                )}
                yield {"event": "message", "data": json.dumps({"type": "done"})}
                return

            next_phones = [get_phone_by_id(pid) for pid in next_ids if get_phone_by_id(pid)]
            session.recommend_offset = offset + len(next_phones)

            yield {"event": "message", "data": json.dumps(
                {"type": "reasoning", "content": "再看看这几款是否合你心意："}
            )}
            await asyncio.sleep(0.3)

            req_desc = f"预算{'%d-%d' % (session.price_min or 0, session.price_max or 99999)}元"
            if session.use_cases:
                req_desc += f"，用途：{'、'.join(session.use_cases)}"
            try:
                recommendation = generate_recommendation(req_desc, next_phones)
            except Exception:
                recommendation = "\n\n".join([
                    f"**{p['name']}** — ¥{p['price']}\n{p['summary']}"
                    for p in next_phones
                ])
            yield {"event": "message", "data": json.dumps(
                {"type": "recommendation", "content": recommendation, "phones": next_phones[:3]}
            )}
            yield {"event": "message", "data": json.dumps({"type": "done"})}
            return

        # 4. 判断是否需要继续追问
        needs_info = parsed.get("need_more_info", True)
        # 如果用户说要调整预算，不需要追问，直接调
        if intent == "adjust":
            needs_info = False
            # 自动降价 30%，不依赖 LLM 的价格解析
            if old_max:
                session.price_max = int(old_max * 0.7)
                session.price_min = int(old_max * 0.5) if old_min == old_max else int(old_min * 0.7)
        # 如果用户没给预算，必须追问
        if session.price_min is None and session.price_max is None:
            needs_info = True
        # 已追问超过 2 轮，强制推荐
        if needs_info and session.question_count >= 2:
            needs_info = False
            session.stage = "recommending"
        # 即使 LLM 说还需要信息，但会话已有足够信息时，直接推荐
        if needs_info and session.is_ready_to_recommend():
            needs_info = False
            session.stage = "recommending"

        if needs_info:
            # 推进状态机
            session.advance_stage()
            session.question_count += 1
            question = parsed.get("next_question") or session.get_next_question()
            yield {"event": "message", "data": json.dumps(
                {"type": "question", "content": question}
            )}
            yield {"event": "message", "data": json.dumps({"type": "done"})}
            return

        # 5. 收集到足够信息，进入推荐流程
        session.stage = "recommending"

        # 5a. 过滤
        candidates = filter_phones(
            price_min=session.price_min,
            price_max=session.price_max,
            need_nfc="nfc" in session.must_haves,
            need_ip68="ip68" in session.must_haves,
            need_35mm="耳机孔" in session.must_haves,
            brands=session.brand_preference if session.brand_preference else None,
        )

        if not candidates:
            # 尝试扩展价格范围 ±500
            expanded_min = session.price_min - 500 if session.price_min else None
            expanded_max = session.price_max + 500 if session.price_max else None
            candidates = filter_phones(
                price_min=expanded_min,
                price_max=expanded_max,
                need_nfc="nfc" in session.must_haves,
                need_ip68="ip68" in session.must_haves,
                need_35mm="耳机孔" in session.must_haves,
                brands=session.brand_preference if session.brand_preference else None,
            )
            # 如果扩展后最便宜的机型价格仍远超预算（> 1.5倍），视作无匹配，走联网搜索
            if candidates and session.price_max:
                min_price = min(p["price"] for p in candidates)
                if min_price > session.price_max * 1.5:
                    candidates = []

        if not candidates:
            # 数据库无匹配，触发联网搜索
            yield {"event": "message", "data": json.dumps(
                {"type": "reasoning", "content": "正在为你查找合适的机型..."}
            )}
            await asyncio.sleep(0.3)

            search_query = build_search_query(
                price_min=session.price_min,
                price_max=session.price_max,
                use_cases=session.use_cases,
                priorities=session.priorities,
            )
            web_results = search_phones(search_query)

            if web_results and web_results[0].get("title") != "搜索失败":
                # 将搜索结果传给 LLM 生成推荐，同时带上数据库机型供前端展示卡片
                search_phones_data = filter_phones(price_min=session.price_min, price_max=session.price_max)
                if not search_phones_data:
                    # 预算内无数据，用全部数据兜底（仅当价格接近时）
                    search_phones_data = filter_phones()
                    if search_phones_data and session.price_max:
                        min_p = min(p["price"] for p in search_phones_data)
                        if min_p > session.price_max * 1.5:
                            search_phones_data = []
                # 如果兜底数据也被清空（远超预算），不推荐，直接提示
                if not search_phones_data and session.price_max:
                    yield {"event": "message", "data": json.dumps(
                        {"type": "text", "content": "在这个价位段暂未找到合适的机型，建议调整预算后重试。"}
                    )}
                else:
                    result_text = generate_recommendation(
                        f"用户需求：{session.to_dict()}\n参考信息：{json.dumps(web_results, ensure_ascii=False)}",
                        search_phones_data[:5]
                    )
                    yield {"event": "message", "data": json.dumps(
                        {"type": "recommendation", "content": result_text, "phones": search_phones_data[:3]}
                    )}
            else:
                # 搜索也失败，用数据库已有数据兜底推荐（仅当价格接近时）
                fallback = filter_phones()
                if fallback and session.price_max:
                    min_price = min(p["price"] for p in fallback)
                    if min_price > session.price_max * 1.5:
                        fallback = []
                if fallback:
                    result_text = generate_recommendation(
                        f"用户需求：{session.to_dict()}",
                        fallback[:5]
                    )
                    yield {"event": "message", "data": json.dumps(
                        {"type": "recommendation", "content": result_text, "phones": fallback[:3]}
                    )}
                else:
                    yield {"event": "message", "data": json.dumps(
                        {"type": "text", "content": "在这个价位段暂未找到合适的机型，建议调整预算后重试。"}
                    )}
            yield {"event": "message", "data": json.dumps({"type": "done"})}
            return

        # 5b. 加权评分 - 优先用 priorities（用户明确指定），其次用 use_cases
        weights = {"gaming": 0.25, "photo": 0.25, "battery": 0.25, "processor": 0.25}
        if session.priorities:
            if "photo" in session.priorities:
                weights = {"gaming": 0.1, "photo": 0.45, "battery": 0.2, "processor": 0.25}
            elif "gaming" in session.priorities:
                weights = {"gaming": 0.45, "photo": 0.1, "battery": 0.25, "processor": 0.2}
            elif "battery" in session.priorities:
                weights = {"gaming": 0.1, "photo": 0.15, "battery": 0.5, "processor": 0.25}
        else:
            if "拍照" in session.use_cases:
                weights = {"gaming": 0.1, "photo": 0.45, "battery": 0.2, "processor": 0.25}
            elif "游戏" in session.use_cases:
                weights = {"gaming": 0.45, "photo": 0.1, "battery": 0.25, "processor": 0.2}
            elif "续航" in session.use_cases:
                weights = {"gaming": 0.1, "photo": 0.15, "battery": 0.5, "processor": 0.25}

        top_phones = score_recommend(candidates, weights, top_n=3)
        session.last_recommended_ids = [p["id"] for p in top_phones]
        # 保存完整排序列表，供"还有吗"使用
        all_scored = score_recommend(candidates, weights, top_n=len(candidates))
        session.all_candidate_ids = [p["id"] for p in all_scored]
        session.recommend_offset = 3

        # 5c. 构建用户需求描述
        req_desc = f"预算{'%d-%d' % (session.price_min or 0, session.price_max or 99999)}元"
        if session.use_cases:
            req_desc += f"，用途：{'、'.join(session.use_cases)}"
        if session.priorities:
            req_desc += f"，关注：{'、'.join(session.priorities)}"

        # 5d. 生成推荐理由
        yield {"event": "message", "data": json.dumps(
            {"type": "reasoning", "content": "根据你的需求，我重点推荐以下三款机型："}
        )}
        await asyncio.sleep(0.3)

        # 调整预算场景：跳过 LLM 生成，用模板
        if intent == "adjust":
            recommendation = "\n\n".join([
                f"**{p['name']}** — ¥{p['price']}\n💡 {p['summary']}"
                for p in top_phones
            ])
        else:
            try:
                recommendation = generate_recommendation(req_desc, top_phones)
            except Exception:
                recommendation = "\n\n".join([
                    f"**{p['name']}** — ¥{p['price']}\n{p['summary']}"
                    for p in top_phones
                ])

        yield {"event": "message", "data": json.dumps(
            {"type": "recommendation", "content": recommendation, "phones": top_phones}
        )}

        # 5e. 发送快捷选项
        yield {"event": "message", "data": json.dumps({"type": "done"})}

    return EventSourceResponse(event_generator())


@app.post("/api/chat/reset")
async def reset_chat(request: Request):
    """重置对话"""
    body = await request.json()
    session_id = body.get("session_id", "default")
    session = get_or_create_session(session_id)
    session.reset()
    return {"message": "对话已重置"}


# 部署环境：托管前端静态文件
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
