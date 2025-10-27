import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { materialsApi, compositesApi } from '../services/api'
import { CheckCircle, XCircle, Send, FileCheck2 } from 'lucide-react'

const Workflows = () => {
  const queryClient = useQueryClient()

  // Obtener todos los composites y filtrar solo los que necesitan aprobación
  const { data: allComposites, isLoading } = useQuery({
    queryKey: ['all-composites-for-approval'],
    queryFn: async () => {
      const materials = await materialsApi.getAll()
      const compositesPromises = materials.map(material => 
        compositesApi.getByMaterial(material.id).catch(() => [])
      )
      const allResults = await Promise.all(compositesPromises)
      const allComposites = allResults.flat().map(composite => ({
        ...composite,
        material_name: materials.find(m => m.id === composite.material_id)?.name || 'Material desconocido',
        material_reference: materials.find(m => m.id === composite.material_id)?.reference_code || 'N/A'
      }))
      
      // Filtrar solo composites en DRAFT o PENDING_APPROVAL
      return allComposites.filter(composite => 
        composite.status === 'DRAFT' || composite.status === 'PENDING_APPROVAL'
      )
    },
  })

  // Mutaciones para acciones de aprobación
  const submitMutation = useMutation({
    mutationFn: async (compositeId: number) => {
      return await compositesApi.submitForApproval(compositeId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-composites-for-approval'] })
      queryClient.invalidateQueries({ queryKey: ['all-composites'] })
      alert('✅ Composite enviado para aprobación')
    },
    onError: (error: any) => {
      alert('❌ Error al enviar para aprobación: ' + (error.message || 'Error desconocido'))
    }
  })

  const approveMutation = useMutation({
    mutationFn: async (compositeId: number) => {
      return await compositesApi.approve(compositeId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-composites-for-approval'] })
      queryClient.invalidateQueries({ queryKey: ['all-composites'] })
      alert('✅ Composite aprobado exitosamente')
    },
    onError: (error: any) => {
      alert('❌ Error al aprobar composite: ' + (error.message || 'Error desconocido'))
    }
  })

  const rejectMutation = useMutation({
    mutationFn: async (compositeId: number) => {
      return await compositesApi.reject(compositeId, 'Rechazado desde la página de aprobaciones')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-composites-for-approval'] })
      queryClient.invalidateQueries({ queryKey: ['all-composites'] })
      alert('✅ Composite rechazado')
    },
    onError: (error: any) => {
      alert('❌ Error al rechazar composite: ' + (error.message || 'Error desconocido'))
    }
  })

  const handleSubmit = (compositeId: number) => {
    if (confirm('¿Enviar este composite para aprobación?')) {
      submitMutation.mutate(compositeId)
    }
  }

  const handleApprove = (compositeId: number) => {
    if (confirm('¿Aprobar este composite?')) {
      approveMutation.mutate(compositeId)
    }
  }

  const handleReject = (compositeId: number) => {
    if (confirm('¿Rechazar este composite?')) {
      rejectMutation.mutate(compositeId)
    }
  }

  // Ordenar composites: PENDING_APPROVAL primero, luego DRAFT, ambos por fecha de creación (más reciente primero)
  const sortedComposites = allComposites ? [...allComposites].sort((a, b) => {
    if (a.status === 'PENDING_APPROVAL' && b.status === 'DRAFT') return -1
    if (a.status === 'DRAFT' && b.status === 'PENDING_APPROVAL') return 1
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  }) : []

  if (isLoading) {
    return <div className="loading-container">Cargando aprobaciones...</div>
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Aprobaciones</h1>
          <p>Gestión de composites pendientes de aprobación</p>
        </div>
      </div>

      <div className="card">
        {sortedComposites && sortedComposites.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Material</th>
                <th>Versión</th>
                <th>Estado</th>
                <th>Componentes</th>
                <th>Fecha</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {sortedComposites.map((composite) => (
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
                    <span className={`badge ${
                      composite.status === 'PENDING_APPROVAL' ? 'badge-warning' : 'badge-info'
                    }`}>
                      {composite.status === 'PENDING_APPROVAL' ? 'Pendiente' : 'Draft'}
                    </span>
                  </td>
                  <td>{composite.components?.length || 0}</td>
                  <td>
                    {new Date(composite.created_at).toLocaleDateString('es-ES')}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      {composite.status === 'DRAFT' && (
                        <button 
                          onClick={() => handleSubmit(composite.id)} 
                          disabled={submitMutation.isPending}
                          className="btn btn-sm"
                          style={{ 
                            background: '#3b82f6', 
                            color: 'white', 
                            border: 'none',
                            padding: '0.25rem 0.5rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.25rem'
                          }}
                        >
                          <Send size={14} /> Enviar
                        </button>
                      )}
                      {composite.status === 'PENDING_APPROVAL' && (
                        <>
                          <button 
                            onClick={() => handleApprove(composite.id)} 
                            disabled={approveMutation.isPending}
                            className="btn btn-sm"
                            style={{ 
                              background: '#10b981', 
                              color: 'white', 
                              border: 'none',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.25rem'
                            }}
                          >
                            <CheckCircle size={14} /> Aprobar
                          </button>
                          <button 
                            onClick={() => handleReject(composite.id)} 
                            disabled={rejectMutation.isPending}
                            className="btn btn-sm"
                            style={{ 
                              background: '#ef4444', 
                              color: 'white', 
                              border: 'none',
                              padding: '0.25rem 0.5rem',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '0.25rem'
                            }}
                          >
                            <XCircle size={14} /> Rechazar
                          </button>
                        </>
                      )}
                      <Link to={`/composites/${composite.id}`} className="btn-link" style={{ fontSize: '0.75rem' }}>
                        Ver detalles
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">
            <FileCheck2 size={48} />
            <h3>No hay composites pendientes</h3>
            <p>Los composites aparecerán aquí cuando estén en estado Draft o Pendiente de Aprobación</p>
          </div>
        )}
      </div>

      {sortedComposites && sortedComposites.filter(c => c.status === 'PENDING_APPROVAL').length > 0 && (
        <div className="card" style={{ background: '#fffbeb', borderLeft: '4px solid #f59e0b' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <CheckCircle size={24} style={{ color: '#f59e0b' }} />
            <div>
              <p style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                {sortedComposites.filter(c => c.status === 'PENDING_APPROVAL').length} composites pendientes de aprobación
              </p>
              <p style={{ fontSize: '0.875rem', color: '#92400e' }}>
                Revisa y aprueba los composites que están esperando tu decisión
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Workflows