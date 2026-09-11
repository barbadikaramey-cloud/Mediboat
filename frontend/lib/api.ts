/**
 * API client — typed fetch wrappers for the MediBot FastAPI backend.
 * All requests include the JWT bearer token from localStorage.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface Source {
  id?: string
  document: string
  section: string
  collection: string
  score?: number
  page_number?: number | null
  chunk_type?: string
  text?: string
}

export interface ChatResponse {
  answer: string
  sources: Source[]
  retrieval_type: 'document_rag' | 'sql_rag' | 'blocked'
  role: string
  is_cached?: boolean
}

export interface CollectionsResponse {
  role: string
  collections: string[]
}

// ── Auth ─────────────────────────────────────────────────────────────────────
export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? 'Invalid credentials')
  }
  return res.json()
}

// ── Chat ─────────────────────────────────────────────────────────────────────
export interface HistoryMessage {
  role: 'user' | 'assistant'
  content: string
}

export async function chat(
  question: string,
  token: string,
  history: HistoryMessage[] = [],
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question, history }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? 'Chat request failed')
  }
  return res.json()
}

// ── Collections ───────────────────────────────────────────────────────────────
export async function getCollections(
  role: string,
  token: string,
): Promise<CollectionsResponse> {
  const res = await fetch(`${API_URL}/collections/${role}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error('Failed to fetch collections')
  return res.json()
}

// ── Token helpers ─────────────────────────────────────────────────────────────
export function saveToken(token: string, role: string, username: string) {
  localStorage.setItem('medibot_token', token)
  localStorage.setItem('medibot_role', role)
  localStorage.setItem('medibot_username', username)
}

export function loadToken(): { token: string; role: string; username: string } | null {
  if (typeof window === 'undefined') return null
  const token = localStorage.getItem('medibot_token')
  const role = localStorage.getItem('medibot_role')
  const username = localStorage.getItem('medibot_username')
  if (!token || !role || !username) return null
  return { token, role, username }
}

export function clearToken() {
  localStorage.removeItem('medibot_token')
  localStorage.removeItem('medibot_role')
  localStorage.removeItem('medibot_username')
}

// ── Role metadata ─────────────────────────────────────────────────────────────
export const ROLE_META: Record<string, { label: string; color: string; collections: string[] }> = {
  doctor:            { label: 'Doctor',            color: 'blue',   collections: ['clinical', 'nursing', 'general'] },
  nurse:             { label: 'Nurse',              color: 'green',  collections: ['nursing', 'general'] },
  billing_executive: { label: 'Billing Executive',  color: 'orange', collections: ['billing', 'general'] },
  technician:        { label: 'Technician',         color: 'purple', collections: ['equipment', 'general'] },
  admin:             { label: 'Admin',              color: 'red',    collections: ['clinical', 'nursing', 'billing', 'equipment', 'general'] },
}

export const DEMO_ACCOUNTS = [
  { username: 'dr.mehta',     password: 'doctor',            role: 'doctor',            label: 'Dr. Mehta (Doctor)' },
  { username: 'nurse.priya',  password: 'nurse',             role: 'nurse',             label: 'Nurse Priya (Nurse)' },
  { username: 'billing.ravi', password: 'billing_executive', role: 'billing_executive', label: 'Ravi (Billing Executive)' },
  { username: 'tech.anand',   password: 'technician',        role: 'technician',        label: 'Anand (Technician)' },
  { username: 'admin.sys',    password: 'admin',             role: 'admin',             label: 'Admin (All Access)' },
]
