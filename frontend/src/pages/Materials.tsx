import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Package, X, Search } from 'lucide-react'
import { materialsApi } from '../services/api'

const Materials = () => {
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [newMaterial, setNewMaterial] = useState({
    name: '',
    reference_code: '',
    material_type: 'NATURAL',
    supplier: '',
    cas_number: '',
    description: '',
    is_active: true
  })
  const queryClient = useQueryClient()

  const { data: materials, isLoading, error } = useQuery({
    queryKey: ['materials'],
    queryFn: () => materialsApi.getAll(),
  })

  // Filtrar materiales según la búsqueda
  const filteredMaterials = useMemo(() => {
    if (!materials) return []
    if (!searchQuery.trim()) return materials
    
    const query = searchQuery.toLowerCase()
    return materials.filter(material => 
      material.reference_code?.toLowerCase().includes(query) ||
      material.name?.toLowerCase().includes(query) ||
      material.supplier?.toLowerCase().includes(query) ||
      material.cas_number?.toLowerCase().includes(query)
    )
  }, [materials, searchQuery])

  const createMutation = useMutation({
    mutationFn: async (material: any) => {
      return await materialsApi.create(material)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['materials'] })
      setShowCreateModal(false)
      setNewMaterial({
        name: '',
        reference_code: '',
        material_type: 'NATURAL',
        supplier: '',
        cas_number: '',
        description: '',
        is_active: true
      })
      alert('✅ Material creado exitosamente!')
    },
    onError: (error: any) => {
      alert('❌ Error al crear material: ' + (error.message || 'Error desconocido'))
    }
  })

  const handleCreateMaterial = () => {
    if (!newMaterial.name || !newMaterial.reference_code) {
      alert('Por favor completa los campos obligatorios (Nombre y Código de Referencia)')
      return
    }
    createMutation.mutate(newMaterial)
  }

  if (isLoading) return <div className="loading">Cargando materiales...</div>
  if (error) return <div className="error">Error al cargar materiales</div>

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Materiales</h1>
          <p>Gestión de materiales y materias primas</p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateModal(true)}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
        >
          <Plus size={18} />
          Nuevo Material
        </button>
      </div>

      <div className="card">
        {/* Barra de búsqueda */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ position: 'relative' }}>
            <Search 
              size={18} 
              style={{ 
                position: 'absolute', 
                left: '12px', 
                top: '50%', 
                transform: 'translateY(-50%)',
                color: '#6b7280'
              }} 
            />
            <input
              type="text"
              placeholder="Buscar por código, nombre, proveedor o CAS..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem 0.75rem 0.75rem 2.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                fontSize: '0.9rem',
                backgroundColor: 'white',
                transition: 'border-color 0.2s ease'
              }}
            />
          </div>
          {searchQuery && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: '#6b7280' }}>
              {filteredMaterials.length} material{filteredMaterials.length !== 1 ? 'es' : ''} encontrado{filteredMaterials.length !== 1 ? 's' : ''}
            </div>
          )}
        </div>

        {filteredMaterials && filteredMaterials.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>Referencia</th>
                <th>Nombre</th>
                <th>Tipo</th>
                <th>Proveedor</th>
                <th>CAS</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filteredMaterials.map((material) => (
                <tr key={material.id}>
                  <td>
                    <Link to={`/materials/${material.id}`} className="link">
                      {material.reference_code}
                    </Link>
                  </td>
                  <td>{material.name}</td>
                  <td>
                    <span className="badge badge-info">
                      {material.material_type || 'N/A'}
                    </span>
                  </td>
                  <td>{material.supplier || '-'}</td>
                  <td>{material.cas_number || '-'}</td>
                  <td>
                    <span className={`badge ${material.is_active ? 'badge-success' : 'badge-error'}`}>
                      {material.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td>
                    <Link to={`/materials/${material.id}`} className="btn-link">
                      Ver detalles
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <Package size={48} />
            <h3>{searchQuery ? 'No se encontraron materiales' : 'No hay materiales'}</h3>
            <p>{searchQuery ? 'Intenta con otros términos de búsqueda' : 'Crea tu primer material para comenzar'}</p>
            <button
              className="btn btn-primary"
              onClick={() => setShowCreateModal(true)}
              style={{ marginTop: '1rem' }}
            >
              <Plus size={20} />
              Crear Material
            </button>
          </div>
        )}
      </div>

      {/* Modal para crear material */}
      {showCreateModal && (
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
              <h2 style={{ margin: 0, color: '#1f2937', fontSize: '1.5rem', fontWeight: 600 }}>Crear Nuevo Material</h2>
              <button 
                onClick={() => setShowCreateModal(false)}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  fontSize: '1.5rem', 
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
                  Nombre *
                </label>
                <input
                  type="text"
                  value={newMaterial.name}
                  onChange={(e) => setNewMaterial({ ...newMaterial, name: e.target.value })}
                  placeholder="Nombre del material"
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
                  Código de Referencia *
                </label>
                <input
                  type="text"
                  value={newMaterial.reference_code}
                  onChange={(e) => setNewMaterial({ ...newMaterial, reference_code: e.target.value })}
                  placeholder="Ej: LEM-001"
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
                  Tipo de Material
                </label>
                <select
                  value={newMaterial.material_type}
                  onChange={(e) => setNewMaterial({ ...newMaterial, material_type: e.target.value })}
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
                  <option value="NATURAL">Natural</option>
                  <option value="SYNTHETIC">Sintético</option>
                  <option value="BLEND">Mezcla</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: '#374151', fontSize: '0.9rem' }}>
                  Proveedor
                </label>
                <input
                  type="text"
                  value={newMaterial.supplier}
                  onChange={(e) => setNewMaterial({ ...newMaterial, supplier: e.target.value })}
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
                  Número CAS
                </label>
                <input
                  type="text"
                  value={newMaterial.cas_number}
                  onChange={(e) => setNewMaterial({ ...newMaterial, cas_number: e.target.value })}
                  placeholder="Ej: 8008-56-8"
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
                  Descripción
                </label>
                <textarea
                  value={newMaterial.description}
                  onChange={(e) => setNewMaterial({ ...newMaterial, description: e.target.value })}
                  placeholder="Descripción del material"
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
                  onClick={handleCreateMaterial}
                  disabled={createMutation.isPending}
                  style={{ 
                    flex: 1,
                    padding: '0.75rem 1.5rem',
                    fontSize: '0.9rem',
                    fontWeight: 600,
                    borderRadius: '8px',
                    transition: 'all 0.2s ease'
                  }}
                >
                  {createMutation.isPending ? 'Creando...' : 'Crear Material'}
                </button>
                <button 
                  className="btn"
                  onClick={() => setShowCreateModal(false)}
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

export default Materials