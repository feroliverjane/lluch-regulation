import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import '../components/Layout.css';

interface BlueLine {
  id: number;
  material_id: number;
  supplier_code: string;
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

interface Template {
  id: number;
  name: string;
  questions_schema: QuestionField[];
  section_names?: { [key: string]: string };
  tab_names?: { [key: string]: string };
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api';

export default function BlueLineDetail() {
  const { id } = useParams<{ id: string }>();
  const [blueLine, setBlueLine] = useState<BlueLine | null>(null);
  const [material, setMaterial] = useState<Material | null>(null);
  const [template, setTemplate] = useState<Template | null>(null);
  const [composite, setComposite] = useState<Composite | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [importing, setImporting] = useState(false);
  const [currentTab, setCurrentTab] = useState<number>(1);

  useEffect(() => {
    fetchBlueLineDetail();
  }, [id]);

  const fetchBlueLineDetail = async () => {
    try {
      setLoading(true);
      
      // Load Blue Line
      const response = await fetch(`${API_URL}${API_PREFIX}/blue-line/${id}`);
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
          <h1 style={{ color: 'white' }}>Línea Azul #{blueLine.id}</h1>
          <p style={{ color: '#d1d5db', marginTop: '4px' }}>
            {material.reference_code} - {material.name}
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
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>Proveedor</div>
            <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>{blueLine.supplier_code}</div>
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
    </div>
  );
}