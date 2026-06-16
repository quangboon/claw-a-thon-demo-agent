import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Save } from "lucide-react";
import { api, type AvoidEntry } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

/** Profile admin — create a team (Domain Pack) and edit its tone + need-to-avoid list. */
export function ProfileAdmin() {
  const qc = useQueryClient();
  const profiles = useQuery({ queryKey: ["profiles"], queryFn: api.listProfiles });
  const [selected, setSelected] = useState<string>("");

  const refreshProfiles = () => qc.invalidateQueries({ queryKey: ["profiles"] });

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <CreateProfile onCreated={(id) => { refreshProfiles(); setSelected(id); }} />
      <Card>
        <CardHeader><CardTitle>Chọn profile để sửa</CardTitle></CardHeader>
        <CardContent>
          <Select value={selected} onChange={(e) => setSelected(e.target.value)} className="w-full">
            <option value="">— chọn profile —</option>
            {(profiles.data ?? []).map((p) => <option key={p.id} value={p.id}>{p.name || p.id}</option>)}
          </Select>
        </CardContent>
      </Card>
      {selected && <ProfileEditor key={selected} profileId={selected} />}
    </div>
  );
}

function CreateProfile({ onCreated }: { onCreated: (id: string) => void }) {
  const [id, setId] = useState("");
  const [name, setName] = useState("");
  const [langs, setLangs] = useState("vi");
  const create = useMutation({
    mutationFn: () => api.upsertProfile({ id, name, target_langs: langs.split(",").map((s) => s.trim()).filter(Boolean) }),
    onSuccess: () => { onCreated(id); setId(""); setName(""); setLangs("vi"); },
  });
  return (
    <Card>
      <CardHeader><CardTitle>Tạo / cập nhật profile</CardTitle></CardHeader>
      <CardContent className="space-y-2">
        <Input value={id} onChange={(e) => setId(e.target.value)} placeholder="id (vd: game-c)" />
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Tên hiển thị" />
        <Input value={langs} onChange={(e) => setLangs(e.target.value)} placeholder="ngôn ngữ đích: vi,th,en" />
        <Button size="sm" onClick={() => create.mutate()} disabled={!id.trim() || create.isPending}>
          <Plus size={14} /> Lưu profile
        </Button>
        {create.isError && <p className="text-sm text-danger">{(create.error as Error).message}</p>}
      </CardContent>
    </Card>
  );
}

function ProfileEditor({ profileId }: { profileId: string }) {
  const detail = useQuery({ queryKey: ["profile", profileId], queryFn: () => api.getProfile(profileId) });
  const profile = detail.data;
  const langs = profile?.target_langs ?? ["vi"];
  const [lang, setLang] = useState(langs[0]);
  useEffect(() => { setLang((profile?.target_langs ?? ["vi"])[0]); }, [profile]);

  return (
    <Card className="lg:col-span-2">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Sửa tone & need-to-avoid · {profile?.name ?? profileId}</CardTitle>
        <Select value={lang} onChange={(e) => setLang(e.target.value)}>
          {langs.map((l) => <option key={l} value={l}>{l}</option>)}
        </Select>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">
        <ToneEditor profileId={profileId} lang={lang} />
        <AvoidEditor profileId={profileId} lang={lang} />
      </CardContent>
    </Card>
  );
}

function ToneEditor({ profileId, lang }: { profileId: string; lang: string }) {
  const [text, setText] = useState("");
  const save = useMutation({ mutationFn: () => api.setTone(profileId, lang, text) });
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Tone guide ({lang})</p>
      <Textarea value={text} onChange={(e) => setText(e.target.value)} rows={8}
                placeholder="Nhập văn phong cho ngôn ngữ này…" />
      <Button size="sm" onClick={() => save.mutate()} disabled={save.isPending}>
        <Save size={14} /> Lưu tone
      </Button>
      {save.isSuccess && <Badge tone="success">Đã lưu</Badge>}
    </div>
  );
}

function AvoidEditor({ profileId, lang }: { profileId: string; lang: string }) {
  const [rows, setRows] = useState<AvoidEntry[]>([{ term: "", category: "", severity: "warning" }]);
  const save = useMutation({ mutationFn: () => api.setAvoid(profileId, lang, rows.filter((r) => r.term.trim())) });
  const update = (i: number, patch: Partial<AvoidEntry>) =>
    setRows(rows.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Need-to-avoid ({lang})</p>
      {rows.map((r, i) => (
        <div key={i} className="flex gap-2">
          <Input value={r.term} onChange={(e) => update(i, { term: e.target.value })} placeholder="từ cấm" />
          <Select value={r.severity} onChange={(e) => update(i, { severity: e.target.value })}>
            <option value="warning">warning</option>
            <option value="error">error (block)</option>
          </Select>
        </div>
      ))}
      <div className="flex gap-2">
        <Button size="sm" variant="ghost" onClick={() => setRows([...rows, { term: "", category: "", severity: "warning" }])}>
          <Plus size={14} /> Thêm dòng
        </Button>
        <Button size="sm" onClick={() => save.mutate()} disabled={save.isPending}>
          <Save size={14} /> Lưu avoid
        </Button>
      </div>
      {save.isSuccess && <Badge tone="success">Đã lưu</Badge>}
    </div>
  );
}
