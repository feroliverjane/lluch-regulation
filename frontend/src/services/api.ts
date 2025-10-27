import axios from 'axios'
import type { 
  Material, 
  Composite, 
  ChromatographicAnalysis, 
  ApprovalWorkflow,
  CompositeComparison
} from '../types'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_PREFIX = '/api'

const api = axios.create({
  baseURL: `${API_URL}${API_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Materials API
export const materialsApi = {
  getAll: async (params?: { skip?: number; limit?: number; active_only?: boolean }) => {
    const { data } = await api.get<Material[]>('/materials', { params })
    return data
  },
  
  getById: async (id: number) => {
    const { data } = await api.get<Material>(`/materials/${id}`)
    return data
  },
  
  getByReference: async (referenceCode: string) => {
    const { data } = await api.get<Material>(`/materials/reference/${referenceCode}`)
    return data
  },
  
  create: async (material: Partial<Material>) => {
    const { data } = await api.post<Material>('/materials', material)
    return data
  },
  
  update: async (id: number, material: Partial<Material>) => {
    const { data } = await api.put<Material>(`/materials/${id}`, material)
    return data
  },
  
  delete: async (id: number) => {
    await api.delete(`/materials/${id}`)
  },
}

// Chromatographic Analyses API
export const analysesApi = {
  upload: async (formData: FormData) => {
    const { data } = await api.post<ChromatographicAnalysis>(
      '/chromatographic-analyses',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    )
    return data
  },
  
  getByMaterial: async (materialId: number) => {
    const { data } = await api.get<ChromatographicAnalysis[]>(
      `/chromatographic-analyses/material/${materialId}`
    )
    return data
  },
  
  getById: async (id: number) => {
    const { data } = await api.get<ChromatographicAnalysis>(
      `/chromatographic-analyses/${id}`
    )
    return data
  },
  
  delete: async (id: number) => {
    await api.delete(`/chromatographic-analyses/${id}`)
  },
}

// Composites API
export const compositesApi = {
  calculate: async (request: {
    material_id: number
    origin?: string
    analysis_ids?: number[]
    notes?: string
  }) => {
    const { data } = await api.post<Composite>('/composites/calculate', request)
    return data
  },
  
  create: async (composite: any) => {
    const { data } = await api.post<Composite>('/composites', composite)
    return data
  },
  
  getById: async (id: number) => {
    const { data } = await api.get<Composite>(`/composites/${id}`)
    return data
  },
  
  getByMaterial: async (
    materialId: number,
    params?: { skip?: number; limit?: number; status_filter?: string }
  ) => {
    const { data } = await api.get<Composite[]>(
      `/composites/material/${materialId}`,
      { params }
    )
    return data
  },
  
  compare: async (compositeId: number, otherCompositeId: number) => {
    const { data } = await api.get<CompositeComparison>(
      `/composites/${compositeId}/compare/${otherCompositeId}`
    )
    return data
  },
  
  submitForApproval: async (id: number, assignedToId?: number) => {
    const { data } = await api.put<Composite>(
      `/composites/${id}/submit-for-approval`,
      null,
      { params: { assigned_to_id: assignedToId } }
    )
    return data
  },
  
  approve: async (id: number, comments?: string) => {
    const { data } = await api.put<Composite>(
      `/composites/${id}/approve`,
      null,
      { params: { comments } }
    )
    return data
  },
  
  reject: async (id: number, reason: string, comments?: string) => {
    const { data } = await api.put<Composite>(
      `/composites/${id}/reject`,
      null,
      { params: { reason, comments } }
    )
    return data
  },
  
  delete: async (id: number) => {
    await api.delete(`/composites/${id}`)
  },
}

// Workflows API
export const workflowsApi = {
  getAll: async (params?: {
    status_filter?: string
    assigned_to_id?: number
    skip?: number
    limit?: number
  }) => {
    const { data } = await api.get<ApprovalWorkflow[]>('/workflows', { params })
    return data
  },
  
  getById: async (id: number) => {
    const { data } = await api.get<ApprovalWorkflow>(`/workflows/${id}`)
    return data
  },
  
  getByComposite: async (compositeId: number) => {
    const { data } = await api.get<ApprovalWorkflow>(
      `/workflows/composite/${compositeId}`
    )
    return data
  },
}

export default api






