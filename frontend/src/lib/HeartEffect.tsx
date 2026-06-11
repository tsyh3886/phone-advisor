import { useEffect, useState } from "react";

export default function HeartAnimation() {
  const [visible, setVisible] = useState(true);
  const [hearts] = useState(() =>
    Array.from({ length: 20 }, (_, i) => ({
      id: i,
      left: Math.random() * 100,
      delay: Math.random() * 0.5,
      size: 14 + Math.random() * 24,
      duration: 1.5 + Math.random() * 1.5,
    }))
  );

  useEffect(() => {
    const timer = setTimeout(() => setVisible(false), 3000);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center">
      <div className="animate-heartbeat text-8xl select-none">❤️</div>
      {hearts.map((h) => (
        <div
          key={h.id}
          className="absolute animate-float-up select-none"
          style={{
            left: `${h.left}%`,
            bottom: "40%",
            fontSize: `${h.size}px`,
            animationDelay: `${h.delay}s`,
            animationDuration: `${h.duration}s`,
            opacity: 0.8,
          }}
        >
          {["❤️", "💖", "💗", "💕", "💓"][h.id % 5]}
        </div>
      ))}
    </div>
  );
}
