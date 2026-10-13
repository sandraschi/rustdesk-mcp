// Fleet standard: same-origin relative by default (vite proxy forwards /api to
// the backend), absolute only inside the Tauri WebView where same-origin has
// no http backend to proxy through.
const inTauri =
  typeof window !== "undefined" &&
  ("__TAURI__" in window || "__TAURI_INTERNALS__" in window);
export const API_BASE = inTauri ? "http://127.0.0.1:10805" : "";
