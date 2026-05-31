export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  avatar_url?: string | null;
  is_verified: boolean;
  auth_provider: string;
  tier: string;
  storage_used_bytes: number;
  created_at: string;
}

export interface Topic {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  document_count: number;
  size_bytes: number;
}

export interface Document {
  id: string;
  topic_id?: string | null;
  title: string;
  file_type: string;
  source_type: string;
  source_url?: string | null;
  size_bytes: number;
  cloudinary_url?: string | null;
  status: string;
  page_count?: number | null;
  error?: string | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title?: string | null;
  topic_id?: string | null;
  created_at: string;
}

export interface Citation {
  index: number;
  document_id: string;
  document_title?: string | null;
  page?: number | null;
  url?: string | null;
  snippet: string;
}

export interface Message {
  id: string;
  role: string;
  content: string;
  citations?: Citation[] | null;
  charts?: ChartSpec[] | null;
  tools?: string[] | null;
  created_at: string;
}

export interface Usage {
  used_bytes: number;
  quota_bytes: number;
  quota_mb: number;
  percent: number;
}

export interface ChartSpec {
  type: "bar" | "line" | "area" | "pie";
  title?: string;
  x?: string;
  series?: { key: string; name?: string }[];
  nameKey?: string;
  valueKey?: string;
  data: Record<string, string | number>[];
}

export type StreamEvent =
  | { type: "evidence"; count: number }
  | { type: "thinking"; token: string }
  | { type: "token"; token: string }
  | { type: "citations"; citations: Citation[] }
  | { type: "chart"; chart: ChartSpec }
  | { type: "tools"; tools: string[] }
  | { type: "done" };
