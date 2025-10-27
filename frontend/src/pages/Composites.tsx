import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { FileCheck2, Calculator, X, Package } from 'lucide-react'
import { materialsApi, compositesApi, analysesApi } from '../services/api'

const Composites = () => {
  const [showCalculateModal, setShowCalculateModal] = useState(false)
  const [selectedMaterialId, setSelectedMaterialId] = useState<number | null>(null)
  const [selectedAnalyses, setSelectedAnalyses] = useState<number[]>([])
  const [calculateData, setCalculateData] = useState({
    origin: 'LAB',
    notes: ''
  })
  const navigate = useNavigate()
  // const queryClient = useQueryClient()

  const { data: materials } = useQuery({
    queryKey: ['materials'],
    queryFn: () => materialsApi.getAll(),
  })

  // Obtener todos los composites disponibles
  const { data: allComposites, isLoading: compositesLoading } = useQuery({
    queryKey: ['all-composites'],
    queryFn: async () => {
      if (!materials) return []
      const compositesPromises = materials.map(material => 
        compositesApi.getByMaterial(material.id).catch(() => [])
      )
      const allResults = await Promise.all(compositesPromises)
      return allResults.flat().map(composite => ({
        ...composite,
        material_name: materials.find(m => m.id === composite.material_id)?.name || 'Material desconocido',
        material_reference: materials.find(m => m.id === composite.material_id)?.reference_code || 'N/A'
      }))
    },
    enabled: !!materials,
  })

  const { data: analyses } = useQuery({
    queryKey: ['analyses', selectedMaterialId],
    queryFn: () => analysesApi.getByMaterial(selectedMaterialId!),
    enabled: !!selectedMaterialId,
  })

  const calculateMutation = useMutation({
    mutationFn: async () => {
      if (!selectedMaterialId) throw new Error('Material no seleccionado')
      return await compositesApi.calculate({
        material_id: selectedMaterialId,
        analysis_ids: selectedAnalyses,
        origin: calculateData.origin,
        notes: calculateData.notes
      })
    },
    onSuccess: (data) => {
      setShowCalculateModal(false)
      setSelectedMaterialId(null)
      setSelectedAnalyses([])
      setCalculateData({ origin: 'LAB', notes: '' })
      alert(`✅ Composite calculado! Versión ${data.version} con ${data.components.length} componentes`)
      // Navegar al composite creado
      navigate(`/composites/${data.id}`)
    },
    onError: (error: any) => {
      alert('❌ Error al calcular composite: ' + (error.message || 'Error desconocido'))
    }
  })

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

  const handleCalculate = () => {
    if (!selectedMaterialId) {
      alert('Por favor selecciona un material')
      return
    }

    if (!analyses || analyses.length === 0) {
      alert('⚠️  Este material no tiene análisis cromatográficos. Debes subir al menos un análisis antes de calcular un composite.')
      return
    }

    if (selectedAnalyses.length === 0) {
      alert('⚠️  Debes seleccionar al menos un análisis para calcular el composite')
      return
    }

    const selectedCount = selectedAnalyses.length
    if (confirm(`¿Calcular nuevo composite usando ${selectedCount} análisis seleccionado${selectedCount > 1 ? 's' : ''}?`)) {
      calculateMutation.mutate()
    }
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Composites</h1>
          <p>Gestión de composites calculados y aprobados</p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCalculateModal(true)}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <Calculator size={18} />
          Calcular Composite
        </button>
      </div>

      <div className="card">
        {compositesLoading ? (
          <div className="loading-container">
            <p>Cargando composites...</p>
          </div>
        ) : allComposites && allComposites.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Material</th>
                <th>Versión</th>
                <th>Origen</th>
                <th>Estado</th>
                <th>Componentes</th>
                <th>Fecha</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {allComposites.map((composite) => (
                <tr key={composite.id}>
                  <td>#{composite.id}</td>
                  <td>
                    <div>
                      <div style={{ fontWeight: 500 }}>{composite.material_name}</div>
                      <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                        {composite.material_reference}
                      </div>
                    </div>
                  </td>
                  <td style={{ fontWeight: 500 }}>v{composite.version}</td>
                  <td>
                    <span className="badge badge-info">{composite.origin}</span>
                  </td>
                  <td>
                    <span className={`badge ${
                      composite.status === 'APPROVED' ? 'badge-success' :
                      composite.status === 'PENDING_APPROVAL' ? 'badge-warning' :
                      composite.status === 'REJECTED' ? 'badge-error' : 'badge-info'
                    }`}>
                      {composite.status === 'APPROVED' ? 'Aprobado' :
                       composite.status === 'PENDING_APPROVAL' ? 'Pendiente' :
                       composite.status === 'REJECTED' ? 'Rechazado' : composite.status}
                    </span>
                  </td>
                  <td>{composite.components?.length || 0}</td>
                  <td>
                    {new Date(composite.created_at).toLocaleDateString('es-ES')}
                  </td>
                  <td>
                    <button 
                      className="btn-link"
                      onClick={() => navigate(`/composites/${composite.id}`)}
                    >
                      Ver detalles
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
        <div className="empty-state">
          <FileCheck2 size={48} />
            <h3>No hay composites disponibles</h3>
            <p>Calcula composites desde materiales con análisis cromatográficos</p>
            <button 
              className="btn btn-primary"
              onClick={() => setShowCalculateModal(true)}
              style={{ marginTop: '1rem' }}
            >
              <Calculator size={20} />
              Calcular Primer Composite
            </button>
          </div>
        )}
      </div>

      {/* Modal para calcular composite */}
      {showCalculateModal && (
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
              <h2 style={{ margin: 0, color: '#1f2937', fontSize: '1.5rem', fontWeight: 600 }}>Calcular Composite</h2>
              <button 
                onClick={() => {
                  setShowCalculateModal(false)
                  setSelectedMaterialId(null)
                  setSelectedAnalyses([])
                  setCalculateData({ origin: 'LAB', notes: '' })
                }}
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
                  Material *
                </label>
                <select
                  value={selectedMaterialId || ''}
                  onChange={(e) => setSelectedMaterialId(parseInt(e.target.value) || null)}
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #d1d5db', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                >
                  <option value="">Selecciona un material</option>
                  {materials?.map((material) => (
                    <option key={material.id} value={material.id}>
                      {material.reference_code} - {material.name}
                    </option>
                  ))}
                </select>
              </div>

              {selectedMaterialId && analyses && (
                <div>
                  <div style={{ 
                    padding: '1rem', 
                    background: analyses.length > 0 ? '#f0f9ff' : '#fef2f2', 
                    borderRadius: '8px',
                    border: analyses.length > 0 ? '1px solid #0ea5e9' : '1px solid #f87171',
                    marginBottom: '1rem'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <Package size={16} style={{ color: analyses.length > 0 ? '#0ea5e9' : '#f87171' }} />
                      <span style={{ fontWeight: 500, color: analyses.length > 0 ? '#0ea5e9' : '#f87171' }}>
                        Análisis disponibles: {analyses.length}
                      </span>
                    </div>
                    {analyses.length > 0 ? (
                      <p style={{ fontSize: '0.875rem', color: '#0369a1', margin: 0 }}>
                        ✓ Este material tiene análisis cromatográficos para calcular el composite
                      </p>
                    ) : (
                      <p style={{ fontSize: '0.875rem', color: '#dc2626', margin: 0 }}>
                        ⚠️ Este material no tiene análisis. Debes subir análisis cromatográficos primero.
                      </p>
                    )}
                  </div>

                  {analyses && analyses.length > 0 && (
                    <div>
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

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '200px', overflowY: 'auto' }}>
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
                              boxShadow: analysis.is_processed === 1 ? '0 1px 3px rgba(0, 0, 0, 0.1)' : 'none'
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
                            <div style={{ flex: 1 }}>
                              <p style={{ 
                                fontWeight: 500, 
                                margin: 0, 
                                color: analysis.is_processed === 1 ? '#1f2937' : '#dc2626',
                                fontSize: '0.95rem'
                              }}>
                                {analysis.filename}
                              </p>
                              <p style={{ 
                                fontSize: '0.875rem', 
                                color: analysis.is_processed === 1 ? '#6b7280' : '#dc2626', 
                                margin: 0 
                              }}>
                                {analysis.batch_number || 'Sin lote'} • {analysis.supplier || 'Sin proveedor'}
                              </p>
                            </div>
                            <span className={`badge ${
                              analysis.is_processed === 1 ? 'badge-success' :
                              analysis.is_processed === -1 ? 'badge-error' : 'badge-warning'
                            }`}>
                              {analysis.is_processed === 1 ? 'Procesado' : 
                               analysis.is_processed === -1 ? 'Error' : 'Pendiente'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#374151', fontSize: '0.9rem' }}>
                  Origen
                </label>
                <select
                  value={calculateData.origin}
                  onChange={(e) => setCalculateData({ ...calculateData, origin: e.target.value })}
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #d1d5db', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                >
                  <option value="LAB">Laboratorio</option>
                  <option value="PRODUCTION">Producción</option>
                  <option value="RESEARCH">Investigación</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#374151', fontSize: '0.9rem' }}>
                  Notas
                </label>
                <textarea
                  value={calculateData.notes}
                  onChange={(e) => setCalculateData({ ...calculateData, notes: e.target.value })}
                  placeholder="Notas adicionales sobre el composite..."
                  rows={3}
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #d1d5db', 
                    borderRadius: '8px', 
                    resize: 'vertical',
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
                  onClick={handleCalculate}
                  disabled={calculateMutation.isPending || !selectedMaterialId || !analyses || analyses.length === 0 || selectedAnalyses.length === 0}
                  style={{ 
                    flex: 1,
                    padding: '0.75rem 1.5rem',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    borderRadius: '8px',
                    transition: 'all 0.2s ease',
                    opacity: (!selectedMaterialId || !analyses || analyses.length === 0 || selectedAnalyses.length === 0) ? 0.5 : 1,
                    cursor: (!selectedMaterialId || !analyses || analyses.length === 0 || selectedAnalyses.length === 0) ? 'not-allowed' : 'pointer'
                  }}
                >
                  {calculateMutation.isPending ? 'Calculando...' : 
                   selectedAnalyses.length === 0 ? 'Selecciona análisis para calcular' :
                   `Calcular Composite (${selectedAnalyses.length} análisis)`}
                </button>
                <button 
                  className="btn"
                  onClick={() => {
                    setShowCalculateModal(false)
                    setSelectedMaterialId(null)
                    setSelectedAnalyses([])
                    setCalculateData({ origin: 'LAB', notes: '' })
                  }}
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

export default Composites