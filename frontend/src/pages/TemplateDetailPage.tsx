import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import {
  ArrowLeft,
  FileText,
  Loader2,
  Eye,
  EyeOff,
  ChevronDown,
  ChevronRight,
  GripVertical,
} from 'lucide-react'
import { templatesApi } from '../lib/api'
import { useAuthStore } from '../stores/authStore'
import type { TemplateSchemaSection, TemplateSchemaField } from '../types'
import { useState } from 'react'
import clsx from 'clsx'

export default function TemplateDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const isAdmin = user?.role === 'admin'
  
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())

  const { data: template, isLoading } = useQuery({
    queryKey: ['template', id],
    queryFn: () => templatesApi.get(Number(id)),
    enabled: !!id,
  })

  const publishMutation = useMutation({
    mutationFn: (publish: boolean) =>
      publish ? templatesApi.publish(Number(id)) : templatesApi.unpublish(Number(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['template', id] })
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('Template updated')
    },
  })

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId)
    } else {
      newExpanded.add(sectionId)
    }
    setExpandedSections(newExpanded)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
      </div>
    )
  }

  if (!template) {
    return (
      <div className="text-center py-12">
        <p className="text-surface-500">Template not found</p>
      </div>
    )
  }

  const sections = template.schema?.sections || []
  const fields = template.schema?.fields || []
  const rules = template.schema?.rules || []

  const getFieldsForSection = (sectionId: string) =>
    fields.filter((f: TemplateSchemaField) => f.section_id === sectionId)

  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/templates')}
            className="p-2 text-surface-500 hover:text-surface-700 hover:bg-surface-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-semibold text-surface-900">{template.name}</h1>
            <p className="text-surface-500 mt-1">
              {template.description || 'No description'} • v{template.version}
            </p>
          </div>
        </div>
        {isAdmin && (
          <div className="flex items-center gap-3">
            <button
              onClick={() => publishMutation.mutate(!template.is_published)}
              className={clsx(
                'btn',
                template.is_published ? 'btn-secondary' : 'btn-success'
              )}
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
          </div>
        )}
      </div>

      {/* Template info card */}
      <div className="card p-6 mb-6">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 rounded-xl bg-primary-50 flex items-center justify-center">
            <FileText className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <p className="text-sm text-surface-500">Original File</p>
            <p className="font-medium text-surface-900">{template.original_file_name}</p>
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4 pt-4 border-t border-surface-100">
          <div>
            <p className="text-sm text-surface-500">Sections</p>
            <p className="text-lg font-semibold text-surface-900">{sections.length}</p>
          </div>
          <div>
            <p className="text-sm text-surface-500">Fields</p>
            <p className="text-lg font-semibold text-surface-900">{fields.length}</p>
          </div>
          <div>
            <p className="text-sm text-surface-500">Rules</p>
            <p className="text-lg font-semibold text-surface-900">{rules.length}</p>
          </div>
        </div>
      </div>

      {/* Schema sections */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-surface-900">Form Schema</h2>
        
        {sections.length === 0 ? (
          <div className="card p-8 text-center">
            <p className="text-surface-500">No sections defined in the schema</p>
          </div>
        ) : (
          sections.map((section: TemplateSchemaSection) => {
            const sectionFields = getFieldsForSection(section.id)
            const isExpanded = expandedSections.has(section.id)
            
            return (
              <div key={section.id} className="card overflow-hidden">
                <button
                  onClick={() => toggleSection(section.id)}
                  className="w-full flex items-center gap-4 p-4 hover:bg-surface-50 transition-colors"
                >
                  <div className="w-8 h-8 rounded-lg bg-surface-100 flex items-center justify-center">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-surface-500" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-surface-500" />
                    )}
                  </div>
                  <div className="flex-1 text-left">
                    <p className="font-medium text-surface-900">{section.title}</p>
                    <p className="text-sm text-surface-500">
                      {sectionFields.length} field{sectionFields.length !== 1 ? 's' : ''}
                    </p>
                  </div>
                  <span className="badge bg-surface-100 text-surface-600">{section.id}</span>
                </button>
                
                {isExpanded && sectionFields.length > 0 && (
                  <div className="border-t border-surface-100 divide-y divide-surface-100">
                    {sectionFields.map((field: TemplateSchemaField) => (
                      <div
                        key={field.id}
                        className="flex items-center gap-4 p-4 hover:bg-surface-50"
                      >
                        <GripVertical className="w-4 h-4 text-surface-300" />
                        <div className="flex-1">
                          <p className="font-medium text-surface-800">{field.label}</p>
                          <p className="text-sm text-surface-500">
                            <span className="font-mono text-xs bg-surface-100 px-1 rounded">
                              {field.id}
                            </span>
                            <span className="mx-2">•</span>
                            <span className="capitalize">{field.type}</span>
                            {field.required && (
                              <>
                                <span className="mx-2">•</span>
                                <span className="text-accent-rose">Required</span>
                              </>
                            )}
                          </p>
                        </div>
                        {field.anchor && (
                          <span className="badge bg-blue-50 text-blue-600">
                            {field.anchor.type}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      {/* Rules section */}
      {rules.length > 0 && (
        <div className="mt-8 space-y-4">
          <h2 className="text-lg font-semibold text-surface-900">Conditional Rules</h2>
          <div className="card divide-y divide-surface-100">
            {rules.map((rule: any, index: number) => (
              <div key={rule.id || index} className="p-4">
                <p className="text-sm font-medium text-surface-700 mb-2">
                  <span className="font-mono text-xs bg-surface-100 px-1 rounded mr-2">
                    {rule.id}
                  </span>
                </p>
                <div className="text-sm text-surface-600">
                  <p>
                    <span className="text-surface-500">IF</span>{' '}
                    {rule.conditions?.map((c: any, i: number) => (
                      <span key={i}>
                        {i > 0 && ' AND '}
                        <span className="font-mono bg-amber-50 text-amber-700 px-1 rounded">
                          {c.field}
                        </span>{' '}
                        {c.operator} {c.value && `"${c.value}"`}
                      </span>
                    ))}
                  </p>
                  <p className="mt-1">
                    <span className="text-surface-500">THEN</span>{' '}
                    {rule.then_actions?.map((a: any, i: number) => (
                      <span key={i}>
                        {i > 0 && ', '}
                        {a.action}{' '}
                        <span className="font-mono bg-emerald-50 text-emerald-700 px-1 rounded">
                          {a.field}
                        </span>
                      </span>
                    ))}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
