export interface Material {
  id: number
  reference_code: string
  name: string
  supplier?: string
  description?: string
  cas_number?: string
  material_type?: string
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface CompositeComponent {
  id: number
  composite_id: number
  cas_number?: string
  component_name: string
  percentage: number
  component_type: 'COMPONENT' | 'IMPURITY'
  confidence_level?: number
  notes?: string
  created_at: string
}

export interface Composite {
  id: number
  material_id: number
  version: number
  origin: 'LAB' | 'CALCULATED' | 'MANUAL'
  status: 'DRAFT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'ARCHIVED'
  metadata?: any
  notes?: string
  created_at: string
  updated_at?: string
  approved_at?: string
  components: CompositeComponent[]
}

export interface ChromatographicAnalysis {
  id: number
  material_id: number
  filename: string
  file_path: string
  batch_number?: string
  supplier?: string
  analysis_date?: string
  lab_technician?: string
  weight: number
  parsed_data?: any
  is_processed: number
  processing_notes?: string
  created_at: string
  updated_at?: string
}

export interface ApprovalWorkflow {
  id: number
  composite_id: number
  assigned_to_id?: number
  assigned_by_id?: number
  status: 'PENDING' | 'IN_REVIEW' | 'APPROVED' | 'REJECTED' | 'CANCELLED'
  review_comments?: string
  rejection_reason?: string
  created_at: string
  assigned_at?: string
  reviewed_at?: string
  completed_at?: string
}

export interface CompositeComparison {
  old_composite_id: number
  new_composite_id: number
  old_version: number
  new_version: number
  components_added: ComponentComparison[]
  components_removed: ComponentComparison[]
  components_changed: ComponentComparison[]
  significant_changes: boolean
  total_change_score: number
}

export interface ComponentComparison {
  component_name: string
  cas_number?: string
  old_percentage?: number
  new_percentage?: number
  change: number
  change_percent?: number
}






