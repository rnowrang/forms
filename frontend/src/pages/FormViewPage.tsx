import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  ArrowLeft,
  FileText,
  Download,
  History,
  MessageSquare,
  Loader2,
  Send,
  CheckCircle,
  Clock,
  AlertCircle,
  Lock,
  Edit3,
  X,
} from 'lucide-react'
import { formsApi, templatesApi, versionsApi, reviewApi, auditApi, exportApi } from '../lib/api'
import { useAuthStore } from '../stores/authStore'
import type { FormVersion, ChangeEvent, CommentThread, FormStatus } from '../types'
import clsx from 'clsx'
import { format } from 'date-fns'

const statusConfig: Record<FormStatus, { label: string; icon: any; class: string }> = {
  draft: { label: 'Draft', icon: FileText, class: 'badge-draft' },
  in_review: { label: 'In Review', icon: Clock, class: 'badge-in-review' },
  needs_changes: { label: 'Needs Changes', icon: AlertCircle, class: 'badge-needs-changes' },
  approved: { label: 'Approved', icon: CheckCircle, class: 'badge-approved' },
  locked: { label: 'Locked', icon: Lock, class: 'badge-locked' },
}

export default function FormViewPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  
  const [activeTab, setActiveTab] = useState<'details' | 'versions' | 'audit' | 'comments'>('details')
  const [showCommentModal, setShowCommentModal] = useState(false)
  const [commentContent, setCommentContent] = useState('')
  const [commentFieldId, setCommentFieldId] = useState<string | undefined>()

  const isReviewer = user?.role === 'reviewer' || user?.role === 'admin'

  const { data: form, isLoading: formLoading } = useQuery({
    queryKey: ['form', id],
    queryFn: () => formsApi.get(Number(id)),
    enabled: !!id,
  })

  const { data: template } = useQuery({
    queryKey: ['template', form?.template_id],
    queryFn: () => templatesApi.get(form!.template_id),
    enabled: !!form?.template_id,
  })

  const { data: versions } = useQuery({
    queryKey: ['versions', id],
    queryFn: () => versionsApi.listForForm(Number(id)),
    enabled: !!id,
  })

  const { data: auditLog } = useQuery({
    queryKey: ['audit', id],
    queryFn: () => auditApi.getFormLog(Number(id)),
    enabled: !!id && activeTab === 'audit',
  })

  const { data: comments } = useQuery({
    queryKey: ['comments', id],
    queryFn: () => reviewApi.getComments(Number(id), true),
    enabled: !!id,
  })

  // Review actions
  const requestChangesMutation = useMutation({
    mutationFn: (notes: string) => reviewApi.requestChanges(Number(id), notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form', id] })
      toast.success('Changes requested')
    },
  })

  const approveMutation = useMutation({
    mutationFn: (notes?: string) => reviewApi.approve(Number(id), notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['form', id] })
      toast.success('Form approved')
    },
  })

  const addCommentMutation = useMutation({
    mutationFn: (data: { content: string; field_id?: string }) => 
      reviewApi.createComment(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', id] })
      setShowCommentModal(false)
      setCommentContent('')
      setCommentFieldId(undefined)
      toast.success('Comment added')
    },
  })

  const resolveThreadMutation = useMutation({
    mutationFn: (threadId: number) => reviewApi.resolveThread(threadId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comments', id] })
      toast.success('Thread resolved')
    },
  })

  const handleExport = async (format: 'docx' | 'pdf') => {
    try {
      toast.loading('Generating document...')
      const blob = format === 'docx' 
        ? await exportApi.downloadDocx(Number(id))
        : await exportApi.downloadPdf(Number(id))
      
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${form?.title || 'form'}.${format}`
      a.click()
      window.URL.revokeObjectURL(url)
      toast.dismiss()
      toast.success('Document downloaded')
    } catch {
      toast.dismiss()
      toast.error('Failed to generate document')
    }
  }

  if (formLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
      </div>
    )
  }

  if (!form) {
    return (
      <div className="text-center py-12">
        <p className="text-surface-500">Form not found</p>
      </div>
    )
  }

  const status = statusConfig[form.status as FormStatus]
  const openComments = comments?.filter((t: CommentThread) => !t.is_resolved) || []

  return (
    <div className="max-w-5xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 text-surface-500 hover:text-surface-700 hover:bg-surface-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold text-surface-900">{form.title}</h1>
              <span className={status.class}>{status.label}</span>
            </div>
            <p className="text-sm text-surface-500">
              {template?.name || 'Loading...'} • v{form.current_version_number}
              {form.owner_name && ` • ${form.owner_name}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {form.status === 'draft' && form.owner_id === user?.id && (
            <button
              onClick={() => navigate(`/forms/${id}/edit`)}
              className="btn-secondary"
            >
              <Edit3 className="w-4 h-4" />
              Edit
            </button>
          )}
          {form.status === 'needs_changes' && form.owner_id === user?.id && (
            <button
              onClick={() => navigate(`/forms/${id}/edit`)}
              className="btn-primary"
            >
              <Edit3 className="w-4 h-4" />
              Make Changes
            </button>
          )}
          <button onClick={() => handleExport('pdf')} className="btn-ghost">
            <Download className="w-4 h-4" />
            Export PDF
          </button>
          {isReviewer && form.status === 'in_review' && (
            <>
              <button
                onClick={() => {
                  const notes = prompt('Enter notes for changes requested:')
                  if (notes) requestChangesMutation.mutate(notes)
                }}
                className="btn-secondary"
              >
                Request Changes
              </button>
              <button
                onClick={() => approveMutation.mutate(undefined)}
                className="btn-success"
              >
                <CheckCircle className="w-4 h-4" />
                Approve
              </button>
            </>
          )}
        </div>
      </div>

      {/* Comment banner */}
      {openComments.length > 0 && (
        <div className="card p-4 mb-6 bg-amber-50 border-amber-200">
          <div className="flex items-center gap-3">
            <MessageSquare className="w-5 h-5 text-amber-600" />
            <p className="text-sm text-amber-800">
              <strong>{openComments.length}</strong> unresolved comment{openComments.length !== 1 ? 's' : ''} on this form
            </p>
            <button
              onClick={() => setActiveTab('comments')}
              className="ml-auto text-sm font-medium text-amber-700 hover:text-amber-800"
            >
              View Comments
            </button>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-surface-200 mb-6">
        <nav className="flex gap-6">
          {[
            { id: 'details', label: 'Details', icon: FileText },
            { id: 'versions', label: 'Versions', icon: History },
            { id: 'audit', label: 'Audit Log', icon: Clock },
            { id: 'comments', label: `Comments (${comments?.length || 0})`, icon: MessageSquare },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={clsx(
                'flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors',
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-surface-500 hover:text-surface-700'
              )}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === 'details' && (
        <div className="card">
          <div className="p-6 border-b border-surface-100">
            <h2 className="text-lg font-semibold text-surface-900">Form Data</h2>
          </div>
          <div className="p-6">
            {form.data && Object.keys(form.data).length > 0 ? (
              <dl className="space-y-4">
                {Object.entries(form.data).map(([key, value]) => {
                  if (key.startsWith('_')) return null
                  const field = template?.schema?.fields?.find((f: any) => f.id === key)
                  return (
                    <div key={key} className="grid grid-cols-3 gap-4">
                      <dt className="text-sm font-medium text-surface-500">
                        {field?.label || key}
                      </dt>
                      <dd className="col-span-2 text-sm text-surface-900">
                        {Array.isArray(value) ? value.join(', ') : String(value || '-')}
                      </dd>
                    </div>
                  )
                })}
              </dl>
            ) : (
              <p className="text-surface-500">No data entered yet</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'versions' && (
        <div className="card divide-y divide-surface-100">
          {versions?.map((version: FormVersion) => (
            <div key={version.id} className="p-4 flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-surface-100 flex items-center justify-center">
                <span className="text-sm font-semibold text-surface-600">v{version.version_number}</span>
              </div>
              <div className="flex-1">
                <p className="font-medium text-surface-900">
                  {version.version_label || `Version ${version.version_number}`}
                </p>
                <p className="text-sm text-surface-500">
                  {version.created_by_name} • {format(new Date(version.created_at), 'MMM d, yyyy h:mm a')}
                </p>
              </div>
              <span className={statusConfig[version.status_at_creation].class}>
                {statusConfig[version.status_at_creation].label}
              </span>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'audit' && (
        <div className="card divide-y divide-surface-100">
          {auditLog?.items?.map((event: ChangeEvent) => (
            <div key={event.id} className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-surface-900">
                    <span className="font-medium">{event.user_name}</span>
                    {event.action_type ? (
                      <span className="text-surface-500"> {event.action_details || event.action_type}</span>
                    ) : (
                      <span className="text-surface-500"> updated </span>
                    )}
                    {event.field_id !== '_system' && (
                      <span className="font-mono text-xs bg-surface-100 px-1 rounded">
                        {event.field_label || event.field_id}
                      </span>
                    )}
                  </p>
                  {event.field_id !== '_system' && event.old_value !== undefined && (
                    <p className="text-xs text-surface-500 mt-1">
                      Changed from "{String(event.old_value)}" to "{String(event.new_value)}"
                    </p>
                  )}
                </div>
                <span className="text-xs text-surface-400">
                  {format(new Date(event.timestamp), 'MMM d, h:mm a')}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'comments' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => setShowCommentModal(true)}
              className="btn-primary"
            >
              <MessageSquare className="w-4 h-4" />
              Add Comment
            </button>
          </div>
          
          {comments?.length === 0 ? (
            <div className="card p-8 text-center">
              <MessageSquare className="w-8 h-8 text-surface-300 mx-auto mb-2" />
              <p className="text-surface-500">No comments yet</p>
            </div>
          ) : (
            comments?.map((thread: CommentThread) => (
              <div key={thread.id} className={clsx('card', thread.is_resolved && 'opacity-60')}>
                <div className="p-4 border-b border-surface-100 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {thread.field_id && (
                      <span className="badge bg-surface-100 text-surface-600">
                        {thread.field_id}
                      </span>
                    )}
                    {thread.is_resolved ? (
                      <span className="badge bg-emerald-100 text-emerald-700">Resolved</span>
                    ) : (
                      <span className="badge bg-amber-100 text-amber-700">Open</span>
                    )}
                  </div>
                  {!thread.is_resolved && (
                    <button
                      onClick={() => resolveThreadMutation.mutate(thread.id)}
                      className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                    >
                      Resolve
                    </button>
                  )}
                </div>
                <div className="divide-y divide-surface-100">
                  {thread.comments.map((comment) => (
                    <div key={comment.id} className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-surface-900">
                          {comment.author_name}
                        </span>
                        <span className="text-xs text-surface-400">
                          {format(new Date(comment.created_at), 'MMM d, h:mm a')}
                        </span>
                      </div>
                      <p className="text-sm text-surface-600">{comment.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Comment Modal */}
      {showCommentModal && (
        <div className="fixed inset-0 bg-surface-900/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md animate-slide-up">
            <div className="p-6 border-b border-surface-100 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-surface-900">Add Comment</h3>
              <button
                onClick={() => setShowCommentModal(false)}
                className="text-surface-400 hover:text-surface-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="label">Field (optional)</label>
                <input
                  type="text"
                  value={commentFieldId || ''}
                  onChange={(e) => setCommentFieldId(e.target.value || undefined)}
                  className="input"
                  placeholder="e.g., study.title"
                />
              </div>
              <div>
                <label className="label">Comment</label>
                <textarea
                  value={commentContent}
                  onChange={(e) => setCommentContent(e.target.value)}
                  className="input resize-none"
                  rows={4}
                  placeholder="Enter your comment..."
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 p-6 border-t border-surface-100">
              <button onClick={() => setShowCommentModal(false)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={() => addCommentMutation.mutate({
                  content: commentContent,
                  field_id: commentFieldId,
                })}
                disabled={!commentContent.trim() || addCommentMutation.isPending}
                className="btn-primary"
              >
                {addCommentMutation.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
                Post Comment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
