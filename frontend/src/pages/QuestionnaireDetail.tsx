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
  template_id?: number;
  status: string;
  responses: { [key: string]: any };
  ai_risk_score?: number;
  ai_summary?: string;
  ai_recommendation?: string;
  ai_coherence_score?: number;
  ai_coherence_details?: Array<{ field: string; issue: string; severity: string }>;
  attached_documents?: Array<{ filename: string; path: string; upload_date: string }>;
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

interface QuestionField {
  fieldCode: string;
  fieldName: string;
  fieldType: string;
  tab: number;
  section: number;
  required: boolean;
  critical: boolean;
}

interface Template {
  id: number;
  name: string;
  questions_schema: QuestionField[];
  section_names?: { [key: string]: string };
  tab_names?: { [key: string]: string };
}

export default function QuestionnaireDetail() {
  const { id } = useParams<{ id: string }>();
  const [questionnaire, setQuestionnaire] = useState<Questionnaire | null>(null);
  const [material, setMaterial] = useState<Material | null>(null);
  const [template, setTemplate] = useState<Template | null>(null);
  const [validations, setValidations] = useState<Validation[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [currentTab, setCurrentTab] = useState<number>(1);
  
  // New AI features states
  const [coherenceValidating, setCoherenceValidating] = useState(false);
  const [uploadingDocs, setUploadingDocs] = useState(false);
  const [extractingComposite, setExtractingComposite] = useState(false);
  const [compositeInfo, setCompositeInfo] = useState<any>(null);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [blueLine, setBlueLine] = useState<any>(null);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load questionnaire
      const qResponse = await api.get(`/questionnaires/${id}`);
      setQuestionnaire(qResponse.data);
      
      // Load template if available
      if (qResponse.data.template_id) {
        try {
          const templateRes = await api.get(`/questionnaire-templates/${qResponse.data.template_id}`);
          setTemplate(templateRes.data);
          // Set first tab
          if (templateRes.data.questions_schema.length > 0) {
            const firstTab = templateRes.data.questions_schema[0].tab;
            setCurrentTab(firstTab);
          }
        } catch (err) {
          console.warn('Could not load template:', err);
        }
      }
      
      // Load material
      const mResponse = await api.get(`/materials/${qResponse.data.material_id}`);
      setMaterial(mResponse.data);
      
      // Load validations
      const vResponse = await api.get(`/questionnaires/${id}/validations`);
      setValidations(vResponse.data);
      
      // Load incidents
      const iResponse = await api.get(`/questionnaires/${id}/incidents`);
      setIncidents(iResponse.data);
      
      // Try to load composite if exists
      try {
        const compResponse = await api.get(`/questionnaires/${id}/composite`);
        setCompositeInfo(compResponse.data);
      } catch (err) {
        // No composite yet
        setCompositeInfo(null);
      }
      
      // Try to load blue line
      try {
        const blResponse = await api.get(`/blue-line/material/${qResponse.data.material_id}`);
        setBlueLine(blResponse.data);
      } catch (err: any) {
        // No blue line yet - check if it's a 404 (expected) or another error
        if (err.response?.status === 404) {
          setBlueLine(null);
        } else {
          console.error('Error loading blue line:', err);
          setBlueLine(null);
        }
      }
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading questionnaire');
    } finally {
      setLoading(false);
    }
  };

  const handleValidateCoherence = async () => {
    try {
      setCoherenceValidating(true);
      const response = await api.post(`/questionnaires/${id}/validate-coherence`);
      
      // Reload questionnaire to get updated coherence data
      const qResponse = await api.get(`/questionnaires/${id}`);
      setQuestionnaire(qResponse.data);
      
      alert(`Validación completada. Score: ${response.data.coherence_score}/100`);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al validar coherencia');
    } finally {
      setCoherenceValidating(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFiles(e.target.files);
    }
  };

  const handleUploadDocuments = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      alert('Por favor seleccione al menos un archivo PDF');
      return;
    }

    try {
      setUploadingDocs(true);
      const formData = new FormData();
      
      for (let i = 0; i < selectedFiles.length; i++) {
        formData.append('files', selectedFiles[i]);
      }

      await api.post(`/questionnaires/${id}/upload-documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Reload questionnaire
      const qResponse = await api.get(`/questionnaires/${id}`);
      setQuestionnaire(qResponse.data);
      setSelectedFiles(null);
      
      alert('Documentos subidos exitosamente');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al subir documentos');
    } finally {
      setUploadingDocs(false);
    }
  };

  const handleExtractComposite = async () => {
    try {
      setExtractingComposite(true);
      const response = await api.post(`/questionnaires/${id}/extract-composite`);
      
      setCompositeInfo(response.data);
      alert(`Composite extraído: ${response.data.components_count} componentes con ${response.data.extraction_confidence.toFixed(1)}% confianza`);
    } catch (err: any) {
      console.error('Error extracting composite:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Error al extraer composite';
      alert(`Error al extraer composite: ${errorMessage}`);
    } finally {
      setExtractingComposite(false);
    }
  };

  const handleCreateBlueLine = async () => {
    if (!confirm('¿Crear línea azul desde este cuestionario?')) return;
    
    try {
      setActionLoading(true);
      await api.post(`/questionnaires/${id}/create-blue-line`);
      
      // Reload all data to ensure consistency
      await loadData();
      
      alert('Línea azul creada exitosamente');
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al crear línea azul';
      alert(`Error: ${errorMsg}`);
      console.error('Error creating blue line:', err);
    } finally {
      setActionLoading(false);
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

  // Organize fields by tabs and sections (same as QuestionnaireFormDynamic)
  const organizeByTabs = () => {
    if (!template) return {};
    
    const tabs: { [tab: number]: { [section: number]: QuestionField[] } } = {};
    
    template.questions_schema.forEach(field => {
      if (!tabs[field.tab]) tabs[field.tab] = {};
      if (!tabs[field.tab][field.section]) tabs[field.tab][field.section] = [];
      tabs[field.tab][field.section].push(field);
    });
    
    return tabs;
  };

  // Render field value in read-only mode
  const renderFieldValue = (field: QuestionField, responseValue: any) => {
    if (!responseValue && responseValue !== '' && responseValue !== 0) {
      return <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>No respondido</span>;
    }

    // Handle complex response structure (from questionnaire.responses)
    let value = responseValue;
    if (typeof responseValue === 'object' && responseValue !== null) {
      value = responseValue.value || responseValue;
    }

    // Handle "YES|comment" format
    if (typeof value === 'string' && value.includes('|')) {
      const [yesNo, comment] = value.split('|');
      return (
        <div>
          <div style={{ fontWeight: '500', marginBottom: '4px' }}>{yesNo}</div>
          {comment && (
            <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
              {comment}
            </div>
          )}
        </div>
      );
    }

    // Handle JSON arrays (for tables)
    if (typeof value === 'string' && (value.startsWith('[') || value.startsWith('{'))) {
      try {
        const parsed = JSON.parse(value);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return (
            <div style={{ fontSize: '12px', fontFamily: 'monospace' }}>
              {JSON.stringify(parsed, null, 2)}
            </div>
          );
        }
      } catch (e) {
        // Not valid JSON, show as string
      }
    }

    return <span style={{ wordBreak: 'break-word' }}>{String(value)}</span>;
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
          backgroundColor: '#7f1d1d', 
          border: '1px solid #991b1b',
          borderRadius: '6px',
          marginBottom: '24px',
          color: '#fca5a5'
        }}>
          <strong>⚠️ Atención:</strong> Este cuestionario tiene {openIncidents} incidente(s) crítico(s) sin resolver.
          Debe resolverlos o anularlos antes de aprobar.
        </div>
      )}

      {/* Basic Info */}
      <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1f2937', color: 'white' }}>
        <h2 style={{ marginTop: 0, color: 'white' }}>Información General</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Material</div>
            <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>
              <Link to={`/materials/${material.id}`} className="link" style={{ color: '#60a5fa' }}>
                {material.reference_code}
              </Link>
            </div>
            <div style={{ fontSize: '14px', color: '#d1d5db' }}>{material.name}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Proveedor</div>
            <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>{questionnaire.supplier_code}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Tipo</div>
            <div style={{ marginTop: '4px' }}>
              <span className={`badge ${questionnaire.questionnaire_type === 'INITIAL_HOMOLOGATION' ? 'badge-info' : 'badge-secondary'}`}>
                {questionnaire.questionnaire_type === 'INITIAL_HOMOLOGATION' ? 'Homologación Inicial' : 'Rehomologación'}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Versión</div>
            <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>v{questionnaire.version}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Estado</div>
            <div style={{ marginTop: '4px' }}>
              <span className={`badge ${getStatusBadge(questionnaire.status)}`}>
                {questionnaire.status}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Fecha Creación</div>
            <div style={{ fontWeight: '500', marginTop: '4px', fontSize: '14px', color: 'white' }}>
              {formatDate(questionnaire.created_at)}
            </div>
          </div>
        </div>
      </div>

      {/* AI Analysis */}
      {questionnaire.ai_risk_score !== null && questionnaire.ai_risk_score !== undefined && (
        <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1f2937', color: 'white' }}>
          <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'white' }}>
            🤖 Análisis de IA
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '24px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '14px', color: '#d1d5db', marginBottom: '8px', fontWeight: '500' }}>Puntuación de Riesgo</div>
              <div style={{ 
                fontSize: '48px', 
                fontWeight: 'bold',
                color: questionnaire.ai_risk_score >= 70 ? '#ef4444' : 
                       questionnaire.ai_risk_score >= 40 ? '#f59e0b' : '#10b981'
              }}>
                {questionnaire.ai_risk_score}
              </div>
              <div style={{ fontSize: '12px', color: '#d1d5db', fontWeight: '500' }}>de 100</div>
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
              <div style={{ fontSize: '14px', color: '#d1d5db', marginBottom: '8px', fontWeight: '500' }}>Resumen del Análisis</div>
              <div style={{ 
                fontSize: '14px', 
                lineHeight: '1.6',
                padding: '12px',
                backgroundColor: '#111827',
                borderRadius: '6px',
                border: '1px solid #374151',
                color: 'white'
              }}>
                {questionnaire.ai_summary}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Coherence Validation */}
      <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1f2937', color: 'white' }}>
        <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'white' }}>
          ✨ Validación de Coherencia AI
        </h2>
        
        {questionnaire.ai_coherence_score !== null && questionnaire.ai_coherence_score !== undefined ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '24px', marginBottom: '16px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', color: '#d1d5db', marginBottom: '4px' }}>Score de Coherencia</div>
                <div style={{ 
                  fontSize: '36px', 
                  fontWeight: 'bold',
                  color: questionnaire.ai_coherence_score >= 80 ? '#10b981' : 
                         questionnaire.ai_coherence_score >= 60 ? '#f59e0b' : '#ef4444'
                }}>
                  {questionnaire.ai_coherence_score}
                </div>
                <div style={{ fontSize: '12px', color: '#d1d5db' }}>de 100</div>
              </div>
              <div style={{ flex: 1 }}>
                {questionnaire.ai_coherence_details && questionnaire.ai_coherence_details.length > 0 ? (
                  <div>
                    <div style={{ fontSize: '14px', color: '#d1d5db', marginBottom: '8px', fontWeight: '500' }}>
                      Issues Detectados ({questionnaire.ai_coherence_details.length})
                    </div>
                    <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                      {questionnaire.ai_coherence_details.map((issue, idx) => (
                        <div key={idx} style={{
                          padding: '8px 12px',
                          backgroundColor: '#111827',
                          borderRadius: '4px',
                          marginBottom: '8px',
                          borderLeft: `3px solid ${
                            issue.severity === 'critical' ? '#ef4444' :
                            issue.severity === 'warning' ? '#f59e0b' : '#3b82f6'
                          }`
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <span className={`badge ${
                              issue.severity === 'critical' ? 'badge-danger' :
                              issue.severity === 'warning' ? 'badge-warning' : 'badge-info'
                            }`} style={{ fontSize: '10px' }}>
                              {issue.severity.toUpperCase()}
                            </span>
                            <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#9ca3af' }}>
                              {issue.field}
                            </span>
                          </div>
                          <div style={{ fontSize: '13px', color: '#d1d5db' }}>
                            {issue.issue}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div style={{ 
                    padding: '12px', 
                    backgroundColor: '#064e3b',
                    border: '1px solid #065f46',
                    borderRadius: '6px',
                    color: '#6ee7b7'
                  }}>
                    ✓ No se detectaron problemas de coherencia
                  </div>
                )}
              </div>
            </div>
            <button 
              onClick={handleValidateCoherence}
              className="btn-secondary"
              disabled={coherenceValidating}
              style={{ marginTop: '8px' }}
            >
              {coherenceValidating ? 'Validando...' : 'Re-validar Coherencia'}
            </button>
          </div>
        ) : (
          <div>
            <p style={{ color: '#d1d5db', marginBottom: '16px' }}>
              Valida la coherencia lógica del cuestionario con IA. Detecta contradicciones como:
              "100% natural" con "contiene aditivos", "vegano" con "origen animal", etc.
            </p>
            <button 
              onClick={handleValidateCoherence}
              className="btn-primary"
              disabled={coherenceValidating}
            >
              {coherenceValidating ? 'Validando...' : '🤖 Validar Coherencia con IA'}
            </button>
          </div>
        )}
      </div>

      {/* Documents & Composite Extraction */}
      <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1f2937', color: 'white' }}>
        <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'white' }}>
          📄 Documentos y Composite
        </h2>

        {/* Uploaded Documents */}
        {questionnaire.attached_documents && questionnaire.attached_documents.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '14px', color: '#d1d5db', marginBottom: '8px', fontWeight: '500' }}>
              Documentos Subidos ({questionnaire.attached_documents.length})
            </div>
            <div style={{ display: 'grid', gap: '8px' }}>
              {questionnaire.attached_documents.map((doc, idx) => (
                <div key={idx} style={{
                  padding: '8px 12px',
                  backgroundColor: '#111827',
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span style={{ fontSize: '18px' }}>📑</span>
                  <span style={{ fontSize: '13px', color: '#d1d5db' }}>{doc.filename}</span>
                  <span style={{ fontSize: '11px', color: '#9ca3af', marginLeft: 'auto' }}>
                    {new Date(doc.upload_date).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upload Section */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '14px', color: '#d1d5db', marginBottom: '8px', fontWeight: '500' }}>
            Subir Documentos (PDFs)
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={handleFileSelect}
              style={{
                flex: 1,
                padding: '8px',
                backgroundColor: '#111827',
                border: '1px solid #374151',
                borderRadius: '4px',
                color: 'white'
              }}
            />
            <button 
              onClick={handleUploadDocuments}
              className="btn-primary"
              disabled={uploadingDocs || !selectedFiles}
            >
              {uploadingDocs ? 'Subiendo...' : '📤 Subir'}
            </button>
          </div>
        </div>

        {/* Composite Info */}
        {compositeInfo ? (
          <div style={{
            padding: '12px',
            backgroundColor: '#064e3b',
            border: '1px solid #065f46',
            borderRadius: '6px',
            marginBottom: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <span style={{ fontSize: '18px' }}>✓</span>
              <span style={{ fontSize: '14px', fontWeight: '500', color: '#6ee7b7' }}>
                Composite Extraído
              </span>
              <span className="badge badge-info" style={{ marginLeft: 'auto' }}>
                {compositeInfo.composite_type}
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', fontSize: '13px', color: '#6ee7b7' }}>
              <div>
                <div style={{ color: '#9ca3af', fontSize: '11px' }}>ID Composite</div>
                <div>#{compositeInfo.composite_id}</div>
              </div>
              <div>
                <div style={{ color: '#9ca3af', fontSize: '11px' }}>Componentes</div>
                <div>{compositeInfo.components_count}</div>
              </div>
              <div>
                <div style={{ color: '#9ca3af', fontSize: '11px' }}>Confianza</div>
                <div>{compositeInfo.extraction_confidence?.toFixed(1)}%</div>
              </div>
            </div>
            <Link 
              to={`/composites/${compositeInfo.composite_id}`}
              className="btn-secondary"
              style={{ marginTop: '12px', display: 'inline-block', fontSize: '12px' }}
            >
              Ver Composite Detallado
            </Link>
          </div>
        ) : (
          <div>
            <button 
              onClick={handleExtractComposite}
              className="btn-primary"
              disabled={extractingComposite || !questionnaire.attached_documents || questionnaire.attached_documents.length === 0}
              title={!questionnaire.attached_documents || questionnaire.attached_documents.length === 0 ? 'Sube documentos primero' : ''}
            >
              {extractingComposite ? 'Extrayendo...' : '🤖 Extraer Composite con IA'}
            </button>
            <p style={{ fontSize: '12px', color: '#9ca3af', marginTop: '8px' }}>
              La IA extraerá automáticamente la composición química (CAS, nombres, porcentajes) de los PDFs subidos
            </p>
          </div>
        )}
      </div>

      {/* Blue Line Actions */}
      {questionnaire && questionnaire.status === 'APPROVED' && !loading && (
        <>
          {!blueLine ? (
            <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1e3a8a', border: '1px solid #1e40af' }}>
              <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px', color: 'white' }}>
                📘 Crear Línea Azul
              </h2>
              <p style={{ color: '#bfdbfe', marginBottom: '16px' }}>
                Este material no tiene línea azul. Puedes crearla desde este cuestionario aprobado.
                Se aplicarán automáticamente las lógicas del CSV.
              </p>
              <button 
                onClick={handleCreateBlueLine}
                className="btn-primary"
                disabled={actionLoading}
              >
                {actionLoading ? 'Creando...' : '✨ Crear Línea Azul desde Cuestionario'}
              </button>
            </div>
          ) : (
        <div className="card" style={{ marginBottom: '24px', backgroundColor: '#064e3b', border: '1px solid #065f46' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px', color: '#6ee7b7' }}>
                📘 Línea Azul Existente
              </h2>
              <p style={{ color: '#6ee7b7', fontSize: '14px', marginTop: '4px' }}>
                Este material ya tiene línea azul (Tipo: {blueLine.material_type})
              </p>
            </div>
            <Link 
              to={`/blue-line/${blueLine.id}`}
              className="btn-secondary"
            >
              Ver Línea Azul →
            </Link>
          </div>
        </div>
          )}
        </>
      )}

      {/* Validations */}
      {validations.length > 0 && (
        <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1f2937', color: 'white' }}>
          <h2 style={{ marginTop: 0, color: 'white' }}>Validaciones ({validations.length})</h2>
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
        <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1f2937', color: 'white' }}>
          <h2 style={{ marginTop: 0, color: 'white' }}>Incidentes ({incidents.length})</h2>
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

      {/* Responses - Organized by Template */}
      {template ? (
        <div>
          <div className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px' }}>
            <h2 style={{ marginTop: 0, color: 'white' }}>Respuestas del Cuestionario</h2>
            <p style={{ color: '#d1d5db', fontSize: '14px', marginTop: '4px' }}>
              {template.name} - {Object.keys(questionnaire.responses).filter(k => !k.startsWith('_')).length} campos respondidos
            </p>
          </div>

          {/* Tab Navigation */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', gap: '4px', borderBottom: '2px solid #4b5563' }}>
              {Object.keys(organizeByTabs()).map(tab => {
                const tabNum = parseInt(tab);
                const isActive = currentTab === tabNum;
                const tabName = template?.tab_names?.[tab] || `Tab ${tabNum}`;
                return (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setCurrentTab(tabNum)}
                    style={{
                      padding: '12px 24px',
                      border: 'none',
                      borderBottom: isActive ? '3px solid #3b82f6' : '3px solid transparent',
                      background: isActive ? '#374151' : 'transparent',
                      color: isActive ? 'white' : '#9ca3af',
                      fontWeight: isActive ? '600' : '400',
                      cursor: 'pointer',
                      fontSize: '14px'
                    }}
                  >
                    {tabName}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Fields by Section */}
          {Object.entries(organizeByTabs()[currentTab] || {}).map(([sectionNum, fields]) => {
            const sectionFields = fields as QuestionField[];
            const sectionKey = `${currentTab}_${sectionNum}`;
            const sectionName = template?.section_names?.[sectionKey] || `Sección ${sectionNum}`;
            
            return (
              <div key={sectionNum} className="card" style={{ marginBottom: '24px', backgroundColor: '#1f2937', color: 'white' }}>
                <h2 style={{ marginTop: 0, fontSize: '18px', color: 'white' }}>
                  {sectionName}
                  <span style={{ fontSize: '14px', fontWeight: 'normal', color: '#9ca3af', marginLeft: '12px' }}>
                    ({sectionFields.length} campos)
                  </span>
                </h2>
                
                <div style={{ display: 'grid', gap: '20px' }}>
                  {sectionFields.map((field) => {
                    const responseValue = questionnaire.responses[field.fieldCode];
                    const hasValidation = validations.some(v => v.field_name.includes(field.fieldCode));
                    const hasIncident = incidents.some(i => i.field_name === field.fieldCode);
                    
                    return (
                      <div key={field.fieldCode}>
                        <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: 'white' }}>
                          <span style={{ fontWeight: '500' }}>
                            {field.fieldName}
                            {field.required && <span style={{ color: '#ef4444', marginLeft: '4px' }}>*</span>}
                            {field.critical && (
                              <span style={{ 
                                marginLeft: '8px', 
                                fontSize: '11px', 
                                padding: '2px 6px', 
                                backgroundColor: '#7f1d1d',
                                color: '#fca5a5',
                                borderRadius: '4px'
                              }}>
                                CRITICAL
                              </span>
                            )}
                            {hasValidation && (
                              <span style={{ 
                                marginLeft: '8px', 
                                fontSize: '11px', 
                                padding: '2px 6px', 
                                backgroundColor: '#7f1d1d',
                                color: '#fca5a5',
                                borderRadius: '4px'
                              }}>
                                VALIDATION
                              </span>
                            )}
                            {hasIncident && (
                              <span style={{ 
                                marginLeft: '8px', 
                                fontSize: '11px', 
                                padding: '2px 6px', 
                                backgroundColor: '#991b1b',
                                color: '#fca5a5',
                                borderRadius: '4px'
                              }}>
                                INCIDENT
                              </span>
                            )}
                          </span>
                          <span style={{ 
                            fontSize: '11px', 
                            color: '#9ca3af', 
                            fontFamily: 'monospace',
                            marginLeft: '8px'
                          }}>
                            {field.fieldCode}
                          </span>
                        </label>
                        <div style={{
                          padding: '12px',
                          backgroundColor: '#111827',
                          borderRadius: '6px',
                          border: '1px solid #374151',
                          color: 'white',
                          minHeight: '40px',
                          fontSize: '14px'
                        }}>
                          {renderFieldValue(field, responseValue)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Fallback: Simple display if no template */
        <div className="card">
          <h2 style={{ marginTop: 0 }}>Respuestas del Cuestionario ({Object.keys(questionnaire.responses).filter(k => !k.startsWith('_')).length})</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
            {Object.entries(questionnaire.responses)
              .filter(([key]) => !key.startsWith('_'))
              .map(([key, value]) => (
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
      )}
    </div>
  );
}

