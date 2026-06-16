import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Lock, Loader2 } from "lucide-react";
import { api, setAuthToken } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/** Access gate — username/password (from server env) → bearer token. */
export function Login({ onSuccess }: { onSuccess: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const m = useMutation({
    mutationFn: () => api.login(username, password),
    onSuccess: (data) => { setAuthToken(data.token); onSuccess(); },
  });

  const submit = (e: React.FormEvent) => { e.preventDefault(); if (username && password) m.mutate(); };

  return (
    <div className="flex h-full items-center justify-center bg-bg">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock size={18} className="text-primary" /> Đăng nhập
          </CardTitle>
          <p className="text-sm text-muted">Nền tảng dịch thuật đa team · Termbase + QC</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-3">
            <Input value={username} onChange={(e) => setUsername(e.target.value)}
                   placeholder="Tài khoản" autoFocus autoComplete="username" />
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                   placeholder="Mật khẩu" autoComplete="current-password" />
            <Button type="submit" className="w-full" disabled={m.isPending || !username || !password}>
              {m.isPending ? <Loader2 size={16} className="animate-spin" /> : <Lock size={16} />}
              Đăng nhập
            </Button>
            {m.isError && <p className="text-sm text-danger">{(m.error as Error).message}</p>}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
