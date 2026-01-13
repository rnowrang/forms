import axios from 'axios'
import { useAuthStore } from '../stores/authStore'

const API_URL = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  // Try zustand state first, then localStorage
  let token = useAuthStore.getState().token
  if (!token) {
    try {
      const stored = localStorage.getItem('irb-auth')
      if (stored) {
        const parsed = JSON.parse(stored)
        token = parsed?.token || null
      }
    } catch (e) {
      // Ignore parse errors
    }
  }
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log 401 errors for debugging but don't auto-logout
    // (auto-logout was causing redirect loops)
    if (error.response?.status === 401) {
      console.warn('[API] 401 Unauthorized:', error.config?.url)
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login/json', { email, password })
    return response.data
  },
  register: async (data: { email: string; password: string; full_name: string }) => {
    const response = await api.post('/auth/register', data)
    return response.data
  },
  me: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

// Templates API
export const templatesApi = {
  list: async () => {
    const response = await api.get('/templates')
    return response.data
  },
  listPublished: async () => {
    const response = await api.get('/templates/published')
    return response.data
  },
  get: async (id: number) => {
    const response = await api.get(`/templates/${id}`)
    return response.data
  },
  create: async (data: FormData) => {
    const response = await api.post('/templates', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },
  update: async (id: number, data: any) => {
    const response = await api.put(`/templates/${id}`, data)
    return response.data
  },
  publish: async (id: number) => {
    const response = await api.post(`/templates/${id}/publish`)
    return response.data
  },
  unpublish: async (id: number) => {
    const response = await api.post(`/templates/${id}/unpublish`)
    return response.data
  },
}

// Forms API
export const formsApi = {
  list: async (allForms = false) => {
    const response = await api.get('/forms', { params: { all_forms: allForms } })
    return response.data
  },
  get: async (id: number) => {
    const response = await api.get(`/forms/${id}`)
    return response.data
  },
  create: async (data: { template_id: number; title: string }) => {
    const response = await api.post('/forms', data)
    return response.data
  },
  updateData: async (id: number, changes: any[]) => {
    const response = await api.post(`/forms/${id}/data`, { changes })
    return response.data
  },
  getData: async (id: number) => {
    const response = await api.get(`/forms/${id}/data`)
    return response.data
  },
  delete: async (id: number) => {
    const response = await api.delete(`/forms/${id}`)
    return response.data
  },
}

// Versions API
export const versionsApi = {
  listForForm: async (formId: number) => {
    const response = await api.get(`/versions/form/${formId}`)
    return response.data
  },
  get: async (id: number) => {
    const response = await api.get(`/versions/${id}`)
    return response.data
  },
  create: async (formId: number, label?: string) => {
    const response = await api.post(`/versions/form/${formId}`, { version_label: label })
    return response.data
  },
}

// Audit API
export const auditApi = {
  getFormLog: async (formId: number, page = 1, pageSize = 50) => {
    const response = await api.get(`/audit/form/${formId}`, {
      params: { page, page_size: pageSize },
    })
    return response.data
  },
  getFieldHistory: async (formId: number, fieldId: string) => {
    const response = await api.get(`/audit/form/${formId}/field/${fieldId}`)
    return response.data
  },
  getSummary: async (formId: number) => {
    const response = await api.get(`/audit/form/${formId}/summary`)
    return response.data
  },
  getDiff: async (formId: number, fromVersionId: number, toVersionId: number) => {
    const response = await api.get(`/audit/form/${formId}/diff`, {
      params: { from_version_id: fromVersionId, to_version_id: toVersionId },
    })
    return response.data
  },
}

// Review API
export const reviewApi = {
  submitForReview: async (formId: number, notes?: string) => {
    const response = await api.post(`/review/form/${formId}/submit`, null, {
      params: { notes },
    })
    return response.data
  },
  requestChanges: async (formId: number, notes?: string) => {
    const response = await api.post(`/review/form/${formId}/request-changes`, {
      action_type: 'request_changes',
      notes,
    })
    return response.data
  },
  approve: async (formId: number, notes?: string) => {
    const response = await api.post(`/review/form/${formId}/approve`, {
      action_type: 'approve',
      notes,
    })
    return response.data
  },
  returnToDraft: async (formId: number, notes?: string) => {
    const response = await api.post(`/review/form/${formId}/return-to-draft`, null, {
      params: { notes },
    })
    return response.data
  },
  getComments: async (formId: number, includeResolved = false) => {
    const response = await api.get(`/review/form/${formId}/comments`, {
      params: { include_resolved: includeResolved },
    })
    return response.data
  },
  createComment: async (formId: number, data: {
    content: string
    field_id?: string
    section_id?: string
    thread_id?: number
  }) => {
    const response = await api.post(`/review/form/${formId}/comments`, data)
    return response.data
  },
  resolveThread: async (threadId: number) => {
    const response = await api.post(`/review/threads/${threadId}/resolve`)
    return response.data
  },
  getHistory: async (formId: number) => {
    const response = await api.get(`/review/form/${formId}/history`)
    return response.data
  },
}

// Export API
export const exportApi = {
  generate: async (formId: number, versionId?: number) => {
    const response = await api.post(`/export/form/${formId}/generate`, null, {
      params: { version_id: versionId },
    })
    return response.data
  },
  downloadDocx: async (formId: number, versionId?: number) => {
    const response = await api.get(`/export/form/${formId}/docx`, {
      params: { version_id: versionId },
      responseType: 'blob',
    })
    return response.data
  },
  downloadPdf: async (formId: number, versionId?: number) => {
    const response = await api.get(`/export/form/${formId}/pdf`, {
      params: { version_id: versionId },
      responseType: 'blob',
    })
    return response.data
  },
}
