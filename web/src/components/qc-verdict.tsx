import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

const MAP: Record<string, { tone: "success" | "warning" | "danger"; icon: typeof CheckCircle2; label: string }> = {
  pass: { tone: "success", icon: CheckCircle2, label: "Đạt" },
  needs_review: { tone: "warning", icon: AlertTriangle, label: "Cần duyệt" },
  fail: { tone: "danger", icon: XCircle, label: "Không đạt" },
};

/** QC status badge — semantic colour + icon (not colour-only, for a11y). */
export function QcVerdict({ status }: { status: string }) {
  const v = MAP[status] ?? { tone: "neutral" as const, icon: AlertTriangle, label: status };
  const Icon = v.icon;
  return (
    <Badge tone={v.tone as never}>
      <Icon size={13} aria-hidden /> {v.label}
    </Badge>
  );
}
