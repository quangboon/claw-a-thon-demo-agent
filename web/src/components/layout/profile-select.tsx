import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { api, getActiveProfileId, setActiveProfileId } from "@/lib/api";
import { Select } from "@/components/ui/select";

/** Topbar tenant switcher — sets X-Profile-Id for every subsequent request. */
export function ProfileSelect() {
  const qc = useQueryClient();
  const [active, setActive] = useState(getActiveProfileId());
  const profiles = useQuery({ queryKey: ["profiles"], queryFn: api.listProfiles });

  const onChange = (id: string) => {
    setActiveProfileId(id);
    setActive(id);
    qc.clear(); // drop cached data from the previous tenant → everything refetches
  };

  return (
    <div className="flex items-center gap-2">
      <Users size={16} className="text-muted" />
      <Select value={active} onChange={(e) => onChange(e.target.value)} aria-label="Hồ sơ (team)">
        {(profiles.data ?? [{ id: active, name: active }]).map((p) => (
          <option key={p.id} value={p.id}>{p.name || p.id}</option>
        ))}
      </Select>
    </div>
  );
}
