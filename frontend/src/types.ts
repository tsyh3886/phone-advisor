export interface Phone {
  id: number;
  name: string;
  brand: string;
  price: number;
  processor: string;
  ram: number;
  storage: number;
  battery: number;
  charging_speed: number;
  weight: number;
  gaming_score: number;
  photo_score: number;
  battery_score: number;
  tags: string[];
  summary: string;
}

export interface SSEEvent {
  type: "question" | "reasoning" | "recommendation" | "comparison" | "text" | "error" | "done";
  content: string;
  phones?: Phone[];
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  type: "text" | "recommendation" | "comparison" | "question" | "reasoning" | "error";
  phones?: Phone[];
  timestamp: number;
}
