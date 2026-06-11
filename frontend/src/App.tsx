import { useState, useRef, useEffect } from "react";
import type { Message, SSEEvent, Phone } from "./types";
import { sendMessage, resetSession } from "./api/chat";
import ChatMessage from "./components/ChatMessage";
import ChatInput from "./components/ChatInput";
import PhoneCard from "./components/PhoneCard";
import CompareView from "./components/CompareView";
import HeartAnimation from "./lib/HeartEffect";

function generateId() {
  return "msg_" + Date.now() + "_" + Math.random().toString(36).slice(2, 6);
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: '欢迎使用手机智能导购。请告诉我你的预算和需求，我来推荐最合适的机型。\n\n例如："3000左右，主要打游戏"',
      type: "text",
      timestamp: Date.now(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [recommendedPhones, setRecommendedPhones] = useState<Phone[]>([]);
  const [showCompare, setShowCompare] = useState(false);
  const [showHeart, setShowHeart] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text: string) => {
    // 彩蛋：输入"涵涵"只触发爱心，不回复
    if (text.includes("涵涵")) {
      setShowHeart(true);
      setTimeout(() => setShowHeart(false), 3000);
      return;
    }

    const userMsg: Message = {
      id: generateId(),
      role: "user",
      content: text,
      type: "text",
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    let assistantContent = "";
    let currentPhones: Phone[] = [];
    let hasRecommendation = false;

    const assistantMsgId = generateId();
    const assistantMsg: Message = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      type: "text",
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    await sendMessage(
      text,
      (event: SSEEvent) => {
        if (event.type === "done") {
          setIsLoading(false);
          return;
        }
        if (event.type === "recommendation") {
          hasRecommendation = true;
          assistantContent = event.content;
          if (event.phones) {
            currentPhones = event.phones;
            setRecommendedPhones(event.phones);
          }
        } else if (event.type === "comparison") {
          assistantContent = event.content;
        } else if (event.type === "error") {
          assistantContent = event.content;
        } else {
          assistantContent += event.content + "\n";
        }

        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: hasRecommendation ? event.content : assistantContent,
                  type: (hasRecommendation ? "recommendation" : event.type) as Message["type"],
                  phones: currentPhones.length > 0 ? currentPhones : m.phones,
                }
              : m
          )
        );
      },
      (error: string) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: `错误: ${error}`, type: "error" }
              : m
          )
        );
        setIsLoading(false);
      }
    );
  };

  const handleReset = () => {
    resetSession();
    setMessages([
      {
        id: "welcome",
        role: "assistant",
        content: "对话已重置。请重新告诉我你的预算和需求。",
        type: "text",
        timestamp: Date.now(),
      },
    ]);
    setRecommendedPhones([]);
    setShowCompare(false);
  };

  return (
    <div className="flex flex-col h-screen bg-warm-base">
      {showHeart && <HeartAnimation />}
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-warm-border bg-warm-surface/80 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-warm-accent to-warm-amber flex items-center justify-center text-sm font-bold text-white">
            AI
          </div>
          <div>
            <h1 className="text-lg font-bold text-text-primary tracking-tight">
              手机智能导购
            </h1>
            <p className="text-xs text-text-muted font-mono">Phone Advisor</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {recommendedPhones.length > 1 && (
            <button
              onClick={() => setShowCompare(!showCompare)}
              className="text-xs px-3 py-1.5 rounded-md border border-warm-border text-text-secondary hover:text-warm-teal hover:border-warm-teal/50 transition-all duration-200"
            >
              {showCompare ? "关闭对比" : "对比机型"}
            </button>
          )}
          <button
            onClick={handleReset}
            className="text-xs px-3 py-1.5 rounded-md border border-warm-border text-text-secondary hover:text-warm-rose hover:border-warm-rose/50 transition-all duration-200"
          >
            重置对话
          </button>
        </div>
      </header>

      {/* Main content area */}
      <div className="flex-1 overflow-hidden flex">
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
            {messages.map((msg, idx) => (
              <div key={msg.id} className={msg.role === "user" ? "" : "animate-in"}>
                <ChatMessage message={msg} />
                {msg.type === "recommendation" && msg.phones && msg.phones.length > 0 && (
                  <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
                    {msg.phones.map((phone) => (
                      <PhoneCard key={phone.id} phone={phone} />
                    ))}
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2 text-text-muted text-sm font-mono animate-in">
                <span className="w-2 h-2 rounded-full bg-warm-accent animate-pulse" />
                <span className="w-2 h-2 rounded-full bg-warm-accent animate-pulse" style={{ animationDelay: "0.2s" }} />
                <span className="w-2 h-2 rounded-full bg-warm-accent animate-pulse" style={{ animationDelay: "0.4s" }} />
                <span className="ml-1 text-xs">思考中</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-warm-border bg-warm-surface/80">
            <ChatInput onSend={handleSend} disabled={isLoading} />
          </div>
        </div>

        {/* Sidebar: compare view */}
        {showCompare && recommendedPhones.length > 1 && (
          <div className="hidden md:block w-96 border-l border-warm-border bg-warm-surface/80 overflow-y-auto p-4">
            <CompareView phones={recommendedPhones} />
          </div>
        )}
      </div>
    </div>
  );
}
