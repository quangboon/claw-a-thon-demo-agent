// Mirrors backend format_preservation.py — used to VISUALISE which placeholders/tags
// are missing (in source, absent from draft) or extra (added in draft). Display-only;
// the backend QC rule is the source of truth for pass/fail.

const PATTERNS = [
  /\{[^{}]*\}/g, // {0} {name} {0:F2}
  /<[^<>]+>/g, // <b> </b> <color=#fff>
  /\[[^[\]]+\]/g, // [player_name] [HP]
  /%(?:\d+\$)?[-+ #0]*\d*(?:\.\d+)?[a-zA-Z@]/g, // %s %d %1$s %.2f
  /\\[a-zA-Z]+\[\d+\]/g, // \c[3] \n[1] \v[10]
];
const CN_BRACKETS = "【】《》「」『』";

function counts(text: string, extra: string[] = []): Map<string, number> {
  const m = new Map<string, number>();
  const add = (t: string) => m.set(t, (m.get(t) ?? 0) + 1);
  for (const re of PATTERNS) for (const hit of text.matchAll(re)) add(hit[0]);
  for (const ch of CN_BRACKETS) { const n = text.split(ch).length - 1; if (n) m.set(ch, n); }
  for (const tok of extra) if (tok) { const n = text.split(tok).length - 1; if (n) m.set(tok, n); }
  return m;
}

export interface TokenDiff { token: string; status: "ok" | "missing" | "extra"; }

/** Compare source vs draft token multisets → per-token status (for chips). */
export function diffTokens(source: string, draft: string, extra: string[] = []): TokenDiff[] {
  const s = counts(source, extra), d = counts(draft, extra);
  const all = new Set([...s.keys(), ...d.keys()]);
  const out: TokenDiff[] = [];
  for (const tok of all) {
    const sc = s.get(tok) ?? 0, dc = d.get(tok) ?? 0;
    if (sc === dc) out.push({ token: tok, status: "ok" });
    else if (sc > dc) out.push({ token: tok, status: "missing" });
    else out.push({ token: tok, status: "extra" });
  }
  return out;
}

export function hasFormatTokens(source: string, extra: string[] = []): boolean {
  return counts(source, extra).size > 0;
}
