import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Corrections() {
  const { data, isLoading } = useQuery({ queryKey: ["corrections"], queryFn: api.listCorrections });
  return (
    <Card>
      <CardHeader><CardTitle>Corrections / Flywheel</CardTitle></CardHeader>
      <CardContent>
        {isLoading ? (
          <p className="text-muted text-sm">Đang tải…</p>
        ) : !data?.length ? (
          <p className="text-muted text-sm">Chưa có correction nào. Reject một bản dịch ở Review Queue để hệ học.</p>
        ) : (
          <div className="overflow-auto border border-line rounded-md">
            <table className="w-full text-sm">
              <thead className="bg-bg text-muted text-xs">
                <tr>
                  <th className="text-left px-3 py-2 font-medium">Nguồn (ZH)</th>
                  <th className="text-left px-3 py-2 font-medium text-danger">Sai</th>
                  <th className="text-left px-3 py-2 font-medium text-success">Đúng</th>
                  <th className="text-left px-3 py-2 font-medium">Ghi chú</th>
                </tr>
              </thead>
              <tbody>
                {data.map((c, i) => (
                  <tr key={i} className="border-t border-line hover:bg-bg align-top">
                    <td className="px-3 py-2 font-mono">{c.source}</td>
                    <td className="px-3 py-2 text-danger/80 line-through">{c.wrong}</td>
                    <td className="px-3 py-2 text-success">{c.right}</td>
                    <td className="px-3 py-2 text-muted text-xs">{c.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
