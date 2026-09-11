'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { login, saveToken, DEMO_ACCOUNTS, ROLE_META } from '@/lib/api'
import { 
  ShieldCheck, 
  Lock, 
  User, 
  Eye, 
  EyeOff, 
  Activity, 
  ChevronDown, 
  Sparkles, 
  ArrowRight,
  KeyRound
} from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showDemoAccordion, setShowDemoAccordion] = useState(false)

  async function handleLogin(u: string, p: string) {
    if (!u.trim() || !p.trim()) {
      setError('Please enter your staff ID and password.')
      return
    }

    setLoading(true)
    setError('')
    try {
      const res = await login(u.trim(), p)
      const payload = JSON.parse(atob(res.access_token.split('.')[1]))
      const role: string = payload.role
      saveToken(res.access_token, role, u.trim())
      router.push('/chat')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Invalid credentials. Please verify your staff ID and password.')
    } finally {
      setLoading(false)
    }
  }

  function selectDemoAccount(acc: typeof DEMO_ACCOUNTS[0]) {
    setUsername(acc.username)
    setPassword(acc.password)
    setError('')
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-rose-50/70 via-slate-50 to-pink-50/40 flex flex-col items-center justify-center p-4 sm:p-6 relative overflow-hidden">
      {/* Ambient background glow in gentle rose/pink */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-rose-200/40 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-pink-200/35 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center p-3.5 rounded-2xl bg-gradient-to-tr from-rose-500 to-pink-600 text-white shadow-xl shadow-rose-500/20 mb-3.5 ring-4 ring-rose-100">
            <Activity className="w-8 h-8 text-white stroke-[2.5]" />
          </div>
          <div className="flex items-center justify-center gap-2">
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Medi<span className="text-rose-600">Bot</span>
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold tracking-wide uppercase bg-rose-100 text-rose-700 border border-rose-200">
              Enterprise
            </span>
          </div>
          <p className="text-slate-600 font-medium text-sm mt-1.5">
            MediAssist Health Network Clinical Knowledge Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white/95 backdrop-blur-xl rounded-3xl shadow-xl shadow-slate-300/40 border border-slate-200/80 p-8 sm:p-9">
          <div className="mb-6">
            <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">Staff Sign In</h2>
            <p className="text-xs text-slate-500 font-medium mt-1">
              Enter your network credentials to access authorized clinical collections.
            </p>
          </div>

          {error && (
            <div className="mb-5 p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs font-semibold flex items-start gap-2.5">
              <span className="text-red-500 text-sm font-bold">⚠️</span>
              <span className="leading-relaxed">{error}</span>
            </div>
          )}

          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleLogin(username, password)
            }}
            className="space-y-4"
          >
            {/* Username */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Staff ID / Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. dr.mehta"
                  autoComplete="username"
                  className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 font-medium focus:outline-none focus:bg-white focus:ring-2 focus:ring-rose-400 focus:border-rose-300 transition-all"
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  className="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 font-medium focus:outline-none focus:bg-white focus:ring-2 focus:ring-rose-400 focus:border-rose-300 transition-all"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me & Need Access */}
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  defaultChecked
                  className="w-4 h-4 text-rose-600 border-slate-300 rounded focus:ring-rose-400 cursor-pointer accent-rose-600"
                />
                <span className="text-xs font-medium text-slate-600">Remember workstation</span>
              </label>
              <span className="text-[11px] font-semibold text-rose-600 cursor-pointer hover:underline">
                Need access?
              </span>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 bg-gradient-to-r from-rose-500 to-pink-600 hover:from-rose-600 hover:to-pink-700 active:scale-[0.99] disabled:opacity-50 text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-rose-500/25 transition-all text-sm flex items-center justify-center gap-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Verifying Credentials…</span>
                </>
              ) : (
                <>
                  <span>Sign In to Clinical Workspace</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Discreet Developer / Demo Credentials Selector */}
          <div className="mt-6 pt-5 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setShowDemoAccordion(!showDemoAccordion)}
              className="w-full flex items-center justify-between text-xs font-bold text-slate-500 hover:text-slate-800 transition-colors py-1 group cursor-pointer"
            >
              <span className="flex items-center gap-1.5 text-slate-500 group-hover:text-rose-700 font-semibold">
                <Sparkles className="w-3.5 h-3.5 text-rose-500" />
                Test Role Quick-Select
              </span>
              <span className="flex items-center gap-1 text-[11px] text-slate-400 font-medium">
                {showDemoAccordion ? 'Hide' : 'Show'}
                <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${showDemoAccordion ? 'rotate-180' : ''}`} />
              </span>
            </button>

            {showDemoAccordion && (
              <div className="mt-3 bg-rose-50/40 border border-rose-100 rounded-2xl p-3 space-y-1.5 animate-fadeIn">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-2 px-1">
                  Click to pre-fill credentials:
                </p>
                <div className="grid grid-cols-1 gap-1.5">
                  {DEMO_ACCOUNTS.map((acc) => {
                    const isSelected = username === acc.username
                    return (
                      <button
                        key={acc.username}
                        type="button"
                        onClick={() => selectDemoAccount(acc)}
                        className={`text-left px-3 py-2 rounded-xl transition-all flex items-center justify-between border cursor-pointer ${
                          isSelected 
                            ? 'bg-rose-100/80 border-rose-300 shadow-2xs' 
                            : 'bg-white border-slate-200/60 hover:border-rose-200 hover:bg-rose-50/50'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${
                            acc.role === 'admin' ? 'bg-red-500' :
                            acc.role === 'doctor' ? 'bg-rose-500' :
                            acc.role === 'nurse' ? 'bg-teal-500' :
                            acc.role === 'billing_executive' ? 'bg-amber-500' : 'bg-purple-500'
                          }`} />
                          <span className="text-xs font-bold text-slate-800">{acc.label}</span>
                        </div>
                        <span className="text-[10px] font-semibold text-slate-400 font-mono">
                          {acc.username}
                        </span>
                      </button>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Security Badges */}
        <div className="flex items-center justify-center gap-4 text-slate-500 text-xs mt-6 font-medium">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-rose-500" />
            <span>Role-Based Access Control</span>
          </div>
          <span>•</span>
          <div className="flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5 text-pink-500" />
            <span>Encrypted Token Auth</span>
          </div>
        </div>
      </div>
    </main>
  )
}
