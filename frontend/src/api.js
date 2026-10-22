const KEY = "docintel.token";

export const getToken = () => {
  try { return localStorage.getItem(KEY); } catch { return null; }
};
export const setToken = (t) => {
  try { t ? localStorage.setItem(KEY, t) : localStorage.removeItem(KEY); } catch { /* storage bloqueado */ }
};

let onUnauthorized = () => {};
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn; };

async function request(path, opts = {}) {
  const token = getToken();
  const headers = { ...opts.headers, ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  const res = await fetch(path, { ...opts, headers });
  const body = await res.json().catch(() => ({}));
  if (res.status === 401 && !path.startsWith("/auth/login")) onUnauthorized();
  if (!res.ok) throw new Error(body.detail || `Erro ${res.status}`);
  return body;
}

export const getHealth = () => request("/health");
export const getAuthStatus = () => request("/auth/status");
export const getMe = () => request("/auth/me");
export const login = (email, password) =>
  request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
export const getDocuments = () => request("/documents");
export const deleteDocument = (name) =>
  request(`/documents/${encodeURIComponent(name)}`, { method: "DELETE" });
export const uploadDocument = (file) => {
  const fd = new FormData();
  fd.append("file", file);
  return request("/documents", { method: "POST", body: fd });
};
export const ask = (question, topK) =>
  request("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  });
