import { useQuery, useMutation } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { useState, useRef } from 'react'
import { materialsApi, compositesApi, analysesApi } from '../services/api'
import { ArrowLeft, Package, FileCheck2, FlaskConical, Upload, Calculator, X } from 'lucide-react'

const MaterialDetail = () => {
  const { id } = useParams<{ id: string }>()
  const materialId = parseInt(id || '0')
  // const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedAnalyses, setSelectedAnalyses] = useState<number[]>([])
  const [uploadData, setUploadData] = useState({
    batch_number: '',
    supplier: '',
    weight: '1.0'
  })
  const [isCalculating, setIsCalculating] = useState(false)

  const { data: material, isLoading } = useQuery({
    queryKey: ['material', materialId],
    queryFn: () => materialsApi.getById(materialId),
  })

  const { data: composites, refetch: refetchComposites } = useQuery({
    queryKey: ['composites', materialId],
    queryFn: () => compositesApi.getByMaterial(materialId),
  })

  const { data: analyses, refetch: refetchAnalyses } = useQuery({
    queryKey: ['analyses', materialId],
    queryFn: () => analysesApi.getByMaterial(materialId),
  })

  // Mutation para subir análisis
  const uploadMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      return await analysesApi.upload(formData)
    },
    onSuccess: () => {
      refetchAnalyses()
      setShowUploadModal(false)
      setSelectedFile(null)
      setUploadData({ batch_number: '', supplier: '', weight: '1.0' })
      alert('✅ Análisis subido y procesado exitosamente!')
    },
    onError: (error: any) => {
      alert('❌ Error al subir el análisis: ' + (error.message || 'Error desconocido'))
    }
  })

  // Mutation para calcular composite
  const calculateMutation = useMutation({
    mutationFn: async () => {
      return await compositesApi.calculate({
        material_id: materialId,
        analysis_ids: selectedAnalyses,
        origin: 'LAB',
        notes: 'Composite calculado desde la interfaz web'
      })
    },
    onSuccess: (data) => {
      refetchComposites()
      setIsCalculating(false)
      alert(`✅ Composite calculado! Versión ${data.version} con ${data.components.length} componentes`)
    },
    onError: (error: any) => {
      setIsCalculating(false)
      alert('❌ Error al calcular composite: ' + (error.message || 'Error desconocido'))
    }
  })

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      alert('Por favor selecciona un archivo CSV')
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('material_id', materialId.toString())
    formData.append('batch_number', uploadData.batch_number)
    formData.append('supplier', uploadData.supplier)
    formData.append('weight', uploadData.weight)

    uploadMutation.mutate(formData)
  }

  const handleAnalysisSelection = (analysisId: number, isSelected: boolean) => {
    if (isSelected) {
      setSelectedAnalyses(prev => [...prev, analysisId])
    } else {
      setSelectedAnalyses(prev => prev.filter(id => id !== analysisId))
    }
  }

  const handleSelectAll = () => {
    if (!analyses) return
    const processedAnalyses = analyses.filter(a => a.is_processed === 1)
    if (selectedAnalyses.length === processedAnalyses.length) {
      setSelectedAnalyses([])
    } else {
      setSelectedAnalyses(processedAnalyses.map(a => a.id))
    }
  }

  const handleCalculateComposite = () => {
    if (!analyses || analyses.length === 0) {
      alert('⚠️  Debes subir al menos un análisis cromatográfico antes de calcular un composite')
      return
    }

    if (selectedAnalyses.length === 0) {
      alert('⚠️  Debes seleccionar al menos un análisis para calcular el composite')
      return
    }

    const selectedCount = selectedAnalyses.length
    if (confirm(`¿Calcular nuevo composite usando ${selectedCount} análisis seleccionado${selectedCount > 1 ? 's' : ''}?`)) {
      setIsCalculating(true)
      calculateMutation.mutate()
    }
  }

  if (isLoading) {
    return <div className="loading-container">Cargando...</div>
  }

  if (!material) {
    return <div className="error-container">Material no encontrado</div>
  }

  return (
    <div>
      <Link to="/materials" className="link" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <ArrowLeft size={20} />
        Volver a materiales
      </Link>

      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
          <div style={{ background: '#3b82f620', padding: '1rem', borderRadius: '12px', color: '#3b82f6' }}>
            <Package size={32} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.875rem', marginBottom: '0.25rem' }}>{material.name}</h1>
            <p style={{ color: '#6b7280' }}>{material.reference_code}</p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
          <div>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Tipo</p>
            <p style={{ fontWeight: 500 }}>{material.material_type || 'N/A'}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Proveedor</p>
            <p style={{ fontWeight: 500 }}>{material.supplier || 'N/A'}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>CAS Number</p>
            <p style={{ fontWeight: 500 }}><code>{material.cas_number || 'N/A'}</code></p>
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Estado</p>
            <span className={`badge ${material.is_active ? 'badge-success' : 'badge-error'}`}>
              {material.is_active ? 'Activo' : 'Inactivo'}
            </span>
          </div>
        </div>

        {material.description && (
          <div style={{ marginTop: '1.5rem' }}>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>Descripción</p>
            <p>{material.description}</p>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem', marginTop: '1.5rem' }}>
        <div className="card">
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <FileCheck2 size={20} />
            Composites ({composites?.length || 0})
          </h2>
          {composites && composites.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {composites.map((composite) => (
                <Link 
                  key={composite.id} 
                  to={`/composites/${composite.id}`}
                  style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    padding: '0.75rem', 
                    background: '#ffffff', 
                    borderRadius: '8px',
                    textDecoration: 'none',
                    color: 'inherit',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                    transition: 'all 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.backgroundColor = '#f8fafc'
                    e.target.style.borderColor = '#3b82f6'
                    e.target.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)'
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.backgroundColor = '#ffffff'
                    e.target.style.borderColor = '#e5e7eb'
                    e.target.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)'
                  }}
                >
                  <div>
                    <p style={{ fontWeight: 600, color: '#1f2937', margin: 0, fontSize: '0.95rem' }}>Versión {composite.version}</p>
                    <p style={{ fontSize: '0.875rem', color: '#6b7280', margin: '0.25rem 0 0 0' }}>{composite.origin}</p>
                  </div>
                  <span className={`badge ${
                    composite.status === 'APPROVED' ? 'badge-success' :
                    composite.status === 'PENDING_APPROVAL' ? 'badge-warning' :
                    composite.status === 'REJECTED' ? 'badge-error' : 'badge-info'
                  }`} style={{ fontSize: '0.75rem' }}>
                    {composite.status}
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <p className="empty-state">No hay composites creados</p>
          )}
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
              <FlaskConical size={20} />
              Análisis Cromatográficos ({analyses?.length || 0})
            </h2>
            <button 
              className="btn btn-primary" 
              onClick={() => setShowUploadModal(true)}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <Upload size={18} />
              Subir CSV
            </button>
          </div>
          {analyses && analyses.length > 0 && (
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center', 
              marginBottom: '1rem', 
              padding: '0.75rem', 
              background: '#f8fafc', 
              borderRadius: '8px',
              border: '1px solid #e2e8f0'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <button 
                  className="btn btn-sm"
                  onClick={handleSelectAll}
                  style={{ 
                    fontSize: '0.875rem',
                    background: '#3b82f6',
                    color: 'white',
                    border: 'none',
                    padding: '0.5rem 1rem',
                    borderRadius: '6px',
                    cursor: 'pointer'
                  }}
                >
                  {selectedAnalyses.length === analyses.filter(a => a.is_processed === 1).length ? 'Deseleccionar Todo' : 'Seleccionar Todo'}
                </button>
                <span style={{ 
                  fontSize: '0.875rem', 
                  color: '#374151',
                  fontWeight: 500
                }}>
                  {selectedAnalyses.length} de {analyses.filter(a => a.is_processed === 1).length} análisis seleccionados
                </span>
              </div>
            </div>
          )}

          {analyses && analyses.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {analyses.map((analysis) => (
                <div 
                  key={analysis.id}
                  style={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    gap: '1rem',
                    padding: '0.75rem', 
                    background: analysis.is_processed === 1 ? '#ffffff' : '#fef2f2', 
                    borderRadius: '8px',
                    border: selectedAnalyses.includes(analysis.id) ? '2px solid #3b82f6' : '1px solid #e5e7eb',
                    boxShadow: analysis.is_processed === 1 ? '0 1px 3px rgba(0, 0, 0, 0.1)' : 'none',
                    minWidth: 0,
                    overflow: 'hidden'
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedAnalyses.includes(analysis.id)}
                    onChange={(e) => handleAnalysisSelection(analysis.id, e.target.checked)}
                    disabled={analysis.is_processed !== 1}
                    style={{ 
                      width: '18px', 
                      height: '18px',
                      cursor: analysis.is_processed === 1 ? 'pointer' : 'not-allowed',
                      opacity: analysis.is_processed === 1 ? 1 : 0.5
                    }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ 
                      fontWeight: 500, 
                      margin: 0, 
                      color: analysis.is_processed === 1 ? '#1f2937' : '#dc2626',
                      fontSize: '0.9rem',
                      wordBreak: 'break-word',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {analysis.filename}
                    </p>
                    <p style={{ 
                      fontSize: '0.8rem', 
                      color: analysis.is_processed === 1 ? '#6b7280' : '#dc2626', 
                      margin: 0,
                      wordBreak: 'break-word',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {analysis.batch_number || 'Sin lote'} • {analysis.supplier || 'Sin proveedor'}
                    </p>
                  </div>
                  <span className={`badge ${
                    analysis.is_processed === 1 ? 'badge-success' :
                    analysis.is_processed === -1 ? 'badge-error' : 'badge-warning'
                  }`} style={{ 
                    flexShrink: 0,
                    fontSize: '0.75rem',
                    whiteSpace: 'nowrap'
                  }}>
                    {analysis.is_processed === 1 ? 'Procesado' : 
                     analysis.is_processed === -1 ? 'Error' : 'Pendiente'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state">No hay análisis cargados</p>
          )}
          
          {analyses && analyses.length > 0 && (
            <button 
              className="btn btn-success" 
              onClick={handleCalculateComposite}
              disabled={isCalculating || selectedAnalyses.length === 0}
              style={{ 
                marginTop: '1rem', 
                width: '100%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                gap: '0.5rem',
                opacity: selectedAnalyses.length === 0 ? 0.5 : 1,
                cursor: selectedAnalyses.length === 0 ? 'not-allowed' : 'pointer'
              }}
            >
              <Calculator size={18} />
              {isCalculating ? 'Calculando...' : 
               selectedAnalyses.length === 0 ? 'Selecciona análisis para calcular' :
               `Calcular Composite (${selectedAnalyses.length} análisis)`}
            </button>
          )}
        </div>
      </div>

      {/* Modal de Upload */}
      {showUploadModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            borderRadius: '12px',
            padding: '2rem',
            maxWidth: '500px',
            width: '90%',
            maxHeight: '90vh',
            overflow: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, color: '#1f2937', fontSize: '1.5rem', fontWeight: 600 }}>Subir Análisis CSV</h2>
              <button 
                onClick={() => setShowUploadModal(false)}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  cursor: 'pointer',
                  color: '#6b7280',
                  padding: '0.25rem',
                  borderRadius: '4px',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = '#f3f4f6'}
                onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#374151', fontSize: '0.9rem' }}>
                  Archivo CSV *
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  ref={fileInputRef}
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #d1d5db', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                />
                {selectedFile && (
                  <p style={{ 
                    fontSize: '0.875rem', 
                    color: '#059669', 
                    marginTop: '0.5rem',
                    fontWeight: 500,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}>
                    ✓ {selectedFile.name}
                  </p>
                )}
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#374151', fontSize: '0.9rem' }}>
                  Número de Lote
                </label>
                <input
                  type="text"
                  value={uploadData.batch_number}
                  onChange={(e) => setUploadData({ ...uploadData, batch_number: e.target.value })}
                  placeholder="ej: B2024-001"
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #d1d5db', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#374151', fontSize: '0.9rem' }}>
                  Proveedor
                </label>
                <input
                  type="text"
                  value={uploadData.supplier}
                  onChange={(e) => setUploadData({ ...uploadData, supplier: e.target.value })}
                  placeholder="ej: Citrus Italy SpA"
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #d1d5db', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#374151', fontSize: '0.9rem' }}>
                  Peso/Cantidad (para promedio ponderado)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={uploadData.weight}
                  onChange={(e) => setUploadData({ ...uploadData, weight: e.target.value })}
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #d1d5db', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                />
              </div>

              <div style={{ 
                display: 'flex', 
                gap: '1rem', 
                marginTop: '2rem',
                paddingTop: '1rem',
                borderTop: '1px solid #e5e7eb'
              }}>
                <button 
                  className="btn btn-primary"
                  onClick={handleUpload}
                  disabled={uploadMutation.isPending || !selectedFile}
                  style={{ 
                    flex: 1,
                    padding: '0.75rem 1.5rem',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    borderRadius: '8px',
                    transition: 'all 0.2s ease',
                    opacity: !selectedFile ? 0.5 : 1,
                    cursor: !selectedFile ? 'not-allowed' : 'pointer'
                  }}
                >
                  {uploadMutation.isPending ? 'Subiendo...' : 'Subir y Procesar'}
                </button>
                <button 
                  className="btn"
                  onClick={() => setShowUploadModal(false)}
                  style={{ 
                    flex: 1, 
                    background: '#f3f4f6',
                    color: '#374151',
                    padding: '0.75rem 1.5rem',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    borderRadius: '8px',
                    border: '1px solid #d1d5db',
                    transition: 'all 0.2s ease'
                  }}
                >
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default MaterialDetail

