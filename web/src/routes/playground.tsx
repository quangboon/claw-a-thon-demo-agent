import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Loader2, ArrowRight, Send } from "lucide-react";
import { api, getActiveProfileId, type TranslateResult } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { QcVerdict } from "@/components/qc-verdict";

const LANG_LABEL: Record<string, string> = { vi: "Tiếng Việt", th: "ภาษาไทย", en: "English" };

/** Wrap each `term` occurrence in a highlighted <mark> (used for ZH source + VI output). */
function highlight(text: string, terms: string[]) {
  if (!terms.length) return text;
  const escaped = terms.filter(Boolean).map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const parts = text.split(new RegExp(`(${escaped.join("|")})`, "gi"));
  const set = new Set(terms.map((t) => t.toLowerCase()));
  return parts.map((p, i) =>
    set.has(p.toLowerCase()) ? (
      <mark key={i} className="bg-primary/15 text-primary rounded px-0.5 font-medium">{p}</mark>
    ) : (
      <span key={i}>{p}</span>
    ),
  );
}

const SAMPLE = "灵石 +20%，开放传送阵。完成每日任务可领取仙缘礼包，突破境界获得额外修为。";

export function Playground() {
  const [source, setSource] = useState(SAMPLE);
  const [lang, setLang] = useState("vi");
  const profile = useQuery({ queryKey: ["profile", getActiveProfileId()], queryFn: () => api.getProfile(getActiveProfileId()) });
  const langs = profile.data?.target_langs ?? ["vi"];
  const m = useMutation<TranslateResult, Error, void>({ mutationFn: () => api.translate(source, lang) });
  const r = m.data;
  const zhTerms = r?.terms_required.map((t) => t.source) ?? [];
  const viTerms = r?.terms_required.map((t) => t.vi) ?? [];

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader><CardTitle>Văn bản nguồn (Trung)</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            value={source}
            onChange={(e) => setSource(e.target.value)}
            rows={6}
            className="font-mono"
            placeholder="Dán nội dung tiếng Trung…"
          />
          <div className="flex items-center gap-2">
            <Select value={langs.includes(lang) ? lang : langs[0]} onChange={(e) => setLang(e.target.value)} aria-label="Ngôn ngữ đích">
              {langs.map((l) => <option key={l} value={l}>{LANG_LABEL[l] ?? l}</option>)}
            </Select>
            <Button onClick={() => m.mutate()} disabled={m.isPending || !source.trim()}>
              {m.isPending ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
              Dịch + QC
            </Button>
          </div>
          {m.isError && <p className="text-sm text-danger">Lỗi: {m.error.message}</p>}
          {source && (
            <div className="text-sm leading-relaxed border-t border-line pt-3 font-mono whitespace-pre-wrap">
              {highlight(source, zhTerms)}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Bản dịch (Việt)</CardTitle>
          {r && <QcVerdict status={r.qc.status} />}
        </CardHeader>
        <CardContent className="space-y-3">
          {!r && !m.isPending && <p className="text-muted text-sm">Kết quả dịch + QC sẽ hiện ở đây.</p>}
          {m.isPending && <div className="flex items-center gap-2 text-muted text-sm"><Loader2 size={16} className="animate-spin" /> Đang dịch…</div>}
          {r && (
            <>
              <div className="text-sm leading-relaxed whitespace-pre-wrap">{highlight(r.output, viTerms)}</div>
              <div className="flex flex-wrap gap-2 text-xs">
                <Badge tone={r.decision === "auto_approved" ? "success" : "warning"}>
                  {r.decision === "auto_approved" ? "Tự duyệt" : "Cần người duyệt"}
                </Badge>
                <Badge tone="neutral">Số lần dịch: {r.attempts}</Badge>
                {r.qc.fluency_score != null && <Badge tone="primary">Trôi chảy: {r.qc.fluency_score}/5</Badge>}
              </div>
              {r.terms_required.length > 0 && (
                <div className="border-t border-line pt-3">
                  <p className="text-xs text-muted mb-1">Thuật ngữ bắt buộc</p>
                  <div className="flex flex-wrap gap-1 font-mono text-xs">
                    {r.terms_required.map((t) => (
                      <span key={t.source} className="rounded bg-bg border border-line px-1.5 py-0.5">
                        {t.source} → {t.vi}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {r.qc.issues.length > 0 && (
                <ul className="text-xs text-danger list-disc pl-4">
                  {r.qc.issues.map((i, idx) => <li key={idx}>[{i.axis}] {i.message}</li>)}
                </ul>
              )}
              {r.decision === "send_to_human" && (
                <p className="flex items-center gap-1 text-xs text-warning"><Send size={12} /> Đã đẩy vào hàng đợi duyệt.</p>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
