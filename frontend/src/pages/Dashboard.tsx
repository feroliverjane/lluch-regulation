import { useQuery } from '@tanstack/react-query'
import { materialsApi, workflowsApi } from '../services/api'
import { Package, FileCheck2, Clock, CheckCircle } from 'lucide-react'
import './Dashboard.css'

const Dashboard = () => {
  const { data: materials } = useQuery({
    queryKey: ['materials'],
    queryFn: () => materialsApi.getAll(),
  })

  const { data: workflows } = useQuery({
    queryKey: ['workflows', 'pending'],
    queryFn: () => workflowsApi.getAll({ status_filter: 'PENDING' }),
  })

  const stats = [
    {
      label: 'Materiales Activos',
      value: materials?.filter(m => m.is_active).length || 0,
      icon: Package,
      color: '#3b82f6',
    },
    {
      label: 'Aprobaciones Pendientes',
      value: workflows?.length || 0,
      icon: Clock,
      color: '#f59e0b',
    },
    {
      label: 'Composites Este Mes',
      value: 0, // Placeholder
      icon: FileCheck2,
      color: '#10b981',
    },
    {
      label: 'Análisis Procesados',
      value: 0, // Placeholder
      icon: CheckCircle,
      color: '#8b5cf6',
    },
  ]

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard</h1>
        <p>Resumen del sistema de gestión de composites</p>
      </div>

      <div className="stats-grid">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} className="stat-card">
              <div className="stat-icon" style={{ background: `${stat.color}20`, color: stat.color }}>
                <Icon size={24} />
              </div>
              <div className="stat-content">
                <p className="stat-label">{stat.label}</p>
                <p className="stat-value">{stat.value}</p>
              </div>
            </div>
          )
        })}
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <h2>Materiales Recientes</h2>
          {materials && materials.length > 0 ? (
            <div className="recent-list">
              {materials.slice(0, 5).map((material) => (
                <div key={material.id} className="recent-item">
                  <div>
                    <p className="recent-title">{material.name}</p>
                    <p className="recent-subtitle">{material.reference_code}</p>
                  </div>
                  <span className={`badge ${material.is_active ? 'badge-success' : 'badge-error'}`}>
                    {material.is_active ? 'Activo' : 'Inactivo'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state">No hay materiales registrados</p>
          )}
        </div>

        <div className="card">
          <h2>Aprobaciones Pendientes</h2>
          {workflows && workflows.length > 0 ? (
            <div className="recent-list">
              {workflows.slice(0, 5).map((workflow) => (
                <div key={workflow.id} className="recent-item">
                  <div>
                    <p className="recent-title">Composite #{workflow.composite_id}</p>
                    <p className="recent-subtitle">
                      {new Date(workflow.created_at).toLocaleDateString('es-ES')}
                    </p>
                  </div>
                  <span className="badge badge-warning">Pendiente</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state">No hay aprobaciones pendientes</p>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard






