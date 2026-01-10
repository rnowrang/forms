import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Clock,
  AlertCircle,
  CheckCircle,
  ChevronRight,
  Loader2,
  FileText,
  User,
} from 'lucide-react'
import { formsApi } from '../lib/api'
import { useAuthStore } from '../stores/authStore'
import type { FormInstance, FormStatus } from '../types'
import clsx from 'clsx'
import { format } from 'date-fns'

const statusConfig: Record<FormStatus, { label: string; icon: any; class: string }> = {
  draft: { label: 'Draft', icon: FileText, class: 'badge-draft' },
  in_review: { label: 'In Review', icon: Clock, class: 'badge-in-review' },
  needs_changes: { label: 'Needs Changes', icon: AlertCircle, class: 'badge-needs-changes' },
  approved: { label: 'Approved', icon: CheckCircle, class: 'badge-approved' },
  locked: { label: 'Locked', icon: FileText, class: 'badge-locked' },
}

export default function ReviewPage() {
  const { user } = useAuthStore()
  
  const { data: forms, isLoading } = useQuery({
    queryKey: ['forms', 'all'],
    queryFn: () => formsApi.list(true),
  })

  const pendingReview = forms?.filter((f: FormInstance) => f.status === 'in_review') || []
  const needsChanges = forms?.filter((f: FormInstance) => f.status === 'needs_changes') || []
  const recentlyApproved = forms?.filter((f: FormInstance) => f.status === 'approved').slice(0, 5) || []

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-surface-900">Review Queue</h1>
        <p className="text-surface-500 mt-1">Manage and review submitted IRB applications</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center">
              <Clock className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-surface-900">{pendingReview.length}</p>
              <p className="text-sm text-surface-500">Pending Review</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-rose-50 flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-rose-600" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-surface-900">{needsChanges.length}</p>
              <p className="text-sm text-surface-500">Needs Changes</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-semibold text-surface-900">{recentlyApproved.length}</p>
              <p className="text-sm text-surface-500">Recently Approved</p>
            </div>
          </div>
        </div>
      </div>

      {/* Pending Review */}
      <div className="card mb-8">
        <div className="p-5 border-b border-surface-100 flex items-center gap-3">
          <Clock className="w-5 h-5 text-amber-600" />
          <h2 className="text-lg font-semibold text-surface-900">Pending Review</h2>
          <span className="badge bg-amber-100 text-amber-700">{pendingReview.length}</span>
        </div>
        {pendingReview.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-surface-500">No forms pending review</p>
          </div>
        ) : (
          <div className="divide-y divide-surface-100">
            {pendingReview.map((form: FormInstance) => (
              <FormListItem key={form.id} form={form} />
            ))}
          </div>
        )}
      </div>

      {/* Needs Changes */}
      {needsChanges.length > 0 && (
        <div className="card mb-8">
          <div className="p-5 border-b border-surface-100 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-600" />
            <h2 className="text-lg font-semibold text-surface-900">Awaiting Changes</h2>
            <span className="badge bg-rose-100 text-rose-700">{needsChanges.length}</span>
          </div>
          <div className="divide-y divide-surface-100">
            {needsChanges.map((form: FormInstance) => (
              <FormListItem key={form.id} form={form} />
            ))}
          </div>
        </div>
      )}

      {/* Recently Approved */}
      {recentlyApproved.length > 0 && (
        <div className="card">
          <div className="p-5 border-b border-surface-100 flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-600" />
            <h2 className="text-lg font-semibold text-surface-900">Recently Approved</h2>
          </div>
          <div className="divide-y divide-surface-100">
            {recentlyApproved.map((form: FormInstance) => (
              <FormListItem key={form.id} form={form} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function FormListItem({ form }: { form: FormInstance }) {
  const status = statusConfig[form.status]
  
  return (
    <Link
      to={`/forms/${form.id}`}
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
      <div className="flex items-center gap-2 text-sm text-surface-500">
        <User className="w-4 h-4" />
        {form.owner_name}
      </div>
      <span className={status.class}>{status.label}</span>
      <span className="text-xs text-surface-400">
        {form.submitted_at
          ? format(new Date(form.submitted_at), 'MMM d, yyyy')
          : format(new Date(form.updated_at || form.created_at), 'MMM d, yyyy')}
      </span>
      <ChevronRight className="w-5 h-5 text-surface-300 group-hover:text-surface-400 transition-colors" />
    </Link>
  )
}
