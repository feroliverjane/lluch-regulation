import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';

interface Questionnaire {
  id: number;
  material_id: number;
  supplier_code: string;
  questionnaire_type: string;
  version: number;
  previous_version_id?: number;
  status: string;
  responses: { [key: string]: any };
  ai_risk_score?: number;
  ai_summary?: string;
  ai_recommendation?: string;
  created_at: string;
  submitted_at?: string;
  reviewed_at?: string;
  approved_at?: string;
}

interface Material {
  id: number;
  reference_code: string;
  name: string;
  supplier: string;
}

interface Validation {
  id: number;
  validation_type: string;
  field_name: string;
  expected_value?: string;
  actual_value?: string;
  deviation_percentage?: number;
  severity: string;
  requires_action: boolean;
  message?: string;
  created_at: string;
}

interface Incident {
  id: number;
  field_name: string;
  issue_description: string;
  status: string;
  resolution_action: string;
  override_justification?: string;
  resolution_notes?: string;
  created_at: string;
  resolved_at?: string;
}

export default function QuestionnaireDetail() {
  const { id } = useParams<{ id: string }>();
  const [questionnaire, setQuestionnaire] = useState<Questionnaire | null>(null);
  const [material, setMaterial] = useState<Material | null>(null);
  const [validations, setValidations] = useState<Validation[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load questionnaire
      const qResponse = await api.get(`/questionnaires/${id}`);
      setQuestionnaire(qResponse.data);
      
      // Load material
      const mResponse = await api.get(`/materials/${qResponse.data.material_id}`);
      setMaterial(mResponse.data);
      
      // Load validations
      const vResponse = await api.get(`/questionnaires/${id}/validations`);
      setValidations(vResponse.data);
      
      // Load incidents
      const iResponse = await api.get(`/questionnaires/${id}/incidents`);
      setIncidents(iResponse.data);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading questionnaire');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!confirm('¿Está seguro de que desea aprobar este cuestionario?')) return;
    
    try {
      setActionLoading(true);
      await api.post(`/questionnaires/${id}/approve`);
      await loadData();
      alert('Cuestionario aprobado exitosamente');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al aprobar cuestionario');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!confirm('¿Está seguro de que desea rechazar este cuestionario?')) return;
    
    try {
      setActionLoading(true);
      await api.post(`/questionnaires/${id}/reject`);
      await loadData();
      alert('Cuestionario rechazado');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al rechazar cuestionario');
    } finally {
      setActionLoading(false);
    }
  };

  const handleOverrideIncident = async (incidentId: number) => {
    const justification = prompt('Por favor, ingrese la justificación para anular este incidente:');
    if (!justification || justification.trim().length < 10) {
      alert('La justificación debe tener al menos 10 caracteres');
      return;
    }
    
    try {
      await api.post(`/questionnaires/incidents/${incidentId}/override`, {
        justification: justification.trim()
      });
      await loadData();
      alert('Incidente anulado exitosamente');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al anular incidente');
    }
  };

  const handleEscalateIncident = async (incidentId: number) => {
    if (!confirm('¿Desea escalar este incidente al proveedor?')) return;
    
    try {
      await api.post(`/questionnaires/incidents/${incidentId}/escalate`, {});
      await loadData();
      alert('Incidente escalado al proveedor');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al escalar incidente');
    }
  };

  const getSeverityBadge = (severity: string) => {
    const map: { [key: string]: string } = {
      'INFO': 'badge-info',
      'WARNING': 'badge-warning',
      'CRITICAL': 'badge-danger'
    };
    return map[severity] || 'badge-secondary';
  };

  const getStatusBadge = (status: string) => {
    const map: { [key: string]: string } = {
      'DRAFT': 'badge-secondary',
      'SUBMITTED': 'badge-info',
      'IN_REVIEW': 'badge-warning',
      'APPROVED': 'badge-success',
      'REJECTED': 'badge-danger',
      'REQUIRES_REVISION': 'badge-warning'
    };
    return map[status] || 'badge-secondary';
  };

  const getIncidentStatusBadge = (status: string) => {
    const map: { [key: string]: string } = {
      'OPEN': 'badge-danger',
      'ESCALATED_TO_SUPPLIER': 'badge-warning',
      'RESOLVED': 'badge-success',
      'OVERRIDDEN': 'badge-info'
    };
    return map[status] || 'badge-secondary';
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  if (loading) return <div className="loading">Cargando cuestionario...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!questionnaire || !material) return <div className="error">Cuestionario no encontrado</div>;

  const openIncidents = incidents.filter(i => i.status === 'OPEN').length;

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/questionnaires" className="link" style={{ marginBottom: '8px', display: 'inline-block' }}>
            ← Volver a Cuestionarios
          </Link>
          <h1>Cuestionario #{questionnaire.id}</h1>
          <p style={{ color: '#6b7280', marginTop: '4px' }}>
            {material.reference_code} - {material.name}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {questionnaire.status === 'IN_REVIEW' && (
            <>
              <button 
                onClick={handleReject} 
                className="btn-secondary"
                disabled={actionLoading}
              >
                Rechazar
              </button>
              <button 
                onClick={handleApprove} 
                className="btn-primary"
                disabled={actionLoading || openIncidents > 0}
                title={openIncidents > 0 ? `Hay ${openIncidents} incidente(s) abierto(s)` : ''}
              >
                Aprobar
              </button>
            </>
          )}
        </div>
      </div>

      {/* Status Alert */}
      {openIncidents > 0 && questionnaire.status === 'IN_REVIEW' && (
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#fef2f2', 
          border: '1px solid #fecaca',
          borderRadius: '6px',
          marginBottom: '24px'
        }}>
          <strong>⚠️ Atención:</strong> Este cuestionario tiene {openIncidents} incidente(s) crítico(s) sin resolver.
          Debe resolverlos o anularlos antes de aprobar.
        </div>
      )}

      {/* Basic Info */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h2 style={{ marginTop: 0 }}>Información General</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>Material</div>
            <div style={{ fontWeight: '500', marginTop: '4px' }}>
              <Link to={`/materials/${material.id}`} className="link">
                {material.reference_code}
              </Link>
            </div>
            <div style={{ fontSize: '14px', color: '#6b7280' }}>{material.name}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>Proveedor</div>
            <div style={{ fontWeight: '500', marginTop: '4px' }}>{questionnaire.supplier_code}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>Tipo</div>
            <div style={{ marginTop: '4px' }}>
              <span className={`badge ${questionnaire.questionnaire_type === 'INITIAL_HOMOLOGATION' ? 'badge-info' : 'badge-secondary'}`}>
                {questionnaire.questionnaire_type === 'INITIAL_HOMOLOGATION' ? 'Homologación Inicial' : 'Rehomologación'}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>Versión</div>
            <div style={{ fontWeight: '500', marginTop: '4px' }}>v{questionnaire.version}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>Estado</div>
            <div style={{ marginTop: '4px' }}>
              <span className={`badge ${getStatusBadge(questionnaire.status)}`}>
                {questionnaire.status}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>Fecha Creación</div>
            <div style={{ fontWeight: '500', marginTop: '4px', fontSize: '14px' }}>
              {formatDate(questionnaire.created_at)}
            </div>
          </div>
        </div>
      </div>

      {/* AI Analysis */}
      {questionnaire.ai_risk_score !== null && questionnaire.ai_risk_score !== undefined && (
        <div className="card" style={{ marginBottom: '24px', backgroundColor: '#f9fafb' }}>
          <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px', color: '#111827' }}>
            🤖 Análisis de IA
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '24px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '14px', color: '#374151', marginBottom: '8px', fontWeight: '500' }}>Puntuación de Riesgo</div>
              <div style={{ 
                fontSize: '48px', 
                fontWeight: 'bold',
                color: questionnaire.ai_risk_score >= 70 ? '#ef4444' : 
                       questionnaire.ai_risk_score >= 40 ? '#f59e0b' : '#10b981'
              }}>
                {questionnaire.ai_risk_score}
              </div>
              <div style={{ fontSize: '12px', color: '#374151', fontWeight: '500' }}>de 100</div>
              {questionnaire.ai_recommendation && (
                <div style={{ marginTop: '12px' }}>
                  <span className={`badge ${
                    questionnaire.ai_recommendation === 'APPROVE' ? 'badge-success' :
                    questionnaire.ai_recommendation === 'REJECT' ? 'badge-danger' :
                    'badge-warning'
                  }`}>
                    {questionnaire.ai_recommendation}
                  </span>
                </div>
              )}
            </div>
            <div>
              <div style={{ fontSize: '14px', color: '#374151', marginBottom: '8px', fontWeight: '500' }}>Resumen del Análisis</div>
              <div style={{ 
                fontSize: '14px', 
                lineHeight: '1.6',
                padding: '12px',
                backgroundColor: 'white',
                borderRadius: '6px',
                border: '1px solid #e5e7eb',
                color: '#111827'
              }}>
                {questionnaire.ai_summary}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Validations */}
      {validations.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0 }}>Validaciones ({validations.length})</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Campo</th>
                <th>Tipo</th>
                <th>Esperado</th>
                <th>Actual</th>
                <th>Desviación</th>
                <th>Severidad</th>
                <th>Mensaje</th>
              </tr>
            </thead>
            <tbody>
              {validations.map((validation) => (
                <tr key={validation.id}>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{validation.field_name}</td>
                  <td>
                    <span className="badge badge-secondary" style={{ fontSize: '11px' }}>
                      {validation.validation_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td>{validation.expected_value || '-'}</td>
                  <td>{validation.actual_value || '-'}</td>
                  <td>
                    {validation.deviation_percentage !== null && validation.deviation_percentage !== undefined ? (
                      <span style={{ 
                        fontWeight: '500',
                        color: validation.deviation_percentage >= 10 ? '#ef4444' : 
                               validation.deviation_percentage >= 5 ? '#f59e0b' : '#6b7280'
                      }}>
                        {validation.deviation_percentage.toFixed(1)}%
                      </span>
                    ) : '-'}
                  </td>
                  <td>
                    <span className={`badge ${getSeverityBadge(validation.severity)}`}>
                      {validation.severity}
                    </span>
                  </td>
                  <td style={{ fontSize: '13px', maxWidth: '300px' }}>{validation.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Incidents */}
      {incidents.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0 }}>Incidentes ({incidents.length})</h2>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Campo</th>
                <th>Descripción</th>
                <th>Estado</th>
                <th>Acción</th>
                <th>Justificación</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((incident) => (
                <tr key={incident.id}>
                  <td>#{incident.id}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px' }}>{incident.field_name}</td>
                  <td style={{ fontSize: '13px', maxWidth: '250px' }}>{incident.issue_description}</td>
                  <td>
                    <span className={`badge ${getIncidentStatusBadge(incident.status)}`}>
                      {incident.status}
                    </span>
                  </td>
                  <td>
                    <span className="badge badge-secondary" style={{ fontSize: '11px' }}>
                      {incident.resolution_action}
                    </span>
                  </td>
                  <td style={{ fontSize: '12px', maxWidth: '200px' }}>
                    {incident.override_justification || incident.resolution_notes || '-'}
                  </td>
                  <td>
                    {incident.status === 'OPEN' && (
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          onClick={() => handleEscalateIncident(incident.id)}
                          className="btn-secondary"
                          style={{ fontSize: '12px', padding: '4px 8px' }}
                        >
                          Escalar
                        </button>
                        <button 
                          onClick={() => handleOverrideIncident(incident.id)}
                          className="btn-primary"
                          style={{ fontSize: '12px', padding: '4px 8px' }}
                        >
                          Anular
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Responses */}
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Respuestas del Cuestionario ({Object.keys(questionnaire.responses).length})</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
          {Object.entries(questionnaire.responses).map(([key, value]) => (
            <div
              key={key}
              style={{
                padding: '12px',
                backgroundColor: '#f9fafb',
                borderRadius: '6px',
                border: '1px solid #e5e7eb',
              }}
            >
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px', fontFamily: 'monospace' }}>
                {key}
              </div>
              <div style={{ fontWeight: '500', wordBreak: 'break-word', color: '#111827' }}>
                {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

