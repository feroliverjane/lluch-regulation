import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { compositesApi, materialsApi } from '../services/api'
import { ArrowLeft, FileCheck2, CheckCircle, XCircle, Send } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const CompositeDetail = () => {
  const { id } = useParams<{ id: string }>()
  const compositeId = parseInt(id || '0')
  const queryClient = useQueryClient()

  const { data: composite, isLoading } = useQuery({
    queryKey: ['composite', compositeId],
    queryFn: () => compositesApi.getById(compositeId),
  })

  const { data: material } = useQuery({
    queryKey: ['material', composite?.material_id],
    queryFn: () => materialsApi.getById(composite!.material_id),
    enabled: !!composite?.material_id,
  })

  // Mutaciones para acciones de aprobación
  const submitMutation = useMutation({
    mutationFn: async () => {
      return await compositesApi.submitForApproval(compositeId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['composite', compositeId] })
      queryClient.invalidateQueries({ queryKey: ['all-composites'] })
      queryClient.invalidateQueries({ queryKey: ['all-composites-for-approval'] })
      alert('✅ Composite enviado para aprobación')
    },
    onError: (error: any) => {
      alert('❌ Error al enviar para aprobación: ' + (error.message || 'Error desconocido'))
    }
  })

  const approveMutation = useMutation({
    mutationFn: async () => {
      return await compositesApi.approve(compositeId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['composite', compositeId] })
      queryClient.invalidateQueries({ queryKey: ['all-composites'] })
      queryClient.invalidateQueries({ queryKey: ['all-composites-for-approval'] })
      alert('✅ Composite aprobado exitosamente')
    },
    onError: (error: any) => {
      alert('❌ Error al aprobar composite: ' + (error.message || 'Error desconocido'))
    }
  })

  const rejectMutation = useMutation({
    mutationFn: async () => {
      return await compositesApi.reject(compositeId, 'Rechazado desde la interfaz web')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['composite', compositeId] })
      queryClient.invalidateQueries({ queryKey: ['all-composites'] })
      queryClient.invalidateQueries({ queryKey: ['all-composites-for-approval'] })
      alert('✅ Composite rechazado')
    },
    onError: (error: any) => {
      alert('❌ Error al rechazar composite: ' + (error.message || 'Error desconocido'))
    }
  })

  const handleSubmitForApproval = () => {
    if (confirm('¿Enviar este composite para aprobación?')) {
      submitMutation.mutate()
    }
  }

  const handleApprove = () => {
    if (confirm('¿Aprobar este composite?')) {
      approveMutation.mutate()
    }
  }

  const handleReject = () => {
    if (confirm('¿Rechazar este composite?')) {
      rejectMutation.mutate()
    }
  }

  if (isLoading) {
    return <div className="loading-container">Cargando...</div>
  }

  if (!composite) {
    return <div className="error-container">Composite no encontrado</div>
  }

  // Prepare chart data
  const chartData = composite.components
    .sort((a, b) => b.percentage - a.percentage)
    .slice(0, 10) // Top 10 components
    .map(comp => ({
      name: comp.component_name.length > 20 
        ? comp.component_name.substring(0, 20) + '...' 
        : comp.component_name,
      percentage: parseFloat(comp.percentage.toFixed(2)),
      type: comp.component_type
    }))

  const getStatusBadge = (status: string) => {
    const badges: Record<string, { class: string; text: string }> = {
      DRAFT: { class: 'badge-info', text: 'Borrador' },
      PENDING_APPROVAL: { class: 'badge-warning', text: 'Pendiente' },
      APPROVED: { class: 'badge-success', text: 'Aprobado' },
      REJECTED: { class: 'badge-error', text: 'Rechazado' },
      ARCHIVED: { class: 'badge-info', text: 'Archivado' },
    }
    const badge = badges[status] || { class: 'badge-info', text: status }
    return <span className={`badge ${badge.class}`}>{badge.text}</span>
  }

  return (
    <div>
      <Link 
        to={`/materials/${composite.material_id}`} 
        className="link" 
        style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}
      >
        <ArrowLeft size={20} />
        Volver al material
      </Link>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ background: '#10b98120', padding: '1rem', borderRadius: '12px', color: '#10b981' }}>
              <FileCheck2 size={32} />
            </div>
            <div>
              <h1 style={{ fontSize: '1.875rem', marginBottom: '0.25rem' }}>
                {material?.name} - Versión {composite.version}
              </h1>
              <p style={{ color: '#6b7280' }}>
                Composite #{composite.id} | {material?.reference_code}
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexDirection: 'column', alignItems: 'flex-end' }}>
            {getStatusBadge(composite.status)}
            <span className="badge badge-info">{composite.origin}</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
          <div>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Componentes</p>
            <p style={{ fontWeight: 500, fontSize: '1.25rem' }}>{composite.components.length}</p>
          </div>
          <div>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Fecha de creación</p>
            <p style={{ fontWeight: 500 }}>
              {new Date(composite.created_at).toLocaleDateString('es-ES')}
            </p>
          </div>
          {composite.approved_at && (
            <div>
              <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.25rem' }}>Fecha de aprobación</p>
              <p style={{ fontWeight: 500 }}>
                {new Date(composite.approved_at).toLocaleDateString('es-ES')}
              </p>
            </div>
          )}
        </div>

        {composite.notes && (
          <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: '8px', marginBottom: '1.5rem' }}>
            <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.5rem' }}>Notas</p>
            <p>{composite.notes}</p>
          </div>
        )}

        {composite.status === 'DRAFT' && (
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
            <button 
              className="btn btn-primary" 
              onClick={handleSubmitForApproval}
              disabled={submitMutation.isPending}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <Send size={20} />
              {submitMutation.isPending ? 'Enviando...' : 'Enviar para Aprobación'}
            </button>
          </div>
        )}

        {composite.status === 'PENDING_APPROVAL' && (
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
            <button 
              className="btn btn-success" 
              onClick={handleApprove}
              disabled={approveMutation.isPending}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <CheckCircle size={20} />
              {approveMutation.isPending ? 'Aprobando...' : 'Aprobar'}
            </button>
            <button 
              className="btn btn-danger" 
              onClick={handleReject}
              disabled={rejectMutation.isPending}
              style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
            >
              <XCircle size={20} />
              {rejectMutation.isPending ? 'Rechazando...' : 'Rechazar'}
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>Distribución de Componentes</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
            <YAxis label={{ value: 'Porcentaje (%)', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="percentage" fill="#3b82f6" name="Porcentaje" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: '1rem' }}>
          Componentes ({composite.components.length})
        </h2>
        <table className="table">
          <thead>
            <tr>
              <th>Componente</th>
              <th>CAS Number</th>
              <th>Porcentaje (%)</th>
              <th>Tipo</th>
              <th>Confianza</th>
            </tr>
          </thead>
          <tbody>
            {composite.components
              .sort((a, b) => b.percentage - a.percentage)
              .map((component) => (
                <tr key={component.id}>
                  <td style={{ fontWeight: 500 }}>{component.component_name}</td>
                  <td><code>{component.cas_number || 'N/A'}</code></td>
                  <td>{component.percentage.toFixed(2)}%</td>
                  <td>
                    <span className={`badge ${
                      component.component_type === 'COMPONENT' ? 'badge-info' : 'badge-warning'
                    }`}>
                      {component.component_type === 'COMPONENT' ? 'Componente' : 'Impureza'}
                    </span>
                  </td>
                  <td>
                    {component.confidence_level 
                      ? `${component.confidence_level.toFixed(0)}%`
                      : '-'
                    }
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default CompositeDetail






