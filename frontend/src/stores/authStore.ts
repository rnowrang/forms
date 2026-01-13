import { create } from 'zustand'

export interface User {
  id: number
  email: string
  full_name: string
  role: 'admin' | 'researcher' | 'reviewer'
  is_active: boolean
  created_at: string
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  _hasHydrated: boolean
  setAuth: (token: string, user: User) => void
  logout: () => void
}

// Load initial state from localStorage
const getInitialState = () => {
  try {
    const stored = localStorage.getItem('irb-auth')
    if (stored) {
      const data = JSON.parse(stored)
      return {
        token: data.token || null,
        user: data.user || null,
        isAuthenticated: !!data.token,
      }
    }
  } catch (e) {
    // Ignore parse errors
  }
  return { token: null, user: null, isAuthenticated: false }
}

const initialState = getInitialState()

export const useAuthStore = create<AuthState>()((set) => ({
  token: initialState.token,
  user: initialState.user,
  isAuthenticated: initialState.isAuthenticated,
  _hasHydrated: true, // Already hydrated synchronously
  setAuth: (token, user) => {
    // Save to localStorage immediately
    localStorage.setItem('irb-auth', JSON.stringify({ token, user }))
    set({ token, user, isAuthenticated: true })
  },
  logout: () => {
    localStorage.removeItem('irb-auth')
    set({ token: null, user: null, isAuthenticated: false })
  },
}))
