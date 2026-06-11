import { useMemo } from "react";
import { marked } from "marked";
import type { Message } from "../types";

interface Props {
  message: Message;
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  const htmlContent = useMemo(() => {
    if (isUser) return message.content;
    return marked.parse(message.content, { breaks: true }) as string;
  }, [message.content, isUser]);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} gap-3`}>
      {/* Assistant avatar */}
      {!isUser && (
        <div className="w-8 h-8 mt-0.5 rounded-lg bg-gradient-to-br from-warm-accent to-warm-amber flex items-center justify-center text-xs font-bold text-white flex-shrink-0 shadow-sm">
          AI
        </div>
      )}

      {isUser ? (
        <div className="max-w-[80%] bg-gradient-to-r from-warm-accent to-warm-amber text-white rounded-2xl rounded-tr-md px-4 py-2.5 shadow-sm">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
      ) : (
        <div
          className="max-w-[80%] bg-warm-surface border border-warm-border rounded-2xl px-4 py-3 card-shadow prose prose-sm prose-warm"
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />
      )}

      {/* User - no avatar */}
      {isUser && <div className="w-8 h-8 flex-shrink-0" />}
    </div>
  );
}
