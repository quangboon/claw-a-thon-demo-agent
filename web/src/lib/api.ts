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

// --- auth (lightweight access gate) — bearer token persisted in localStorage ---
const TOKEN_KEY = "authToken";
let authToken = localStorage.getItem(TOKEN_KEY) || "";

export function getAuthToken(): string {
  return authToken;
}
export function setAuthToken(t: string): void {
  authToken = t;
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}
export function logout(): void {
  setAuthToken("");
  location.reload();
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Profile-Id": activeProfileId,
  };
  if (authToken) headers["Authorization"] = `Bearer ${authToken}`;
  const res = await fetch(path, { headers, ...init });
  if (res.status === 401) {
    setAuthToken(""); // stale/invalid token → force re-login
    location.reload();
    throw new Error("401 unauthorized");
  }
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  authStatus: () => req<{ auth_required: boolean }>("/auth/status"),
  // Raw fetch (not `req`) so a 401 surfaces "wrong credentials" instead of reloading.
  login: async (username: string, password: string): Promise<{ token: string }> => {
    const res = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (res.status === 401) throw new Error("Sai tài khoản hoặc mật khẩu");
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  },

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
  getTone: (id: string, lang: string) =>
    req<{ text: string }>(`/profiles/${encodeURIComponent(id)}/tone/${lang}`),
  getAvoid: (id: string, lang: string) =>
    req<AvoidEntry[]>(`/profiles/${encodeURIComponent(id)}/avoid/${lang}`),
  setTone: (id: string, lang: string, text: string) =>
    req<{ ok: boolean }>(`/profiles/${encodeURIComponent(id)}/tone/${lang}`, {
      method: "PUT", body: JSON.stringify({ text }),
    }),
  setAvoid: (id: string, lang: string, entries: AvoidEntry[]) =>
    req<{ ok: boolean }>(`/profiles/${encodeURIComponent(id)}/avoid/${lang}`, {
      method: "PUT", body: JSON.stringify({ entries }),
    }),
};
