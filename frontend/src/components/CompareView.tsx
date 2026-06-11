import type { Phone } from "../types";

interface Props {
  phones: Phone[];
}

export default function CompareView({ phones }: Props) {
  if (phones.length < 2) return null;
  const displayPhones = phones.slice(0, 3);

  const rows = [
    { label: "价格", key: "price", format: (v: number) => `¥${v}` },
    { label: "处理器", key: "processor" },
    { label: "内存/存储", key: "ram_storage", get: (p: Phone) => `${p.ram}G/${p.storage}G` },
    { label: "电池", key: "battery", format: (v: number) => `${v}mAh` },
    { label: "充电", key: "charging_speed", format: (v: number) => `${v}W` },
    { label: "重量", key: "weight", format: (v: number) => `${v}g` },
    { label: "游戏", key: "gaming_score", format: (v: number) => `${v}/100` },
    { label: "拍照", key: "photo_score", format: (v: number) => `${v}/100` },
    { label: "续航", key: "battery_score", format: (v: number) => `${v}/100` },
  ];

  return (
    <div>
      <h3 className="text-sm font-bold text-warm-teal mb-3 font-mono flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-warm-teal" />
        机型对比
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr>
              <th className="text-left text-text-muted px-2 py-1.5 border-b border-warm-border"></th>
              {displayPhones.map((p) => (
                <th
                  key={p.id}
                  className="text-center text-warm-teal px-2 py-1.5 border-b border-warm-border font-semibold"
                >
                  {p.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <td className="text-text-muted px-2 py-1.5 border-b border-warm-border/50">
                  {row.label}
                </td>
                {displayPhones.map((p) => {
                  let value: any;
                  if (row.get) {
                    value = row.get(p);
                  } else {
                    value = (p as any)[row.key];
                    if (row.format) value = row.format(value);
                  }
                  return (
                    <td
                      key={p.id}
                      className="text-center text-text-primary px-2 py-1.5 border-b border-warm-border/50"
                    >
                      {value}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
