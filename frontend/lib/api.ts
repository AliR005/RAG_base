export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  context_window: number;
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  title: string | null;
  url: string | null;
  snippet: string | null;
}

export interface ChatMessage {
  id: string;
  role: string;
  content: string;
  model_used: string | null;
  sources: Citation[];
  created_at: string;
}

export interface Chat {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface DocumentInfo {
  id: string;
  source_type: string;
  origin: string;
  title: string | null;
  status: string;
  error: string | null;
  created_at: string;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function setToken(token: string) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (res.status === 401 && typeof window !== "undefined") {
    clearToken();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  register: (email: string, password: string) =>
    request<{ id: string; email: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<{ id: string; email: string }>("/auth/me"),
  models: () => request<ModelInfo[]>("/models"),
  chats: () => request<Chat[]>("/chats"),
  createChat: (title: string) =>
    request<Chat>("/chats", {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  renameChat: (id: string, title: string) =>
    request<Chat>(`/chats/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }),
  deleteChat: (id: string) =>
    request<void>(`/chats/${id}`, { method: "DELETE" }),
  messages: (chatId: string) =>
    request<ChatMessage[]>(`/chats/${chatId}/messages`),
  documents: () => request<DocumentInfo[]>("/documents"),
  createDocument: (url: string) =>
    request<DocumentInfo>("/documents", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),
  deleteDocument: (id: string) =>
    request<void>(`/documents/${id}`, { method: "DELETE" }),
};

export async function uploadDocument(file: File): Promise<DocumentInfo> {
  const token = getToken();
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/documents/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return (await res.json()) as DocumentInfo;
}
