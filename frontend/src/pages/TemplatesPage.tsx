import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  Plus,
  FileText,
  Upload,
  Loader2,
  MoreVertical,
  Eye,
  EyeOff,
  Settings,
  ChevronRight,
} from 'lucide-react'
import { templatesApi } from '../lib/api'
import { useAuthStore } from '../stores/authStore'
import type { Template } from '../types'
import clsx from 'clsx'

export default function TemplatesPage() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const isAdmin = user?.role === 'admin'
  
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploadName, setUploadName] = useState('')
  const [uploadDescription, setUploadDescription] = useState('')
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [activeMenu, setActiveMenu] = useState<number | null>(null)

  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => templatesApi.list(),
  })

  const uploadMutation = useMutation({
    mutationFn: async (data: FormData) => templatesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template uploaded successfully')
      setShowUploadModal(false)
      setUploadName('')
      setUploadDescription('')
      setUploadFile(null)
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to upload template')
    },
  })

  const publishMutation = useMutation({
    mutationFn: ({ id, publish }: { id: number; publish: boolean }) =>
      publish ? templatesApi.publish(id) : templatesApi.unpublish(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template updated')
    },
  })

  const handleUpload = () => {
    if (!uploadFile || !uploadName.trim()) {
      toast.error('Please provide a name and select a file')
      return
    }
    
    const formData = new FormData()
    formData.append('name', uploadName.trim())
    formData.append('description', uploadDescription.trim())
    formData.append('file', uploadFile)
    
    uploadMutation.mutate(formData)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploadFile(file)
      if (!uploadName) {
        setUploadName(file.name.replace(/\.[^/.]+$/, ''))
      }
    }
  }

  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-surface-900">Templates</h1>
          <p className="text-surface-500 mt-1">
            {isAdmin ? 'Manage IRB form templates' : 'Available IRB form templates'}
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowUploadModal(true)}
            className="btn-primary"
          >
            <Upload className="w-4 h-4" />
            Upload Template
          </button>
        )}
      </div>

      {/* Templates grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
        </div>
      ) : templates?.length === 0 ? (
        <div className="card flex flex-col items-center justify-center py-12 text-center">
          <div className="w-16 h-16 rounded-2xl bg-surface-100 flex items-center justify-center mb-4">
            <FileText className="w-8 h-8 text-surface-400" />
          </div>
          <h3 className="text-lg font-medium text-surface-900 mb-2">No templates yet</h3>
          <p className="text-surface-500 mb-6 max-w-sm">
            {isAdmin
              ? 'Upload your first IRB template to get started.'
              : 'No templates are available yet. Contact an administrator.'}
          </p>
          {isAdmin && (
            <button onClick={() => setShowUploadModal(true)} className="btn-primary">
              <Upload className="w-4 h-4" />
              Upload Template
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates?.map((template: Template) => (
            <div key={template.id} className="card-hover p-5 relative group">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-primary-600" />
                </div>
                {isAdmin && (
                  <div className="relative">
                    <button
                      onClick={() => setActiveMenu(activeMenu === template.id ? null : template.id)}
                      className="p-2 text-surface-400 hover:text-surface-600 rounded-lg hover:bg-surface-100"
                    >
                      <MoreVertical className="w-4 h-4" />
                    </button>
                    {activeMenu === template.id && (
                      <div className="absolute right-0 mt-1 w-48 bg-white border border-surface-200 rounded-xl shadow-lg z-10 py-1">
                        <button
                          onClick={() => {
                            publishMutation.mutate({ id: template.id, publish: !template.is_published })
                            setActiveMenu(null)
                          }}
                          className="flex items-center gap-2 w-full px-4 py-2 text-sm text-surface-600 hover:bg-surface-50"
                        >
                          {template.is_published ? (
                            <>
                              <EyeOff className="w-4 h-4" />
                              Unpublish
                            </>
                          ) : (
                            <>
                              <Eye className="w-4 h-4" />
                              Publish
                            </>
                          )}
                        </button>
                        <Link
                          to={`/templates/${template.id}`}
                          className="flex items-center gap-2 w-full px-4 py-2 text-sm text-surface-600 hover:bg-surface-50"
                          onClick={() => setActiveMenu(null)}
                        >
                          <Settings className="w-4 h-4" />
                          Configure Schema
                        </Link>
                      </div>
                    )}
                  </div>
                )}
              </div>
              
              <h3 className="font-medium text-surface-900 mb-1">{template.name}</h3>
              <p className="text-sm text-surface-500 line-clamp-2 mb-4">
                {template.description || 'No description provided'}
              </p>
              
              <div className="flex items-center justify-between pt-4 border-t border-surface-100">
                <div className="flex items-center gap-2">
                  <span className={clsx(
                    'badge',
                    template.is_published ? 'bg-emerald-100 text-emerald-700' : 'bg-surface-100 text-surface-600'
                  )}>
                    {template.is_published ? 'Published' : 'Draft'}
                  </span>
                  <span className="text-xs text-surface-400">v{template.version}</span>
                </div>
                <Link
                  to={`/templates/${template.id}`}
                  className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
                >
                  View
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-surface-900/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md animate-slide-up">
            <div className="p-6 border-b border-surface-100">
              <h3 className="text-lg font-semibold text-surface-900">Upload Template</h3>
              <p className="text-sm text-surface-500 mt-1">Upload a DOCX file to create a new template</p>
            </div>
            <div className="p-6 space-y-5">
              <div>
                <label className="label">Template Name</label>
                <input
                  type="text"
                  value={uploadName}
                  onChange={(e) => setUploadName(e.target.value)}
                  className="input"
                  placeholder="e.g., Minimal Risk Application"
                />
              </div>
              <div>
                <label className="label">Description (optional)</label>
                <textarea
                  value={uploadDescription}
                  onChange={(e) => setUploadDescription(e.target.value)}
                  className="input resize-none"
                  rows={3}
                  placeholder="Brief description of this template..."
                />
              </div>
              <div>
                <label className="label">Template File</label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".docx,.doc"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className={clsx(
                    'w-full p-4 border-2 border-dashed rounded-xl transition-colors',
                    uploadFile
                      ? 'border-primary-300 bg-primary-50'
                      : 'border-surface-200 hover:border-surface-300'
                  )}
                >
                  {uploadFile ? (
                    <div className="flex items-center gap-3">
                      <FileText className="w-6 h-6 text-primary-600" />
                      <div className="text-left">
                        <p className="text-sm font-medium text-surface-900">{uploadFile.name}</p>
                        <p className="text-xs text-surface-500">
                          {(uploadFile.size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center gap-2 text-surface-500">
                      <Upload className="w-6 h-6" />
                      <span className="text-sm">Click to select a DOCX file</span>
                    </div>
                  )}
                </button>
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 p-6 border-t border-surface-100">
              <button
                onClick={() => {
                  setShowUploadModal(false)
                  setUploadFile(null)
                  setUploadName('')
                  setUploadDescription('')
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleUpload}
                disabled={uploadMutation.isPending || !uploadFile}
                className="btn-primary"
              >
                {uploadMutation.isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  'Upload Template'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
