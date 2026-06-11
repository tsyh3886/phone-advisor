"""多轮对话状态机"""

from enum import Enum


class Stage(str, Enum):
    START = "start"
    ASK_BUDGET = "ask_budget"
    ASK_USECASE = "ask_usecase"
    RECOMMENDING = "recommending"
    COMPARING = "comparing"


INITIAL_QUESTIONS = {
    Stage.ASK_BUDGET: "你的预算大概是多少？比如 2000-3000 元、或者 4000 元左右。",
    Stage.ASK_USECASE: "平时主要用手机做什么？\n\n🎮 打游戏  📷 拍照  🔋 续航优先  📱 日常使用",
}


class SessionState:
    """单个对话会话的状态"""

    def __init__(self):
        self.stage: Stage = Stage.START
        self.price_min: float | None = None
        self.price_max: float | None = None
        self.use_cases: list[str] = []
        self.priorities: list[str] = []
        self.must_haves: list[str] = []
        self.deal_breakers: list[str] = []
        self.brand_preference: list[str] = []
        self.last_recommended_ids: list[int] = []
        self.all_candidate_ids: list[int] = []   # 当前推荐的全部候选机型 ID
        self.recommend_offset: int = 0            # 已展示到第几个
        self.message_history: list[dict] = []
        self.question_count: int = 0

    def to_dict(self):
        return {
            "stage": self.stage.value if isinstance(self.stage, Stage) else self.stage,
            "price_min": self.price_min,
            "price_max": self.price_max,
            "use_cases": self.use_cases,
            "priorities": self.priorities,
            "must_haves": self.must_haves,
            "deal_breakers": self.deal_breakers,
            "brand_preference": self.brand_preference,
        }

    def is_ready_to_recommend(self) -> bool:
        """判断是否收集到足够信息进行推荐"""
        has_price = self.price_min is not None or self.price_max is not None
        has_scenario = len(self.use_cases) > 0 or len(self.priorities) > 0
        return has_price and has_scenario

    def advance_stage(self):
        """根据已收集的信息推进到下一阶段"""
        if self.stage == Stage.START:
            self.stage = Stage.ASK_BUDGET
        elif self.stage == Stage.ASK_BUDGET:
            self.stage = Stage.ASK_USECASE
        elif self.stage == Stage.ASK_USECASE:
            self.stage = Stage.RECOMMENDING

    def get_next_question(self) -> str | None:
        """获取当前阶段需要追问的问题"""
        if self.stage == Stage.START:
            self.advance_stage()
        return INITIAL_QUESTIONS.get(self.stage)

    def reset(self):
        """重置对话"""
        self.__init__()


# 全局会话存储（简单实现，生产环境应用 Redis）
sessions: dict[str, SessionState] = {}


def get_or_create_session(session_id: str) -> SessionState:
    """获取或创建会话"""
    if session_id not in sessions:
        sessions[session_id] = SessionState()
    return sessions[session_id]


def update_session_from_llm(session: SessionState, parsed: dict):
    """根据 LLM 解析结果更新会话状态"""
    if parsed.get("price_min") is not None:
        session.price_min = parsed["price_min"]
    if parsed.get("price_max") is not None:
        session.price_max = parsed["price_max"]
    if parsed.get("use_cases"):
        session.use_cases = list(set(session.use_cases + parsed["use_cases"]))
    if parsed.get("priorities"):
        session.priorities = list(set(session.priorities + parsed["priorities"]))
    if parsed.get("must_haves"):
        session.must_haves = list(set(session.must_haves + parsed["must_haves"]))
    if parsed.get("deal_breakers"):
        session.deal_breakers = list(
            set(session.deal_breakers + parsed["deal_breakers"])
        )
    if parsed.get("brand_preference"):
        session.brand_preference = list(
            set(session.brand_preference + parsed["brand_preference"])
        )
