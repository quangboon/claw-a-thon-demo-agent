import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { BookText, CheckCircle2, Inbox, History } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Dashboard() {
  const { data, isLoading } = useQuery({ queryKey: ["metrics"], queryFn: api.metrics });

  const cards = [
    { label: "Tổng thuật ngữ", value: data?.terms_total, icon: BookText, tone: "text-primary" },
    { label: "Đang dùng", value: data?.terms_active, icon: CheckCircle2, tone: "text-success" },
    { label: "Chờ duyệt", value: data?.reviews_pending, icon: Inbox, tone: "text-warning" },
    { label: "Corrections", value: data?.corrections_total, icon: History, tone: "text-accent" },
  ];
  const chart = [
    { name: "Thuật ngữ", value: data?.terms_active ?? 0 },
    { name: "Chờ duyệt", value: data?.reviews_pending ?? 0 },
    { name: "Corrections", value: data?.corrections_total ?? 0 },
  ];

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <Card key={c.label}>
              <CardContent className="flex items-center gap-3 py-4">
                <Icon className={c.tone} size={28} />
                <div>
                  <div className="text-2xl font-semibold tabular-nums">{isLoading ? "…" : c.value ?? 0}</div>
                  <div className="text-xs text-muted">{c.label}</div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      <Card>
        <CardHeader><CardTitle>Tổng quan hệ thống</CardTitle></CardHeader>
        <CardContent style={{ height: 280 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#2563EB" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
