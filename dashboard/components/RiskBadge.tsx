import type { RiskAssessment } from "@/lib/types";

const LEVEL_STYLES: Record<RiskAssessment["risk_level"], string> = {
  HEALTHY:   "bg-emerald-100 text-emerald-800 border-emerald-300",
  GREY_ZONE: "bg-amber-100  text-amber-800  border-amber-300",
  CRITICAL:  "bg-red-100    text-red-800    border-red-300",
};

const LEVEL_LABELS: Record<RiskAssessment["risk_level"], string> = {
  HEALTHY:   "Healthy",
  GREY_ZONE: "Grey Zone",
  CRITICAL:  "Critical",
};

interface Props {
  level: RiskAssessment["risk_level"];
  className?: string;
}

export function RiskBadge({ level, className = "" }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${LEVEL_STYLES[level]} ${className}`}
    >
      {LEVEL_LABELS[level]}
    </span>
  );
}
