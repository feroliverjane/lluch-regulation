import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

interface Material {
  id: number;
  reference_code: string;
  name: string;
  supplier_code?: string;
}

interface QuestionField {
  fieldCode: string;
  fieldName: string;
  fieldType: string;
  tab: number;
  section: number;
  required: boolean;
  critical: boolean;
  validationRules: any;
  defaultValue?: string;
  order: number;
}

interface Template {
  id: number;
  name: string;
  questions_schema: QuestionField[];
  total_questions: number;
  total_sections: number;
}

export default function QuestionnaireFormDynamic() {
  const navigate = useNavigate();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [template, setTemplate] = useState<Template | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form data
  const [materialId, setMaterialId] = useState<number | ''>('');
  const [supplierCode, setSupplierCode] = useState('');
  const [currentTab, setCurrentTab] = useState(1);
  const [responses, setResponses] = useState<{ [fieldCode: string]: any }>({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load materials
      const materialsRes = await api.get('/materials');
      setMaterials(materialsRes.data);
      
      // Load default template
      const templateRes = await api.get('/questionnaire-templates/default');
      setTemplate(templateRes.data);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading data');
    } finally {
      setLoading(false);
    }
  };

  const handleMaterialChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = parseInt(e.target.value);
    setMaterialId(id);
    
    const material = materials.find(m => m.id === id);
    if (material?.supplier_code) {
      setSupplierCode(material.supplier_code);
    }
  };

  const handleFieldChange = (fieldCode: string, value: any) => {
    setResponses(prev => ({
      ...prev,
      [fieldCode]: {
        name: getFieldName(fieldCode),
        type: getFieldType(fieldCode),
        value: value
      }
    }));
  };

  const getFieldName = (fieldCode: string): string => {
    const field = template?.questions_schema.find(q => q.fieldCode === fieldCode);
    return field?.fieldName || fieldCode;
  };

  const getFieldType = (fieldCode: string): string => {
    const field = template?.questions_schema.find(q => q.fieldCode === fieldCode);
    return field?.fieldType || 'inputText';
  };

  const renderField = (field: QuestionField) => {
    const value = responses[field.fieldCode]?.value || '';
    const commonStyle = {
      width: '100%',
      padding: '8px',
      borderRadius: '6px',
      border: '1px solid #e5e7eb',
      fontSize: '14px'
    };

    switch (field.fieldType) {
      case 'inputText':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(field.fieldCode, e.target.value)}
            required={field.required}
            style={commonStyle}
            placeholder={field.required ? 'Required' : 'Optional'}
          />
        );

      case 'inputNumber':
        return (
          <input
            type="number"
            step="0.01"
            value={value}
            onChange={(e) => handleFieldChange(field.fieldCode, e.target.value)}
            required={field.required}
            style={commonStyle}
          />
        );

      case 'inputTextarea':
        return (
          <textarea
            value={value}
            onChange={(e) => handleFieldChange(field.fieldCode, e.target.value)}
            required={field.required}
            rows={3}
            style={{ ...commonStyle, resize: 'vertical' }}
          />
        );

      case 'yesNoNA':
        return (
          <select
            value={value}
            onChange={(e) => handleFieldChange(field.fieldCode, e.target.value)}
            required={field.required}
            style={commonStyle}
          >
            <option value="">Select...</option>
            <option value="YES">Yes</option>
            <option value="NO">No</option>
            <option value="NA">Not Applicable</option>
          </select>
        );

      case 'checkComents':
      case 'yesNoComments':
        const [yesNo, comment] = typeof value === 'string' ? value.split('|') : ['', ''];
        return (
          <div style={{ display: 'flex', gap: '8px' }}>
            <select
              value={yesNo}
              onChange={(e) => {
                const newValue = `${e.target.value}|${comment || ''}`;
                handleFieldChange(field.fieldCode, newValue);
              }}
              style={{ ...commonStyle, flex: '0 0 120px' }}
            >
              <option value="">Select...</option>
              <option value="YES">Yes</option>
              <option value="NO">No</option>
              <option value="NA">N/A</option>
            </select>
            <input
              type="text"
              value={comment || ''}
              onChange={(e) => {
                const newValue = `${yesNo || ''}|${e.target.value}`;
                handleFieldChange(field.fieldCode, newValue);
              }}
              placeholder="Comments (optional)"
              style={{ ...commonStyle, flex: '1' }}
            />
          </div>
        );

      case 'lov':
      case 'selectManyMenu':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(field.fieldCode, e.target.value)}
            required={field.required}
            style={commonStyle}
            placeholder="Enter value or code"
          />
        );

      case 'selectManyCheckbox':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(field.fieldCode, e.target.value)}
            style={commonStyle}
            placeholder="Comma-separated values"
          />
        );

      case 'checkTableMatCasPercen':
      case 'tableDescYesNoPercen':
      case 'tableDescYesNoSubtCASPercent':
      case 'checkTableMatCasAnnexPercen':
      case 'checkTableMatCasROPercen':
      case 'checkTableMatStatusCFRPercen':
      case 'presenceIngredientTablePercentHandlers2':
        // For complex tables, use textarea with JSON format
        return (
          <textarea
            value={value}
            onChange={(e) => handleFieldChange(field.fieldCode, e.target.value)}
            rows={3}
            style={{ ...commonStyle, fontFamily: 'monospace', fontSize: '12px' }}
            placeholder='JSON format: [{"field1": "value1", "field2": "value2"}] or "[]" for empty'
          />
        );

      default:
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(field.fieldCode, e.target.value)}
            style={commonStyle}
          />
        );
    }
  };

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

  const handleSubmit = async (e: React.FormEvent, submitForReview: boolean = false) => {
    e.preventDefault();
    
    if (!materialId) {
      alert('Por favor seleccione un material');
      return;
    }
    
    if (!supplierCode.trim()) {
      alert('Por favor ingrese el código del proveedor');
      return;
    }

    try {
      setSaving(true);
      
      const createResponse = await api.post('/questionnaires', {
        material_id: materialId,
        supplier_code: supplierCode.trim(),
        questionnaire_type: 'INITIAL_HOMOLOGATION',
        template_id: template?.id,
        responses: responses
      });
      
      const questionnaireId = createResponse.data.id;
      
      if (submitForReview) {
        await api.post(`/questionnaires/${questionnaireId}/submit`, {});
        alert('Cuestionario creado y enviado para revisión');
      } else {
        alert('Cuestionario guardado como borrador');
      }
      
      navigate(`/questionnaires/${questionnaireId}`);
      
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al guardar cuestionario');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading">Cargando template...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!template) return <div className="error">No template available</div>;

  const tabs = organizeByTabs();
  const currentTabSections = tabs[currentTab] || {};

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/questionnaires" className="link" style={{ marginBottom: '8px', display: 'inline-block' }}>
            ← Volver a Cuestionarios
          </Link>
          <h1>Nuevo Cuestionario - Formato Lluch</h1>
          <p style={{ color: '#374151', marginTop: '4px', fontWeight: '500' }}>
            {template.name} - {template.total_questions} campos organizados en {template.total_sections} secciones
          </p>
        </div>
      </div>

      {error && (
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#fef2f2', 
          border: '1px solid #fecaca',
          borderRadius: '6px',
          marginBottom: '24px',
          color: '#991b1b'
        }}>
          {error}
        </div>
      )}

      <form onSubmit={(e) => handleSubmit(e, false)}>
        {/* Basic Info */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0, color: '#111827', fontWeight: '600' }}>Información Básica</h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#111827', fontSize: '14px' }}>
                Material *
              </label>
              <select
                value={materialId}
                onChange={handleMaterialChange}
                required
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              >
                <option value="">Seleccione un material</option>
                {materials.map(material => (
                  <option key={material.id} value={material.id}>
                    {material.reference_code} - {material.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#111827', fontSize: '14px' }}>
                Código Proveedor *
              </label>
              <input
                type="text"
                value={supplierCode}
                onChange={(e) => setSupplierCode(e.target.value)}
                required
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              />
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', gap: '4px', borderBottom: '2px solid #e5e7eb' }}>
            {Object.keys(tabs).map(tab => {
              const tabNum = parseInt(tab);
              const isActive = currentTab === tabNum;
              return (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setCurrentTab(tabNum)}
                  style={{
                    padding: '12px 24px',
                    border: 'none',
                    borderBottom: isActive ? '3px solid #3b82f6' : '3px solid transparent',
                    background: isActive ? '#eff6ff' : 'transparent',
                    color: isActive ? '#1e40af' : '#374151',
                    fontWeight: isActive ? '600' : '500',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  Tab {tabNum}
                </button>
              );
            })}
          </div>
        </div>

        {/* Fields by Section */}
        {Object.entries(currentTabSections).map(([sectionNum, fields]) => {
          const sectionFields = fields as QuestionField[];
          return (
            <div key={sectionNum} className="card" style={{ marginBottom: '24px' }}>
              <h2 style={{ marginTop: 0, fontSize: '18px', color: '#111827', fontWeight: '600' }}>
                Section {sectionNum}
                <span style={{ fontSize: '14px', fontWeight: 'normal', color: '#374151', marginLeft: '12px' }}>
                  ({sectionFields.length} campos)
                </span>
              </h2>
              
              <div style={{ display: 'grid', gap: '20px' }}>
                {sectionFields.map((field) => (
                  <div key={field.fieldCode}>
                    <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: '#111827' }}>
                      <span style={{ fontWeight: '500' }}>
                        {field.fieldName}
                        {field.required && <span style={{ color: '#ef4444', marginLeft: '4px' }}>*</span>}
                        {field.critical && (
                          <span style={{ 
                            marginLeft: '8px', 
                            fontSize: '11px', 
                            padding: '2px 6px', 
                            backgroundColor: '#fee2e2',
                            color: '#991b1b',
                            borderRadius: '4px'
                          }}>
                            CRITICAL
                          </span>
                        )}
                      </span>
                      <span style={{ 
                        fontSize: '11px', 
                        color: '#6b7280', 
                        fontFamily: 'monospace',
                        marginLeft: '8px',
                        fontWeight: '500'
                      }}>
                        {field.fieldCode}
                      </span>
                    </label>
                    {renderField(field)}
                    
                    {field.fieldType.includes('Table') && (
                      <div style={{ fontSize: '12px', color: '#374151', marginTop: '4px', fontWeight: '500' }}>
                        💡 Formato tabla: Use "[]" para vacío o JSON array
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {/* Progress Indicator */}
        <div className="card" style={{ marginBottom: '24px', backgroundColor: '#f9fafb' }}>
          <div style={{ fontSize: '14px', color: '#111827', fontWeight: '600' }}>
            📊 Progreso del cuestionario
          </div>
          <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ flex: 1, height: '10px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{
                width: `${(Object.keys(responses).length / template.total_questions) * 100}%`,
                height: '100%',
                backgroundColor: '#3b82f6',
                transition: 'width 0.3s'
              }} />
            </div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#111827' }}>
              {Object.keys(responses).length} / {template.total_questions}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '14px', color: '#111827', fontWeight: '500' }}>
            {currentTab < Object.keys(tabs).length ? (
              <button
                type="button"
                onClick={() => setCurrentTab(currentTab + 1)}
                className="btn-secondary"
              >
                Siguiente Tab →
              </button>
            ) : (
              <span style={{ color: '#059669', fontWeight: '600' }}>✅ Última sección</span>
            )}
          </div>
          
          <div style={{ display: 'flex', gap: '12px' }}>
            <Link to="/questionnaires" className="btn-secondary">
              Cancelar
            </Link>
            <button
              type="submit"
              className="btn-secondary"
              disabled={saving}
            >
              {saving ? 'Guardando...' : 'Guardar Borrador'}
            </button>
            <button
              type="button"
              onClick={(e) => handleSubmit(e, true)}
              className="btn-primary"
              disabled={saving}
            >
              {saving ? 'Guardando...' : 'Guardar y Enviar para Revisión'}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

