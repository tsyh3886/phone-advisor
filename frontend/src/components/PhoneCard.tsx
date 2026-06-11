import type { Phone } from "../types";

interface Props {
  phone: Phone;
}

export default function PhoneCard({ phone }: Props) {
  return (
    <div className="bg-warm-card border border-warm-border rounded-xl p-4 card-shadow transition-all duration-200 hover:shadow-md group">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="text-xs text-warm-teal font-mono mb-0.5">{phone.brand}</p>
          <h3 className="text-sm font-bold text-text-primary group-hover:text-warm-accent transition-colors">
            {phone.name}
          </h3>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-lg font-bold text-warm-accent font-mono">¥{phone.price}</p>
        </div>
      </div>

      {/* Score bars */}
      <div className="space-y-1.5 mb-2.5">
        <ScoreBar label="游戏" score={phone.gaming_score} color="bg-warm-accent" />
        <ScoreBar label="拍照" score={phone.photo_score} color="bg-warm-teal" />
        <ScoreBar label="续航" score={phone.battery_score} color="bg-warm-green" />
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1 mb-2">
        {phone.tags.map((tag) => (
          <span
            key={tag}
            className="text-[10px] px-1.5 py-0.5 rounded bg-warm-accent-light/80 text-warm-amber font-mono"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Summary */}
      <p className="text-xs text-text-secondary leading-relaxed">{phone.summary}</p>

      {/* Specs row */}
      <div className="mt-2 pt-2 border-t border-warm-border grid grid-cols-3 gap-1 text-[10px] text-text-muted font-mono">
        <span>{phone.processor?.split(" ").pop()}</span>
        <span>{phone.battery}mAh</span>
        <span>{phone.weight}g</span>
      </div>
    </div>
  );
}

function ScoreBar({ label, score, color }: { label: string; score: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-[10px] text-text-muted w-6 flex-shrink-0">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-warm-border overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-300`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-[10px] text-text-muted font-mono w-6 text-right">{score}</span>
    </div>
  );
}
