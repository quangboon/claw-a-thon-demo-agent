// Typed client for the FastAPI backend (same origin — UI served by FastAPI).

export interface Term {
  source: string;
  vi: string;
  category?: string;
  note?: string;
  trust_score?: number;
  last_used?: string | null;
  status?: string;
  targets?: Record<string, string>;
}

export interface QcIssue { axis: string; message: string; severity: string; }

export interface TranslateResult {
  id: string;
  source: string;
  translation: string;
  output: string;
  decision: "auto_approved" | "send_to_human";
  target_lang: string;
  attempts: number;
  terms_required: { source: string; vi: string }[];
  qc: { status: string; fluency_score: number | null; issues: QcIssue[] };
}

export interface ReviewItem {
  id: string;
  source: string;
  translation: string;
  status: string;
  qc?: { status: string; issues: QcIssue[] };
  corrected?: string;
}

export interface Correction { source: string; wrong: string; right: string; note?: string; }

export interface Metrics {
  terms_total: number;
  terms_active: number;
  reviews_pending: number;
  corrections_total: number;
}

export interface AvoidEntry { term: string; category?: string; severity?: string; is_pattern?: boolean; }

export interface Profile {
  id: string;
  name: string;
  source_lang: string;
  target_langs: string[];
  char_name_convention?: string;
  tone_langs?: string[];
  avoid_counts?: Record<string, number>;
}

// --- active profile (multi-tenant scope) — persisted, sent as X-Profile-Id ---
const PROFILE_KEY = "activeProfileId";
let activeProfileId = localStorage.getItem(PROFILE_KEY) || "default";

export function getActiveProfileId(): string {
  return activeProfileId;
}
export function setActiveProfileId(id: string): void {
  activeProfileId = id;
  localStorage.setItem(PROFILE_KEY, id);
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", "X-Profile-Id": activeProfileId },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  translate: (source: string, target_lang = "vi") =>
    req<TranslateResult>("/translate", { method: "POST", body: JSON.stringify({ source, target_lang }) }),

  listTerms: (q = "", status?: string) => {
    const p = new URLSearchParams();
    if (q) p.set("q", q);
    if (status) p.set("status", status);
    const qs = p.toString();
    return req<Term[]>(`/terms${qs ? `?${qs}` : ""}`);
  },
  upsertTerm: (t: Term) => req<{ ok: boolean }>("/terms", { method: "POST", body: JSON.stringify(t) }),
  archiveTerm: (source: string) =>
    req<{ ok: boolean }>(`/terms/${encodeURIComponent(source)}`, { method: "DELETE" }),
  listCandidates: () => req<Term[]>("/terms/candidates"),
  approveCandidate: (t: Term) =>
    req<{ ok: boolean }>("/terms/candidates/approve", { method: "POST", body: JSON.stringify(t) }),

  pendingReviews: () => req<ReviewItem[]>("/review/pending"),
  approveReview: (id: string) => req<{ ok: boolean }>(`/review/${id}/approve`, { method: "POST" }),
  rejectReview: (id: string, corrected_text: string) =>
    req<{ ok: boolean }>(`/review/${id}/reject`, { method: "POST", body: JSON.stringify({ corrected_text }) }),

  listCorrections: () => req<Correction[]>("/corrections"),
  metrics: () => req<Metrics>("/metrics"),

  // --- profiles (Domain Packs) ---
  listProfiles: () => req<Profile[]>("/profiles"),
  getProfile: (id: string) => req<Profile>(`/profiles/${encodeURIComponent(id)}`),
  upsertProfile: (p: Partial<Profile> & { id: string }) =>
    req<{ ok: boolean }>("/profiles", { method: "POST", body: JSON.stringify(p) }),
  setTone: (id: string, lang: string, text: string) =>
    req<{ ok: boolean }>(`/profiles/${encodeURIComponent(id)}/tone/${lang}`, {
      method: "PUT", body: JSON.stringify({ text }),
    }),
  setAvoid: (id: string, lang: string, entries: AvoidEntry[]) =>
    req<{ ok: boolean }>(`/profiles/${encodeURIComponent(id)}/avoid/${lang}`, {
      method: "PUT", body: JSON.stringify({ entries }),
    }),
};
