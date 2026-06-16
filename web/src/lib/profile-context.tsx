import { createContext, useContext, useState, type ReactNode } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { getActiveProfileId, setActiveProfileId } from "@/lib/api";

/** Active profile (tenant) shared across topbar + playground so both stay in sync.
 * The module-level value in api.ts remains the source of truth for the X-Profile-Id
 * header; this context mirrors it as React state and clears caches on change. */
interface ProfileCtx {
  profileId: string;
  setProfileId: (id: string) => void;
}

const Ctx = createContext<ProfileCtx>({ profileId: "default", setProfileId: () => {} });

export function ProfileProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const [profileId, setId] = useState(getActiveProfileId());
  const setProfileId = (id: string) => {
    setActiveProfileId(id); // updates the header source of truth + localStorage
    setId(id);
    qc.clear(); // drop cached data from the previous tenant → everything refetches
  };
  return <Ctx.Provider value={{ profileId, setProfileId }}>{children}</Ctx.Provider>;
}

export function useProfile(): ProfileCtx {
  return useContext(Ctx);
}
