import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FlaskConical, Upload, X } from 'lucide-react'
import { materialsApi, analysesApi } from '../services/api'

const ChromatographicAnalyses = () => {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedMaterialId, setSelectedMaterialId] = useState<number | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadData, setUploadData] = useState({
    batch_number: '',
    supplier: '',
    weight: '1.0'
  })
  const queryClient = useQueryClient()

  const { data: materials } = useQuery({
    queryKey: ['materials'],
    queryFn: () => materialsApi.getAll(),
  })

  // Obtener todos los análisis de todos los materiales
  const { data: allAnalyses, isLoading } = useQuery({
    queryKey: ['all-analyses'],
    queryFn: async () => {
      if (!materials) return []
      const analysesPromises = materials.map(material => 
        analysesApi.getByMaterial(material.id).catch(() => [])
      )
      const allResults = await Promise.all(analysesPromises)
      return allResults.flat().map(analysis => ({
        ...analysis,
        material_name: materials.find(m => m.id === analysis.material_id)?.name || 'Material desconocido',
        material_reference: materials.find(m => m.id === analysis.material_id)?.reference_code || 'N/A'
      }))
    },
    enabled: !!materials,
  })

  const uploadMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      return await analysesApi.upload(formData)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-analyses'] })
      setShowUploadModal(false)
      setSelectedMaterialId(null)
      setSelectedFile(null)
      setUploadData({ batch_number: '', supplier: '', weight: '1.0' })
      alert('✅ Análisis subido exitosamente!')
    },
    onError: (error: any) => {
      alert('❌ Error al subir el análisis: ' + (error.message || 'Error desconocido'))
    }
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) {
      alert('Por favor selecciona un archivo CSV')
      return
    }

    if (!selectedMaterialId) {
      alert('Por favor selecciona un material')
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('material_id', selectedMaterialId.toString())
    formData.append('batch_number', uploadData.batch_number)
    formData.append('supplier', uploadData.supplier)
    formData.append('weight', uploadData.weight)

    uploadMutation.mutate(formData)
  }

  if (isLoading) {
    return <div className="loading-container">Cargando análisis...</div>
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Análisis Cromatográficos</h1>
          <p>Gestión de análisis de laboratorio</p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => setShowUploadModal(true)}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <Upload size={18} />
          Subir Análisis CSV
        </button>
      </div>

      <div className="card">
        {allAnalyses && allAnalyses.length > 0 ? (
          <table className="table" style={{ tableLayout: 'fixed', width: '100%' }}>
            <thead>
              <tr>
                <th style={{ width: '50px' }}>ID</th>
                <th style={{ width: '130px' }}>Material</th>
                <th style={{ width: '160px' }}>Archivo</th>
                <th style={{ width: '90px' }}>Lote</th>
                <th style={{ width: '110px' }}>Proveedor</th>
                <th style={{ width: '90px' }}>Estado</th>
                <th style={{ width: '120px' }}>Componentes</th>
                <th style={{ width: '140px' }}>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {allAnalyses.map((analysis) => (
                <tr key={analysis.id}>
                  <td style={{ fontSize: '0.875rem' }}>#{analysis.id}</td>
                  <td>
                    <div>
                      <div style={{ fontWeight: 500, fontSize: '0.875rem', wordBreak: 'break-word' }}>{analysis.material_name}</div>
                      <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                        {analysis.material_reference}
                      </div>
                    </div>
                  </td>
                  <td style={{ fontWeight: 500, fontSize: '0.875rem', wordBreak: 'break-word' }}>{analysis.filename}</td>
                  <td style={{ fontSize: '0.875rem', wordBreak: 'break-word' }}>{analysis.batch_number || '-'}</td>
                  <td style={{ fontSize: '0.875rem', wordBreak: 'break-word' }}>{analysis.supplier || '-'}</td>
                  <td>
                    <span className={`badge ${
                      analysis.is_processed === 1 ? 'badge-success' :
                      analysis.is_processed === -1 ? 'badge-error' : 'badge-warning'
                    }`} style={{ fontSize: '0.75rem' }}>
                      {analysis.is_processed === 1 ? 'Procesado' :
                       analysis.is_processed === -1 ? 'Error' : 'Pendiente'}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center', fontSize: '0.875rem' }}>{analysis.parsed_data?.component_count || 0}</td>
                  <td style={{ fontSize: '0.875rem' }}>
                    {new Date(analysis.created_at).toLocaleDateString('es-ES')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <FlaskConical size={48} />
            <h3>No hay análisis disponibles</h3>
            <p>Sube análisis CSV desde la página de detalle de cada material o usa el botón de arriba</p>
            <button 
              className="btn btn-primary"
              onClick={() => setShowUploadModal(true)}
              style={{ marginTop: '1rem' }}
            >
              <Upload size={20} />
              Subir Primer Análisis
            </button>
          </div>
        )}
      </div>

      {/* Modal para subir análisis */}
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

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#374151', fontSize: '0.9rem' }}>
                  Archivo CSV *
                </label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
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
                    margin: '0.5rem 0 0 0',
                    fontWeight: 500,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem'
                  }}>
                    ✓ Archivo seleccionado: {selectedFile.name}
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
                  placeholder="Ej: LEM-2024-001"
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
                  placeholder="Nombre del proveedor"
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
                  Peso (kg)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={uploadData.weight}
                  onChange={(e) => setUploadData({ ...uploadData, weight: e.target.value })}
                  placeholder="1.0"
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
                  disabled={uploadMutation.isPending || !selectedFile || !selectedMaterialId}
                  style={{ 
                    flex: 1,
                    padding: '0.75rem 1.5rem',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    borderRadius: '8px',
                    transition: 'all 0.2s ease',
                    opacity: (!selectedFile || !selectedMaterialId) ? 0.5 : 1,
                    cursor: (!selectedFile || !selectedMaterialId) ? 'not-allowed' : 'pointer'
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

export default ChromatographicAnalyses