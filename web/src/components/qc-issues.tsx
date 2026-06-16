import { AlertTriangle, XCircle } from "lucide-react";
import type { QcIssue } from "@/lib/api";

/** Human labels per QC axis (groups the flat issue list into named sections). */
const AXIS_LABEL: Record<string, string> = {
  completeness: "Đầy đủ",
  "term-compliance": "Thuật ngữ bắt buộc",
  fluency: "Trôi chảy",
  "need-to-avoid": "Từ cấm (need-to-avoid)",
  "term-confidence": "Độ tin cậy thuật ngữ",
  format: "Định dạng (placeholder/tag)",
};

const AXIS_ORDER = ["format", "need-to-avoid", "term-compliance", "completeness", "term-confidence", "fluency"];

/** Grouped, severity-coloured QC issues (error = red, warning = amber). */
export function QcIssues({ issues }: { issues: QcIssue[] }) {
  if (!issues.length) return null;
  const groups = new Map<string, QcIssue[]>();
  for (const i of issues) (groups.get(i.axis) ?? groups.set(i.axis, []).get(i.axis)!).push(i);
  const axes = [...groups.keys()].sort((a, b) => AXIS_ORDER.indexOf(a) - AXIS_ORDER.indexOf(b));

  return (
    <div className="space-y-2 border-t border-line pt-3">
      {axes.map((axis) => (
        <div key={axis}>
          <p className="text-xs font-medium text-muted mb-1">{AXIS_LABEL[axis] ?? axis}</p>
          <ul className="space-y-0.5">
            {groups.get(axis)!.map((i, idx) => {
              const err = i.severity === "error";
              const Icon = err ? XCircle : AlertTriangle;
              return (
                <li key={idx} className={`flex items-start gap-1.5 text-xs ${err ? "text-danger" : "text-warning"}`}>
                  <Icon size={13} className="mt-0.5 shrink-0" aria-hidden />
                  <span>{i.message}</span>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
