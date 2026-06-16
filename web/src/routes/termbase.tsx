import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Archive, Check, Search } from "lucide-react";
import { api, type Term } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export function Termbase() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<"terms" | "candidates">("terms");
  const [q, setQ] = useState("");
  const [draft, setDraft] = useState<Term>({ source: "", vi: "", category: "" });

  const terms = useQuery({ queryKey: ["terms", q], queryFn: () => api.listTerms(q) });
  const candidates = useQuery({ queryKey: ["candidates"], queryFn: api.listCandidates, enabled: tab === "candidates" });
  const refresh = () => qc.invalidateQueries({ queryKey: ["terms"] });

  const add = useMutation({ mutationFn: api.upsertTerm, onSuccess: () => { refresh(); setDraft({ source: "", vi: "", category: "" }); } });
  const archive = useMutation({ mutationFn: api.archiveTerm, onSuccess: refresh });
  const approve = useMutation({
    mutationFn: api.approveCandidate,
    onSuccess: () => { refresh(); qc.invalidateQueries({ queryKey: ["candidates"] }); },
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Termbase Manager</CardTitle>
        <div className="flex gap-1 text-sm">
          <Button size="sm" variant={tab === "terms" ? "default" : "ghost"} onClick={() => setTab("terms")}>Thuật ngữ</Button>
          <Button size="sm" variant={tab === "candidates" ? "default" : "ghost"} onClick={() => setTab("candidates")}>Đề xuất</Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {tab === "terms" && (
          <>
            <div className="flex items-center gap-2">
              <Search size={16} className="text-muted" />
              <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm theo chữ Hán hoặc tiếng Việt…" className="max-w-xs" />
            </div>
            <div className="flex flex-wrap items-end gap-2 border border-line rounded-md p-3 bg-bg">
              <Input value={draft.source} onChange={(e) => setDraft({ ...draft, source: e.target.value })} placeholder="灵石" className="w-28 font-mono" />
              <Input value={draft.vi} onChange={(e) => setDraft({ ...draft, vi: e.target.value })} placeholder="Linh Thạch" className="w-40" />
              <Input value={draft.category} onChange={(e) => setDraft({ ...draft, category: e.target.value })} placeholder="category" className="w-32" />
              <Button size="sm" onClick={() => add.mutate(draft)} disabled={!draft.source || !draft.vi || add.isPending}>
                <Plus size={14} /> Thêm
              </Button>
            </div>
            <TermTable rows={terms.data ?? []} loading={terms.isLoading} onArchive={(s) => archive.mutate(s)} />
          </>
        )}
        {tab === "candidates" && (
          <TermTable
            rows={candidates.data ?? []}
            loading={candidates.isLoading}
            approve={(t) => approve.mutate(t)}
          />
        )}
      </CardContent>
    </Card>
  );
}

function TermTable({ rows, loading, onArchive, approve }: {
  rows: Term[]; loading: boolean;
  onArchive?: (source: string) => void; approve?: (t: Term) => void;
}) {
  if (loading) return <p className="text-muted text-sm">Đang tải…</p>;
  if (!rows.length) return <p className="text-muted text-sm">Chưa có dữ liệu.</p>;
  return (
    <div className="overflow-auto border border-line rounded-md">
      <table className="w-full text-sm">
        <thead className="bg-bg text-muted text-xs">
          <tr>
            <th className="text-left px-3 py-2 font-medium">Hán</th>
            <th className="text-left px-3 py-2 font-medium">Tiếng Việt</th>
            <th className="text-left px-3 py-2 font-medium">Loại</th>
            <th className="text-left px-3 py-2 font-medium">Trust</th>
            <th className="text-left px-3 py-2 font-medium">Trạng thái</th>
            <th className="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.source} className="border-t border-line hover:bg-bg">
              <td className="px-3 py-2 font-mono">{t.source}</td>
              <td className="px-3 py-2">{t.vi}</td>
              <td className="px-3 py-2 text-muted">{t.category}</td>
              <td className="px-3 py-2 font-mono tabular-nums">{(t.trust_score ?? 1).toFixed(1)}</td>
              <td className="px-3 py-2">
                <Badge tone={t.status === "archived" ? "neutral" : "success"}>{t.status ?? "active"}</Badge>
              </td>
              <td className="px-3 py-2 text-right">
                {approve && <Button size="sm" variant="success" onClick={() => approve(t)}><Check size={14} /> Duyệt</Button>}
                {onArchive && t.status !== "archived" && (
                  <Button size="sm" variant="ghost" onClick={() => onArchive(t.source)}><Archive size={14} /></Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
