import { useQuery } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { api } from "@/lib/api";
import { useProfile } from "@/lib/profile-context";
import { Select } from "@/components/ui/select";

/** Tenant switcher — sets X-Profile-Id for every subsequent request.
 * Shared via ProfileContext so the topbar and Playground selectors stay in sync. */
export function ProfileSelect({ label }: { label?: string }) {
  const { profileId, setProfileId } = useProfile();
  const profiles = useQuery({ queryKey: ["profiles"], queryFn: api.listProfiles });
  return (
    <div className="flex items-center gap-2">
      {label ? <span className="text-sm text-muted">{label}</span> : <Users size={16} className="text-muted" />}
      <Select value={profileId} onChange={(e) => setProfileId(e.target.value)} aria-label="Hồ sơ (team)">
        {(profiles.data ?? [{ id: profileId, name: profileId }]).map((p) => (
          <option key={p.id} value={p.id}>{p.name || p.id}</option>
        ))}
      </Select>
    </div>
  );
}
