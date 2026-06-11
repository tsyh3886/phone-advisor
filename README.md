# 手机智能导购 Agent

基于大语言模型的交互式手机选购助手 — 就像跟一个懂手机的朋友聊天选机。

## 在线体验

部署后可通过公开链接在线体验，无需本地运行。

## 功能

| 能力    | 说明                                   |
| ----- | ------------------------------------ |
| 个性化推荐 | 输入预算 + 用途（拍照、打游戏、续航等），推荐最合适的机型       |
| 多轮追问  | 没说预算会追问，说"太贵了"自动调整降价推荐               |
| 更多推荐  | "还有吗" / "其他的呢" → 推送下一批机型             |
| 价格查询  | "小米14多少钱" → 秒查价格（数据库命中直接返回，未收录则联网搜索） |
| 机型对比  | "小米14和vivo X100哪个好" → 生成参数对比表格       |
| 闲聊对话  | 打招呼、告别、天气等日常对话也能自然回应                 |
| 交互界面  | 响应式聊天 UI，消息流式输出，对比表格渲染，仅需打字即可交互      |

## 技术栈

| 层级   | 技术                                              |
| ---- | ----------------------------------------------- |
| 前端   | React 19 + TypeScript + Vite 8 + Tailwind CSS 4 |
| 后端   | Python + FastAPI + SSE 流式响应                     |
| 大模型  | DeepSeek Chat（OpenAI 兼容 API）                    |
| 联网搜索 | DuckDuckGo Search API（数据不足时自动补充）                |
| 数据   | 内置 32 款主流机型参数（覆盖小米、华为、vivo、OPPO、三星、荣耀等品牌）       |

## 架构

```
用户输入 → LLM 意图解析 → 查询数据库 / 联网搜索 → LLM 生成推荐 → SSE 流式回显
               ↓                ↓
            闲聊命中         价格查询/对比
```

- **意图解析**：LLM 识别用户意图（推荐/对比/价格/闲聊），并提取预算、用途等结构化字段
- **推荐引擎**：按用户需求对候选机型多维度加权排序（性能、拍照、续航等）
- **兜底策略**：数据库无结果时自动联网搜索补充，仍找不到则如实告知

## 本地运行

### 前置条件

- Python 3.10+
- Node.js 18+

### 1. 克隆 & 安装

```bash
git clone <your-repo-url> && cd phone-advisor

# 后端
cd backend && pip install -r requirements.txt

# 前端
cd ../frontend && npm install
```

### 2. 配置环境变量

```bash
# backend/.env
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your_api_key_here
LLM_MODEL=deepseek-chat
```

### 3. 启动

**终端 A — 后端：**

```bash
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

**终端 B — 前端（开发模式）：**

```bash
cd frontend
npm run dev
```

打开 <http://localhost:5173> 即可使用。

## 部署

本项目设计为单服务器部署，后端自带前端静态文件托管。

### Render

1. GitHub 推送代码
2. Render 新建 Web Service，选择该仓库
3. 配置：

| 字段            | 值                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------- |
| Build Command | `cd frontend && npm install && npm run build`                                                  |
| Start Command | `cd backend && pip install -r requirements.txt && uvicorn app:app --host 0.0.0.0 --port $PORT` |
| 环境变量          | `LLM_BASE_URL` `LLM_API_KEY` `LLM_MODEL`                                                       |

***

