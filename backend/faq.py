"""常见闲聊 FAQ：快速回应常见问候/闲聊，引导用户回到选购正题"""

import re

# 手机选购相关关键词
PHONE_KEYWORDS = [
    "手机", "买", "推荐", "预算", "价格", "元", "千", "万",
    "性能", "拍照", "续航", "电池", "屏幕", "处理器", "内存",
    "像素", "充电", "快充", "游戏", "轻薄", "品牌",
    "便宜", "贵", "性价比", "降价", "优惠", "划算", "价位",
    "小米", "华为", "苹果", "OPPO", "vivo", "三星", "荣耀",
    "redmi", "iPhone", "Samsung", "Pro", "Max", "Ultra",
    "骁龙", "天玑", "A系列", "麒麟",
    "对比", "哪个好", "比较好", "选", "买哪个",
]


def is_phone_related(message: str) -> bool:
    """判断消息是否与手机选购相关"""
    for keyword in PHONE_KEYWORDS:
        if keyword.lower() in message.lower():
            return True
    return False


FAQ_RESPONSES = [
    {
        "patterns": [r"^(涵涵|hán|hanhan|心心)$"],
        "response": "❤️ 涵涵最好了~",
    },
    {
        "patterns": [r"^(你好|嗨|hi|hello|hey|您好|在吗|在不在)$"],
        "response": "嗨！我是你的手机选搭师~ 说说你的预算和需求，包你挑到合适的手机！",
    },
    {
        "patterns": [r"^(你是谁|你是什么|你叫什么|什么AI)$"],
        "response": "我是你的私人手机选搭师！告诉我预算和用途，帮你挑最对的那款~",
    },
    {
        "patterns": [r"^(你能做什么|你会什么|有什么用|功能)$"],
        "response": "我可以帮你推荐最合适的手机，还支持多款对比~ 说说你的预算和需求吧！",
    },
    {
        "patterns": [r"^(谢谢|感谢|好的|ok|okay|知道了|明白)$"],
        "response": "不客气！有需要随时找我，比如调调预算或者对比几款机型~",
    },
    {
        "patterns": [r"^(推荐一款|推荐手机|推荐|有什么推荐)$"],
        "response": "没问题！先告诉我你的预算和主要用途，我马上帮你安排~",
    },
    {
        "patterns": [r"^(再见|拜拜|bye|走了|下次)$"],
        "response": "拜拜~ 有购机需求随时回来找我！",
    },
]

OFFTOPIC_RESPONSE = "我是手机选搭师，只聊手机选购哦~ 告诉我你的预算和用途，帮你挑最合适的机型！"

# 明确无关话题短语（不受字符数限制，直接拦截）
EXPLICIT_OFFTOPIC = [
    "天气", "时间", "日期", "新闻", "吃饭", "睡觉",
    "音乐", "电影", "笑话", "故事", "股票", "汇率",
    "星座", "运势", "八卦", "体育", "足球", "篮球",
]


def match_faq(message: str) -> str | None:
    """检查是否匹配 FAQ，匹配则返回预设回复"""
    msg = message.strip()
    for faq in FAQ_RESPONSES:
        for pattern in faq["patterns"]:
            if re.match(pattern, msg, re.IGNORECASE):
                return faq["response"]
    return None


def is_offtopic(message: str) -> bool:
    """判断是否为与手机选购无关的话题"""
    if is_phone_related(message):
        return False
    # 如果 FAQ 匹配到了，不算 offtopic
    if match_faq(message):
        return False
    # 检查明确无关话题短语
    for phrase in EXPLICIT_OFFTOPIC:
        if phrase in message:
            return True
    # 消息较短（< 10 个字符），可能是对 AI 追问的简短回复（预算数字等），交给 LLM 处理
    if len(message.strip()) < 10:
        return False
    return True
