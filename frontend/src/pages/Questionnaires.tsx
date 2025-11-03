import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

interface Questionnaire {
  id: number;
  material_id: number;
  supplier_code: string;
  questionnaire_type: string;
  version: number;
  status: string;
  ai_risk_score?: number;
  ai_recommendation?: string;
  created_at: string;
  submitted_at?: string;
  approved_at?: string;
}

interface Material {
  id: number;
  reference_code: string;
  name: string;
}

export default function Questionnaires() {
  const [questionnaires, setQuestionnaires] = useState<Questionnaire[]>([]);
  const [materials, setMaterials] = useState<{ [key: number]: Material }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');

  useEffect(() => {
    loadQuestionnaires();
  }, [statusFilter]);

  const loadQuestionnaires = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (statusFilter) {
        params.status_filter = statusFilter;
      }
      
      const response = await api.get('/questionnaires', { params });
      setQuestionnaires(response.data);
      
      // Load materials
      const materialIds = [...new Set(response.data.map((q: Questionnaire) => q.material_id))];
      const materialPromises = materialIds.map(id => api.get(`/materials/${id}`));
      const materialResponses = await Promise.all(materialPromises);
      
      const materialsMap: { [key: number]: Material } = {};
      materialResponses.forEach(res => {
        materialsMap[res.data.id] = res.data;
      });
      setMaterials(materialsMap);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading questionnaires');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusMap: { [key: string]: string } = {
      'DRAFT': 'badge-secondary',
      'SUBMITTED': 'badge-info',
      'IN_REVIEW': 'badge-warning',
      'APPROVED': 'badge-success',
      'REJECTED': 'badge-danger',
      'REQUIRES_REVISION': 'badge-warning'
    };
    return statusMap[status] || 'badge-secondary';
  };

  const getRiskBadge = (score: number) => {
    if (score >= 70) return 'badge-danger';
    if (score >= 40) return 'badge-warning';
    return 'badge-success';
  };

  if (loading) return <div className="loading">Loading questionnaires...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div style={{ width: '100%', maxWidth: '100%' }}>
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <h1>Cuestionarios de Homologación</h1>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Link to="/questionnaires/new" className="btn-primary">
            Nuevo Cuestionario
          </Link>
          <Link to="/questionnaires/import" className="btn-secondary">
            Importar JSON
          </Link>
        </div>
      </div>

      {/* Summary Stats */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '16px', 
        marginBottom: '24px' 
      }}>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '14px', color: '#6b7280' }}>Total</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px' }}>{questionnaires.length}</div>
        </div>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '14px', color: '#6b7280' }}>En Revisión</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px', color: '#f59e0b' }}>
            {questionnaires.filter(q => q.status === 'IN_REVIEW').length}
          </div>
        </div>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '14px', color: '#6b7280' }}>Aprobados</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px', color: '#10b981' }}>
            {questionnaires.filter(q => q.status === 'APPROVED').length}
          </div>
        </div>
        <div className="card" style={{ padding: '16px' }}>
          <div style={{ fontSize: '14px', color: '#6b7280' }}>Borradores</div>
          <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '4px', color: '#6b7280' }}>
            {questionnaires.filter(q => q.status === 'DRAFT').length}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '24px', padding: '16px' }}>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <label style={{ fontWeight: '500' }}>Estado:</label>
          <select
            className="select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}
          >
            <option value="">Todos</option>
            <option value="DRAFT">Borrador</option>
            <option value="SUBMITTED">Enviado</option>
            <option value="IN_REVIEW">En Revisión</option>
            <option value="APPROVED">Aprobado</option>
            <option value="REJECTED">Rechazado</option>
            <option value="REQUIRES_REVISION">Requiere Revisión</option>
          </select>
        </div>
      </div>

      {/* Questionnaires Table */}
      <div className="card" style={{ padding: '1rem', width: '100%', overflow: 'visible' }}>
        <table className="table" style={{ tableLayout: 'fixed', width: '100%', margin: 0 }}>
          <thead>
            <tr>
              <th style={{ width: '5%', padding: '8px', fontSize: '0.75rem' }}>ID</th>
              <th style={{ width: '18%', padding: '8px', fontSize: '0.75rem' }}>Material</th>
              <th style={{ width: '10%', padding: '8px', fontSize: '0.75rem' }}>Proveedor</th>
              <th style={{ width: '10%', padding: '8px', fontSize: '0.75rem' }}>Tipo</th>
              <th style={{ width: '6%', padding: '8px', fontSize: '0.75rem' }}>Versión</th>
              <th style={{ width: '10%', padding: '8px', fontSize: '0.75rem' }}>Estado</th>
              <th style={{ width: '8%', padding: '8px', fontSize: '0.75rem' }}>Riesgo IA</th>
              <th style={{ width: '12%', padding: '8px', fontSize: '0.75rem' }}>Recomendación IA</th>
              <th style={{ width: '13%', padding: '8px', fontSize: '0.75rem' }}>Fecha Creación</th>
              <th style={{ width: '8%', padding: '8px', fontSize: '0.75rem' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {questionnaires.length === 0 ? (
              <tr>
                <td colSpan={10} style={{ textAlign: 'center', padding: '24px', color: '#6b7280' }}>
                  No hay cuestionarios disponibles
                </td>
              </tr>
            ) : (
              questionnaires.map((questionnaire) => (
                <tr key={questionnaire.id}>
                  <td style={{ padding: '8px', fontSize: '0.75rem' }}>{questionnaire.id}</td>
                  <td style={{ padding: '8px' }}>
                    {materials[questionnaire.material_id] ? (
                      <div>
                        <div style={{ fontWeight: '500', fontSize: '0.75rem', wordBreak: 'break-word', lineHeight: '1.3' }}>
                          {materials[questionnaire.material_id].reference_code}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: '#6b7280', wordBreak: 'break-word', lineHeight: '1.2', marginTop: '2px' }}>
                          {materials[questionnaire.material_id].name.length > 30 
                            ? materials[questionnaire.material_id].name.substring(0, 30) + '...'
                            : materials[questionnaire.material_id].name}
                        </div>
                      </div>
                    ) : (
                      <span style={{ fontSize: '0.75rem' }}>#{questionnaire.material_id}</span>
                    )}
                  </td>
                  <td style={{ padding: '8px', fontSize: '0.75rem', wordBreak: 'break-word' }}>
                    {questionnaire.supplier_code.length > 12 
                      ? questionnaire.supplier_code.substring(0, 12) + '...'
                      : questionnaire.supplier_code}
                  </td>
                  <td style={{ padding: '8px' }}>
                    <span className={`badge ${questionnaire.questionnaire_type === 'INITIAL_HOMOLOGATION' ? 'badge-info' : 'badge-secondary'}`} style={{ fontSize: '0.7rem', padding: '2px 6px' }}>
                      {questionnaire.questionnaire_type === 'INITIAL_HOMOLOGATION' ? 'Inicial' : 'Rehomologación'}
                    </span>
                  </td>
                  <td style={{ padding: '8px', fontSize: '0.75rem' }}>v{questionnaire.version}</td>
                  <td style={{ padding: '8px' }}>
                    <span className={`badge ${getStatusBadge(questionnaire.status)}`} style={{ fontSize: '0.7rem', padding: '2px 6px' }}>
                      {questionnaire.status}
                    </span>
                  </td>
                  <td style={{ padding: '8px' }}>
                    {questionnaire.ai_risk_score !== null && questionnaire.ai_risk_score !== undefined ? (
                      <span className={`badge ${getRiskBadge(questionnaire.ai_risk_score)}`} style={{ fontSize: '0.7rem', padding: '2px 6px' }}>
                        {questionnaire.ai_risk_score}
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>-</span>
                    )}
                  </td>
                  <td style={{ padding: '8px' }}>
                    {questionnaire.ai_recommendation ? (
                      <span className={`badge ${
                        questionnaire.ai_recommendation === 'APPROVE' ? 'badge-success' :
                        questionnaire.ai_recommendation === 'REJECT' ? 'badge-danger' :
                        'badge-warning'
                      }`} style={{ fontSize: '0.7rem', padding: '2px 6px' }}>
                        {questionnaire.ai_recommendation}
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>-</span>
                    )}
                  </td>
                  <td style={{ padding: '8px', fontSize: '0.7rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {new Date(questionnaire.created_at).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })}
                  </td>
                  <td style={{ padding: '8px' }}>
                    <Link to={`/questionnaires/${questionnaire.id}`} className="link" style={{ fontSize: '0.75rem' }}>
                      Ver
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

