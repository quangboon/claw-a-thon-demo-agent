import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, X, Inbox } from "lucide-react";
import { api, type ReviewItem } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { QcIssues } from "@/components/qc-issues";

export function Review() {
  const qc = useQueryClient();
  const pending = useQuery({ queryKey: ["review"], queryFn: api.pendingReviews });
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["review"] });
    qc.invalidateQueries({ queryKey: ["corrections"] });
    qc.invalidateQueries({ queryKey: ["metrics"] });
  };
  const approve = useMutation({ mutationFn: api.approveReview, onSuccess: invalidate });
  const reject = useMutation({
    mutationFn: ({ id, text }: { id: string; text: string }) => api.rejectReview(id, text),
    onSuccess: invalidate,
  });

  if (pending.isLoading) return <p className="text-muted text-sm">Đang tải…</p>;
  const items = pending.data ?? [];
  if (!items.length)
    return (
      <Card><CardContent className="flex flex-col items-center gap-2 py-10 text-muted">
        <Inbox size={32} /> <p>Không có bản dịch nào chờ duyệt.</p>
      </CardContent></Card>
    );

  return (
    <div className="space-y-3">
      {items.map((it) => (
        <ReviewCard key={it.id} item={it} onApprove={() => approve.mutate(it.id)}
          onReject={(text) => reject.mutate({ id: it.id, text })} busy={approve.isPending || reject.isPending} />
      ))}
    </div>
  );
}

function ReviewCard({ item, onApprove, onReject, busy }: {
  item: ReviewItem; onApprove: () => void; onReject: (text: string) => void; busy: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(item.translation);
  return (
    <Card>
      <CardHeader><CardTitle className="font-mono text-sm">{item.source}</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm"><span className="text-muted text-xs">Bản dịch ứng viên:</span><br />{item.translation}</div>
        {item.qc?.issues?.length ? <QcIssues issues={item.qc.issues} /> : null}
        {editing ? (
          <div className="space-y-2">
            <Textarea value={text} onChange={(e) => setText(e.target.value)} rows={3} />
            <div className="flex gap-2">
              <Button size="sm" variant="danger" onClick={() => onReject(text)} disabled={busy}>Lưu sửa (Reject)</Button>
              <Button size="sm" variant="ghost" onClick={() => setEditing(false)}>Huỷ</Button>
            </div>
          </div>
        ) : (
          <div className="flex gap-2">
            <Button size="sm" variant="success" onClick={onApprove} disabled={busy}><Check size={14} /> Duyệt</Button>
            <Button size="sm" variant="outline" onClick={() => setEditing(true)}><X size={14} /> Sửa lại</Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
