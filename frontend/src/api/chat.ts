import type { SSEEvent } from "../types";

let sessionId = "session_" + Math.random().toString(36).slice(2);

export function resetSession() {
  sessionId = "session_" + Math.random().toString(36).slice(2);
  fetch("/api/chat/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  }).catch(() => {});
}

export async function sendMessage(
  message: string,
  onEvent: (event: SSEEvent) => void,
  onError: (error: string) => void
): Promise<void> {
  const response = await fetch("/api/chat/message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!response.ok) {
    onError(`请求失败 (${response.status})`);
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onError("无法读取响应");
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ")) {
          try {
            const data = JSON.parse(trimmed.slice(6));
            onEvent(data as SSEEvent);
          } catch {
            // skip malformed JSON
          }
        }
      }
    }
  } catch (err) {
    onError("连接中断");
  }
}
