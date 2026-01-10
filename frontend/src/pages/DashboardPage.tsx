import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  Plus,
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Lock,
  ChevronRight,
  Loader2,
  Trash2,
} from 'lucide-react'
import { formsApi, templatesApi } from '../lib/api'
import { useAuthStore } from '../stores/authStore'
import type { FormInstance, FormStatus } from '../types'
import clsx from 'clsx'

const statusConfig: Record<FormStatus, { label: string; icon: any; class: string }> = {
  draft: { label: 'Draft', icon: FileText, class: 'badge-draft' },
  in_review: { label: 'In Review', icon: Clock, class: 'badge-in-review' },
  needs_changes: { label: 'Needs Changes', icon: AlertCircle, class: 'badge-needs-changes' },
  approved: { label: 'Approved', icon: CheckCircle, class: 'badge-approved' },
  locked: { label: 'Locked', icon: Lock, class: 'badge-locked' },
}

export default function DashboardPage() {
  const { user, token } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showNewFormModal, setShowNewFormModal] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null)
  const [newFormTitle, setNewFormTitle] = useState('')

  const { data: forms, isLoading: formsLoading } = useQuery({
    queryKey: ['forms'],
    queryFn: () => formsApi.list(),
    enabled: !!token,
  })

  const { data: templates } = useQuery({
    queryKey: ['templates', 'published'],
    queryFn: () => templatesApi.listPublished(),
    enabled: !!token,
  })

  const createFormMutation = useMutation({
    mutationFn: (data: { template_id: number; title: string }) => formsApi.create(data),
    onSuccess: (form) => {
      queryClient.invalidateQueries({ queryKey: ['forms'] })
      toast.success('Form created successfully')
      setShowNewFormModal(false)
      navigate(`/forms/${form.id}/edit`)
    },
    onError: () => {
      toast.error('Failed to create form')
    },
  })

  const deleteFormMutation = useMutation({
    mutationFn: (id: number) => formsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forms'] })
      toast.success('Form deleted')
    },
    onError: () => {
      toast.error('Failed to delete form')
    },
  })

  const handleCreateForm = () => {
    if (!selectedTemplate || !newFormTitle.trim()) {
      toast.error('Please select a template and enter a title')
      return
    }
    createFormMutation.mutate({
      template_id: selectedTemplate,
      title: newFormTitle.trim(),
    })
  }

  const handleDeleteForm = (e: React.MouseEvent, id: number) => {
    e.preventDefault()
    e.stopPropagation()
    if (confirm('Are you sure you want to delete this draft?')) {
      deleteFormMutation.mutate(id)
    }
  }

  const stats = {
    total: forms?.length || 0,
    drafts: forms?.filter((f: FormInstance) => f.status === 'draft').length || 0,
    inReview: forms?.filter((f: FormInstance) => f.status === 'in_review').length || 0,
    approved: forms?.filter((f: FormInstance) => f.status === 'approved').length || 0,
  }

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-surface-900">
            Welcome back, {user?.full_name?.split(' ')[0]}
          </h1>
          <p className="text-surface-500 mt-1">Here's an overview of your IRB applications</p>
        </div>
        <button
          onClick={() => setShowNewFormModal(true)}
          className="btn-primary"
        >
          <Plus className="w-4 h-4" />
          New Application
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-surface-100 flex items-center justify-center">
              <FileText className="w-6 h-6 text-surface-600" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-surface-900">{stats.total}</p>
              <p className="text-sm text-surface-500">Total Forms</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center">
              <Clock className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-surface-900">{stats.drafts}</p>
              <p className="text-sm text-surface-500">Drafts</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-surface-900">{stats.inReview}</p>
              <p className="text-sm text-surface-500">In Review</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-surface-900">{stats.approved}</p>
              <p className="text-sm text-surface-500">Approved</p>
            </div>
          </div>
        </div>
      </div>

      {/* Forms list */}
      <div className="card">
        <div className="p-5 border-b border-surface-100">
          <h2 className="text-lg font-semibold text-surface-900">Your Applications</h2>
        </div>
        
        {formsLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
          </div>
        ) : forms?.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-16 h-16 rounded-2xl bg-surface-100 flex items-center justify-center mb-4">
              <FileText className="w-8 h-8 text-surface-400" />
            </div>
            <h3 className="text-lg font-medium text-surface-900 mb-2">No applications yet</h3>
            <p className="text-surface-500 mb-6 max-w-sm">
              Get started by creating your first IRB application from a template.
            </p>
            <button onClick={() => setShowNewFormModal(true)} className="btn-primary">
              <Plus className="w-4 h-4" />
              Create Application
            </button>
          </div>
        ) : (
          <div className="divide-y divide-surface-100">
            {forms?.map((form: FormInstance) => {
              const status = statusConfig[form.status]
              return (
                <Link
                  key={form.id}
                  to={form.status === 'draft' ? `/forms/${form.id}/edit` : `/forms/${form.id}`}
                  className="flex items-center gap-4 p-5 hover:bg-surface-50 transition-colors group"
                >
                  <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center">
                    <status.icon className="w-5 h-5 text-primary-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-surface-900 truncate">{form.title}</p>
                    <p className="text-sm text-surface-500 truncate">
                      {form.template_name} • v{form.current_version_number}
                    </p>
                  </div>
                  <span className={status.class}>{status.label}</span>
                  <span className="text-xs text-surface-400">
                    {new Date(form.updated_at || form.created_at).toLocaleDateString()}
                  </span>
                  {form.status === 'draft' && (
                    <button
                      onClick={(e) => handleDeleteForm(e, form.id)}
                      className="opacity-0 group-hover:opacity-100 p-2 text-surface-400 hover:text-accent-rose transition-all"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                  <ChevronRight className="w-5 h-5 text-surface-300 group-hover:text-surface-400 transition-colors" />
                </Link>
              )
            })}
          </div>
        )}
      </div>

      {/* New Form Modal */}
      {showNewFormModal && (
        <div className="fixed inset-0 bg-surface-900/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md animate-slide-up">
            <div className="p-6 border-b border-surface-100">
              <h3 className="text-lg font-semibold text-surface-900">New Application</h3>
              <p className="text-sm text-surface-500 mt-1">Select a template and enter a title</p>
            </div>
            <div className="p-6 space-y-5">
              <div>
                <label className="label">Template</label>
                <select
                  value={selectedTemplate || ''}
                  onChange={(e) => setSelectedTemplate(Number(e.target.value))}
                  className="input"
                >
                  <option value="">Select a template...</option>
                  {templates?.map((t: any) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Application Title</label>
                <input
                  type="text"
                  value={newFormTitle}
                  onChange={(e) => setNewFormTitle(e.target.value)}
                  className="input"
                  placeholder="e.g., Study on Sleep Patterns"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 p-6 border-t border-surface-100">
              <button
                onClick={() => setShowNewFormModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateForm}
                disabled={createFormMutation.isPending}
                className="btn-primary"
              >
                {createFormMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Application'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
