import { useState, useRef, useEffect } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export default function ChatInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // 发送完成后自动聚焦
  useEffect(() => {
    if (!disabled && inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  const handleSubmit = () => {
    const text = input.trim();
    if (!text || disabled) return;
    onSend(text);
    setInput("");
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  };

  return (
    <div className="flex items-end gap-3 px-4 py-3">
      <div className="flex-1 relative">
        <textarea
          ref={inputRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="描述你的需求..."
          rows={1}
          disabled={disabled}
          className="w-full bg-warm-surface border border-warm-border rounded-xl px-4 py-2.5 pr-10 text-sm text-text-primary placeholder-text-muted resize-none outline-none focus:border-warm-accent focus:ring-1 focus:ring-warm-accent/20 transition-all duration-200"
        />
      </div>
      <button
        onClick={handleSubmit}
        disabled={disabled || !input.trim()}
        className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-warm-accent to-warm-amber text-white font-semibold text-sm disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-warm-accent/20 transition-all duration-200 active:scale-95"
      >
        发送
      </button>
    </div>
  );
}
