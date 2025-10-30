import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import '../components/Layout.css';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface BlueLine {
  id: number;
  material_id: number;
  template_id?: number;
  responses: Record<string, any>;
  blue_line_data: Record<string, any>;
  material_type: 'Z001' | 'Z002';
  composite_id?: number;
  sync_status: 'PENDING' | 'SYNCED' | 'FAILED' | 'NOT_REQUIRED';
  calculated_at: string;
  last_synced_at?: string;
  sync_error_message?: string;
  calculation_metadata?: Record<string, any>;
}

interface Material {
  id: number;
  reference_code: string;
  name: string;
  sap_status?: string;
  supplier: string;
  supplier_code?: string;
}

interface Composite {
  id: number;
  version: number;
  origin: string;
  status: string;
  components: any[];
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

interface MaterialSupplier {
  id: number;
  material_id: number;
  questionnaire_id: number;
  supplier_code: string;
  supplier_name?: string;
  status: string;
  validation_score: number;
  mismatch_fields: any[];
  accepted_mismatches: string[];
  validated_at?: string;
  created_at: string;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api';

export default function BlueLineDetail() {
  const { id, material_id } = useParams<{ id?: string; material_id?: string }>();
  const [blueLine, setBlueLine] = useState<BlueLine | null>(null);
  const [material, setMaterial] = useState<Material | null>(null);
  const [template, setTemplate] = useState<Template | null>(null);
  const [composite, setComposite] = useState<Composite | null>(null);
  const [materialSuppliers, setMaterialSuppliers] = useState<MaterialSupplier[]>([]);
  const [expandedSuppliers, setExpandedSuppliers] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [importing, setImporting] = useState(false);
  const [currentTab, setCurrentTab] = useState<number>(1);

  useEffect(() => {
    fetchBlueLineDetail();
  }, [id, material_id]);

  const fetchBlueLineDetail = async () => {
    try {
      setLoading(true);
      
      // Load Blue Line by material_id (preferred) or by id (backward compatibility)
      let response;
      if (material_id) {
        response = await fetch(`${API_URL}${API_PREFIX}/blue-line/material/${material_id}`);
      } else if (id) {
        // Backward compatibility: support /blue-line/:id
        response = await fetch(`${API_URL}${API_PREFIX}/blue-line/${id}`);
      } else {
        throw new Error('No id or material_id provided');
      }
      
      const data = await response.json();
      setBlueLine(data);

      // Load template if available
      if (data.template_id) {
        try {
          const templateRes = await api.get(`/questionnaire-templates/${data.template_id}`);
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

      // Load composite if available
      if (data.composite_id) {
        try {
          const compositeRes = await api.get(`/composites/${data.composite_id}`);
          setComposite(compositeRes.data);
        } catch (err) {
          console.warn('Could not load composite:', err);
        }
      }

      // Load material
      const matResponse = await fetch(`${API_URL}${API_PREFIX}/materials/${data.material_id}`);
      const materialData = await matResponse.json();
      setMaterial(materialData);

      // Load MaterialSuppliers for this material
      try {
        const suppliersRes = await fetch(`${API_URL}${API_PREFIX}/material-suppliers/by-material/${data.material_id}`);
        if (suppliersRes.ok) {
          const suppliersData = await suppliersRes.json();
          setMaterialSuppliers(suppliersData);
        }
      } catch (err) {
        console.warn('Could not load material suppliers:', err);
      }

      setLoading(false);
    } catch (error) {
      console.error('Error fetching blue line:', error);
      setLoading(false);
    }
  };

  const handleSyncToSAP = async () => {
    if (!blueLine) return;

    setSyncing(true);
    try {
      const response = await fetch(`${API_URL}${API_PREFIX}/blue-line/${blueLine.id}/sync-to-sap`, {
        method: 'POST',
      });
      const result = await response.json();

      if (result.success) {
        alert('Successfully synced to SAP!');
        fetchBlueLineDetail(); // Refresh data
      } else {
        alert(`Sync failed: ${result.message}`);
      }
    } catch (error) {
      console.error('Error syncing to SAP:', error);
      alert('Error syncing to SAP');
    } finally {
      setSyncing(false);
    }
  };

  const handleImportFromSAP = async () => {
    if (!blueLine) return;

    setImporting(true);
    try {
      const response = await fetch(
        `${API_URL}${API_PREFIX}/blue-line/material/${blueLine.material_id}/import-from-sap`,
        {
          method: 'POST',
        }
      );
      const result = await response.json();

      if (result.success) {
        alert('Successfully imported from SAP!');
        fetchBlueLineDetail(); // Refresh data
      } else {
        alert(`Import failed: ${result.message}`);
      }
    } catch (error) {
      console.error('Error importing from SAP:', error);
      alert('Error importing from SAP');
    } finally {
      setImporting(false);
    }
  };

  // Organize fields by tabs and sections (same as QuestionnaireDetail)
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
      return <span style={{ color: '#9ca3af', fontStyle: 'italic' }}>No definido</span>;
    }

    // Handle complex response structure
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

  if (loading) {
    return (
      <div className="loading">Cargando Línea Azul...</div>
    );
  }

  if (!blueLine || !material) {
    return (
      <div className="error">Línea Azul no encontrada</div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/blue-line" className="link" style={{ marginBottom: '8px', display: 'inline-block', color: 'white' }}>
            ← Volver a Líneas Azules
          </Link>
          <h1 style={{ color: 'white' }}>Línea Azul - {material.reference_code}</h1>
          <p style={{ color: '#d1d5db', marginTop: '4px' }}>
            {material.name}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {material?.sap_status === 'Z1' && (
            <>
              <button 
                onClick={handleImportFromSAP} 
                disabled={importing}
                className="btn-secondary"
                style={{ backgroundColor: '#374151', color: 'white', border: '1px solid #4b5563' }}
              >
                {importing ? 'Importando...' : 'Importar de SAP'}
              </button>
              <button 
                onClick={handleSyncToSAP} 
                disabled={syncing}
                className="btn-primary"
              >
                {syncing ? 'Sincronizando...' : 'Sincronizar a SAP'}
              </button>
            </>
          )}
        </div>
      </div>

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
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>ID BlueLine</div>
            <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>#{blueLine.id}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Tipo</div>
            <div style={{ marginTop: '4px' }}>
              <span className={`badge ${blueLine.material_type === 'Z001' ? 'badge-warning' : 'badge-success'}`}>
                {blueLine.material_type === 'Z001' ? 'Z001 - Estimado' : 'Z002 - Homologado'}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Estado Sync</div>
            <div style={{ marginTop: '4px' }}>
              <span className={`badge ${
                blueLine.sync_status === 'SYNCED' ? 'badge-success' :
                blueLine.sync_status === 'FAILED' ? 'badge-danger' :
                blueLine.sync_status === 'PENDING' ? 'badge-warning' :
                'badge-secondary'
              }`}>
                {blueLine.sync_status}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Composite</div>
            <div style={{ marginTop: '4px' }}>
              {blueLine.composite_id ? (
                <Link to={`/composites/${blueLine.composite_id}`} className="link" style={{ color: '#60a5fa' }}>
                  Ver Composite #{blueLine.composite_id}
                </Link>
              ) : (
                <span style={{ color: '#9ca3af' }}>No asociado</span>
              )}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Fecha Cálculo</div>
            <div style={{ fontWeight: '500', marginTop: '4px', fontSize: '14px', color: 'white' }}>
              {new Date(blueLine.calculated_at).toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      {/* Composite Info */}
      {composite && (
        <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1f2937', color: 'white' }}>
          <h2 style={{ marginTop: 0, color: 'white' }}>Composite Asociado</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>ID</div>
              <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>#{composite.id}</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>Versión</div>
              <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>v{composite.version}</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>Origen</div>
              <div style={{ marginTop: '4px' }}>
                <span className="badge badge-secondary">{composite.origin}</span>
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>Componentes</div>
              <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>
                {composite.components?.length || 0} componentes
              </div>
            </div>
          </div>
          {(!composite.components || composite.components.length === 0) && (
            <div style={{ marginTop: '16px', padding: '12px', backgroundColor: '#111827', borderRadius: '6px', border: '1px solid #374151' }}>
              <span style={{ color: '#9ca3af' }}>⚠️ Este composite está vacío. Puede ser rellenado manualmente o importado más tarde.</span>
            </div>
          )}
        </div>
      )}

      {/* Blue Line Data - Organized by Template */}
      {template ? (
        <div>
          <div className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px' }}>
            <h2 style={{ marginTop: 0, color: 'white' }}>Valores Esperados de la Línea Azul</h2>
            <p style={{ color: '#d1d5db', fontSize: '14px', marginTop: '4px' }}>
              {template.name} - {Object.keys(blueLine.responses).filter(k => !k.startsWith('_')).length} campos definidos
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
                    const responseValue = blueLine.responses[field.fieldCode];
                    
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
          <h2 style={{ marginTop: 0 }}>Datos de la Línea Azul ({Object.keys(blueLine.responses || blueLine.blue_line_data || {}).filter(k => !k.startsWith('_')).length})</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
            {Object.entries(blueLine.responses || blueLine.blue_line_data || {})
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

      {/* Material Suppliers Section */}
      <div className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginTop: '24px' }}>
        <h2 style={{ marginTop: 0, color: 'white', marginBottom: '20px' }}>
          Material-Proveedores Asociados ({materialSuppliers.length})
        </h2>

        {materialSuppliers.length === 0 ? (
          <div style={{
            padding: '24px',
            textAlign: 'center',
            color: '#9ca3af',
            backgroundColor: '#111827',
            borderRadius: '6px',
            border: '1px solid #374151'
          }}>
            No hay proveedores asociados a esta Blue Line aún.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {materialSuppliers.map((supplier) => {
              const isExpanded = expandedSuppliers.has(supplier.id);
              
              return (
                <div
                  key={supplier.id}
                  style={{
                    backgroundColor: '#111827',
                    borderRadius: '6px',
                    border: '1px solid #374151',
                    overflow: 'hidden'
                  }}
                >
                  {/* Header - Always visible */}
                  <div
                    onClick={() => {
                      setExpandedSuppliers(prev => {
                        const newSet = new Set(prev);
                        if (newSet.has(supplier.id)) {
                          newSet.delete(supplier.id);
                        } else {
                          newSet.add(supplier.id);
                        }
                        return newSet;
                      });
                    }}
                    style={{
                      padding: '16px',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      backgroundColor: isExpanded ? '#1a1f2e' : '#111827',
                      transition: 'background-color 0.2s'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
                      {isExpanded ? (
                        <ChevronUp size={20} style={{ color: '#9ca3af' }} />
                      ) : (
                        <ChevronDown size={20} style={{ color: '#9ca3af' }} />
                      )}
                      <div>
                        <div style={{ fontWeight: '600', color: 'white', marginBottom: '4px' }}>
                          {supplier.supplier_name || supplier.supplier_code}
                        </div>
                        <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                          Código: {supplier.supplier_code}
                        </div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        padding: '4px 12px',
                        borderRadius: '4px',
                        backgroundColor: supplier.validation_score >= 80 ? '#065f46' : supplier.validation_score >= 50 ? '#92400e' : '#991b1b',
                        color: 'white',
                        fontWeight: '600',
                        fontSize: '14px'
                      }}>
                        Score: {supplier.validation_score}%
                      </div>
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: '600',
                        backgroundColor: supplier.status === 'ACTIVE' ? '#059669' : '#6b7280',
                        color: 'white'
                      }}>
                        {supplier.status}
                      </span>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isExpanded && (
                    <div style={{
                      padding: '16px',
                      borderTop: '1px solid #374151',
                      backgroundColor: '#0f1419'
                    }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                        <div>
                          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Cuestionario ID</div>
                          <div style={{ fontWeight: '500', color: 'white' }}>
                            <Link 
                              to={`/questionnaires/${supplier.questionnaire_id}`}
                              style={{ color: '#60a5fa', textDecoration: 'none' }}
                            >
                              #{supplier.questionnaire_id}
                            </Link>
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>Fecha Validación</div>
                          <div style={{ fontWeight: '500', color: 'white' }}>
                            {supplier.validated_at 
                              ? new Date(supplier.validated_at).toLocaleDateString('es-ES', {
                                  year: 'numeric',
                                  month: 'short',
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })
                              : 'N/A'}
                          </div>
                        </div>
                      </div>

                      {supplier.mismatch_fields && supplier.mismatch_fields.length > 0 && (
                        <div style={{ marginTop: '16px' }}>
                          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px' }}>
                            Diferencias aceptadas ({supplier.accepted_mismatches?.length || 0} de {supplier.mismatch_fields.length})
                          </div>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {supplier.mismatch_fields.map((mismatch: any, idx: number) => (
                              <div
                                key={idx}
                                style={{
                                  padding: '8px 12px',
                                  backgroundColor: mismatch.accepted ? '#065f46' : '#7f1d1d',
                                  borderRadius: '4px',
                                  fontSize: '12px',
                                  display: 'flex',
                                  justifyContent: 'space-between',
                                  alignItems: 'center'
                                }}
                              >
                                <span style={{ color: 'white' }}>
                                  {mismatch.field_name} ({mismatch.field_code})
                                </span>
                                {mismatch.accepted && (
                                  <span style={{
                                    padding: '2px 6px',
                                    backgroundColor: '#10b981',
                                    color: 'white',
                                    borderRadius: '3px',
                                    fontSize: '10px'
                                  }}>
                                    ACEPTADO
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}