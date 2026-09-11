'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { chat, clearToken, loadToken, ROLE_META, type ChatResponse, type Source } from '@/lib/api'
import MarkdownRenderer from '@/components/MarkdownRenderer'
import SourcesViewer from '@/components/SourcesViewer'
import { 
  Activity, 
  Send, 
  LogOut, 
  Database, 
  FileText, 
  ShieldAlert, 
  Sparkles, 
  Clock, 
  ChevronRight,
  ShieldCheck,
  User as UserIcon,
  RefreshCw,
  Zap
} from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  retrieval_type?: string
  blocked?: boolean
  is_cached?: boolean
  timestamp: Date
}

const RETRIEVAL_CONFIG: Record<string, { label: string; icon: React.ComponentType<{ className?: string }>; color: string }> = {
  document_rag: {
    label: 'Document RAG (Hybrid Retrieval)',
    icon: FileText,
    color: 'bg-rose-50 text-rose-700 border-rose-200',
  },
  sql_rag: {
    label: 'SQL RAG (Analytical Query)',
    icon: Database,
    color: 'bg-indigo-50 text-indigo-700 border-indigo-200',
  },
  blocked: {
    label: 'Security Filter Blocked',
    icon: ShieldAlert,
    color: 'bg-amber-50 text-amber-700 border-amber-200',
  },
}

const COLLECTION_BADGES: Record<string, string> = {
  clinical:  'bg-rose-50 text-rose-700 border-rose-200',
  nursing:   'bg-teal-50 text-teal-700 border-teal-200',
  billing:   'bg-amber-50 text-amber-700 border-amber-200',
  equipment: 'bg-purple-50 text-purple-700 border-purple-200',
  general:   'bg-slate-100 text-slate-700 border-slate-200',
}

const ROLE_SUGGESTIONS: Record<string, string[]> = {
  doctor: [
    'What is the recommended antibiotic treatment for pneumonia?',
    'What is the clinical protocol for acute STEMI?',
    'What is the drug dosage guidelines for vancomycin?',
  ],
  nurse: [
    'What are the ICU nursing procedures for ventilated patients?',
    'What is the infection control protocol for MRSA?',
    'What is the staff leave policy for shift workers?',
  ],
  billing_executive: [
    'What is total claims in last month?',
    'How many claims have an escalated status?',
    'What is the average claimed amount by department?',
  ],
  technician: [
    'What is the top maintenance category by ticket count?',
    'How many open maintenance tickets are there for each equipment type?',
    'What are the calibration requirements for monitoring equipment?',
  ],
  admin: [
    'What is total claims in last month?',
    'How many claims have an escalated status?',
    'What is the top maintenance category by ticket count?',
    'What is the protocol for STEMI?',
  ],
}

export default function ChatPage() {
  const router = useRouter()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [auth, setAuth] = useState<{ token: string; role: string; username: string } | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const stored = loadToken()
    if (!stored) {
      router.replace('/login')
      return
    }
    setAuth(stored)
  }, [router])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(textToSend?: string) {
    const query = (textToSend ?? input).trim()
    if (!query || !auth || loading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    }

    // Build history from previous messages
    const historyPayload = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }))

    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res: ChatResponse = await chat(query, auth.token, historyPayload)

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.answer,
        sources: res.sources,
        retrieval_type: res.retrieval_type,
        blocked: res.retrieval_type === 'blocked',
        is_cached: res.is_cached,
        timestamp: new Date(),
      }
      setMessages((m) => [...m, assistantMsg])
    } catch (e: unknown) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: e instanceof Error ? e.message : 'An error occurred. Please verify backend connection.',
        blocked: true,
        timestamp: new Date(),
      }
      setMessages((m) => [...m, errorMsg])
    } finally {
      setLoading(false)
    }
  }

  function handleLogout() {
    clearToken()
    router.replace('/login')
  }

  if (!auth) return null

  const meta = ROLE_META[auth.role]
  const suggestions = ROLE_SUGGESTIONS[auth.role] ?? ROLE_SUGGESTIONS.admin

  return (
    <div className="flex flex-col h-screen bg-slate-50/70 antialiased">
      {/* Top Header */}
      <header className="sticky top-0 z-20 backdrop-blur-md bg-white/95 border-b border-slate-200/80 px-4 sm:px-6 py-3 flex items-center justify-between shadow-2xs">
        {/* Left: Brand & Status */}
        <div className="flex items-center gap-3.5">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-500 to-pink-600 text-white shadow-md shadow-rose-500/20 ring-2 ring-rose-500/10">
            <Activity className="w-5 h-5 text-white stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-extrabold text-slate-900 text-base tracking-tight leading-tight">
                Medi<span className="text-rose-600">Bot</span>
              </h1>
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-50 text-rose-700 border border-rose-200">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
                Active
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">MediAssist Health Network</p>
          </div>
        </div>

        {/* Right: User Profile & Role Badges */}
        <div className="flex items-center gap-3 sm:gap-4">
          {/* User Badge */}
          <div className="flex items-center gap-2.5 bg-rose-50/40 border border-rose-100 rounded-xl px-3 py-1.5">
            <div className="w-7 h-7 rounded-lg bg-rose-500 text-white flex items-center justify-center font-bold text-xs shadow-2xs">
              {auth.username.charAt(0).toUpperCase()}
            </div>
            <div className="flex flex-col text-left">
              <span className="text-xs font-bold text-slate-900 leading-tight">{auth.username}</span>
              <span className="text-[11px] font-semibold text-rose-600">{meta?.label ?? auth.role}</span>
            </div>
          </div>

          {/* Authorized Collections Pills */}
          <div className="hidden md:flex items-center gap-1.5">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-1">
              Authorized:
            </span>
            {meta?.collections.map((c) => (
              <span
                key={c}
                className={`text-[11px] px-2 py-0.5 rounded-lg font-bold border ${
                  COLLECTION_BADGES[c] ?? 'bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                {c}
              </span>
            ))}
          </div>

          {/* Sign Out */}
          <button
            onClick={handleLogout}
            title="Sign out of current terminal"
            className="flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-rose-700 hover:bg-rose-50 border border-slate-200/80 hover:border-rose-200 rounded-xl px-3 py-2 transition-all cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Sign Out</span>
          </button>
        </div>
      </header>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Empty / Welcome Hero */}
          {messages.length === 0 && (
            <div className="text-center py-10 sm:py-16 animate-fadeIn">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-3xl bg-gradient-to-tr from-rose-500 to-pink-600 text-white shadow-xl shadow-rose-500/20 mb-4 ring-8 ring-rose-50">
                <Sparkles className="w-8 h-8 text-white stroke-[2.2]" />
              </div>
              <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                Welcome back, {auth.username}
              </h2>
              <p className="text-sm text-slate-500 font-medium max-w-md mx-auto mt-2 leading-relaxed">
                MediBot is ready. You have access to <strong className="text-slate-800 font-bold">{meta?.collections.join(', ')}</strong> knowledge bases with server-side RBAC protection.
              </p>

              {/* Suggestion Chips Grid */}
              <div className="mt-8 max-w-xl mx-auto text-left">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 text-center">
                  Recommended queries for your role:
                </p>
                <div className="grid grid-cols-1 gap-2.5">
                  {suggestions.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(s)}
                      className="w-full text-left p-3.5 rounded-2xl bg-white border border-slate-200/80 hover:border-rose-300 hover:shadow-md hover:shadow-rose-500/5 transition-all flex items-center justify-between group cursor-pointer"
                    >
                      <span className="text-sm font-semibold text-slate-700 group-hover:text-rose-700">
                        {s}
                      </span>
                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-rose-500 group-hover:translate-x-0.5 transition-all shrink-0 ml-2" />
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Message List */}
          {messages.map((msg) => {
            const isUser = msg.role === 'user'
            const badgeConfig = msg.retrieval_type ? RETRIEVAL_CONFIG[msg.retrieval_type] : null

            return (
              <div
                key={msg.id}
                className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'} animate-fadeIn`}
              >
                {/* Bot Avatar */}
                {!isUser && (
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-rose-500 to-pink-600 text-white flex items-center justify-center shrink-0 shadow-md shadow-rose-500/20 mt-1">
                    <Activity className="w-5 h-5 stroke-[2.5]" />
                  </div>
                )}

                <div className={`max-w-2xl w-full ${isUser ? 'items-end' : 'items-start'}`}>
                  {/* Bubble Container */}
                  <div
                    className={`rounded-2xl p-4.5 sm:p-5 shadow-xs transition-all ${
                      isUser
                        ? 'bg-gradient-to-r from-rose-500 to-pink-600 text-white rounded-tr-xs shadow-md shadow-rose-500/15'
                        : msg.blocked
                        ? 'bg-amber-50/80 border border-amber-200/90 text-amber-950 rounded-tl-xs'
                        : 'bg-white border border-slate-200/90 text-slate-900 rounded-tl-xs'
                    }`}
                  >
                    {isUser ? (
                      <p className="text-sm font-medium leading-relaxed whitespace-pre-wrap">
                        {msg.content}
                      </p>
                    ) : (
                      <MarkdownRenderer content={msg.content} />
                    )}
                  </div>

                  {/* Metadata Bar */}
                  {!isUser && (
                    <div className="mt-2 flex items-center gap-2.5 flex-wrap pl-1">
                      {badgeConfig && (
                        <span
                          className={`inline-flex items-center gap-1.5 text-[11px] font-bold px-2.5 py-0.5 rounded-lg border ${badgeConfig.color}`}
                        >
                          <badgeConfig.icon className="w-3 h-3" />
                          {badgeConfig.label}
                        </span>
                      )}
                      {msg.is_cached && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-lg border bg-emerald-50 text-emerald-700 border-emerald-200">
                          <Zap className="w-3 h-3 text-emerald-600 fill-emerald-600/30" />
                          Cached (Redis)
                        </span>
                      )}
                      <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  )}

                  {/* Collapsible Reranked Sources & Citations Viewer */}
                  {!isUser && msg.sources && msg.sources.length > 0 && (
                    <SourcesViewer sources={msg.sources} />
                  )}
                </div>

                {/* User Avatar */}
                {isUser && (
                  <div className="w-9 h-9 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0 shadow-sm mt-1 font-bold text-xs">
                    <UserIcon className="w-4 h-4" />
                  </div>
                )}
              </div>
            )
          })}

          {/* Loading Indicator */}
          {loading && (
            <div className="flex gap-3.5 justify-start animate-fadeIn">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-rose-500 to-pink-600 text-white flex items-center justify-center shrink-0 shadow-md shadow-rose-500/20">
                <Activity className="w-5 h-5 stroke-[2.5]" />
              </div>
              <div className="bg-white border border-slate-200/90 rounded-2xl rounded-tl-xs px-5 py-4 shadow-2xs flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-rose-500 animate-bounce [animation-delay:0ms]" />
                  <div className="w-2 h-2 rounded-full bg-rose-500 animate-bounce [animation-delay:150ms]" />
                  <div className="w-2 h-2 rounded-full bg-rose-500 animate-bounce [animation-delay:300ms]" />
                </div>
                <span className="text-xs font-bold text-slate-600">
                  Retrieving & Synthesizing Answer…
                </span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Floating Input Bar */}
      <div className="sticky bottom-0 bg-white/95 backdrop-blur-md border-t border-slate-200/80 px-4 sm:px-6 py-3.5 shadow-lg shadow-slate-900/5">
        <div className="max-w-4xl mx-auto space-y-2">
          {/* Quick Query Chips for ongoing session */}
          {messages.length > 0 && (
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider shrink-0 mr-1">
                Quick:
              </span>
              {suggestions.slice(0, 3).map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => sendMessage(s)}
                  className="text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-rose-50 hover:text-rose-700 hover:border-rose-200 border border-slate-200/70 rounded-lg px-2.5 py-1 whitespace-nowrap transition-colors cursor-pointer shrink-0"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Main Input Box */}
          <div className="flex items-end gap-2 bg-slate-50 border border-slate-200/90 focus-within:border-rose-400 focus-within:bg-white focus-within:ring-2 focus-within:ring-rose-400/20 rounded-2xl p-1.5 transition-all">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  sendMessage()
                }
              }}
              placeholder={`Ask a question (e.g. clinical protocol, claims analysis, equipment status)...`}
              rows={1}
              className="flex-1 bg-transparent border-0 px-3.5 py-2 text-sm text-slate-900 font-medium placeholder-slate-400 resize-none focus:outline-none max-h-32 leading-relaxed"
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className="bg-gradient-to-r from-rose-500 to-pink-600 hover:from-rose-600 hover:to-pink-700 disabled:opacity-40 text-white rounded-xl px-4 py-2.5 text-sm font-bold shadow-md shadow-rose-500/20 transition-all shrink-0 flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
            >
              <span>Send</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium px-1">
            <span>Press <kbd className="font-bold text-slate-500 bg-slate-100 px-1 py-0.5 rounded border border-slate-200">Enter</kbd> to send, <kbd className="font-bold text-slate-500 bg-slate-100 px-1 py-0.5 rounded border border-slate-200">Shift+Enter</kbd> for new line</span>
            <span className="flex items-center gap-1 font-semibold text-slate-500">
              <ShieldCheck className="w-3 h-3 text-emerald-600" />
              RBAC Filtered
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
