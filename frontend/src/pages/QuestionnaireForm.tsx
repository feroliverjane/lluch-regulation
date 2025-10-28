import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

interface Material {
  id: number;
  reference_code: string;
  name: string;
  supplier: string;
  supplier_code?: string;
}

export default function QuestionnaireForm() {
  const navigate = useNavigate();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form data
  const [materialId, setMaterialId] = useState<number | ''>('');
  const [supplierCode, setSupplierCode] = useState('');
  const [questionnaireType, setQuestionnaireType] = useState<'INITIAL_HOMOLOGATION' | 'REHOMOLOGATION'>('INITIAL_HOMOLOGATION');
  
  // Sample questionnaire responses
  const [responses, setResponses] = useState({
    company_name: '',
    contact_person: '',
    contact_email: '',
    contact_phone: '',
    quality_certificate: '',
    organic_certified: 'No',
    kosher_certified: 'No',
    halal_certified: 'No',
    sustainable_sourcing: 'Yes',
    allergen_declaration: 'None',
    purity_percentage: '',
    moisture_content: '',
    country_of_origin: '',
    gmo_free: 'Yes',
  });

  useEffect(() => {
    loadMaterials();
  }, []);

  const loadMaterials = async () => {
    try {
      setLoading(true);
      const response = await api.get('/materials');
      setMaterials(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading materials');
    } finally {
      setLoading(false);
    }
  };

  const handleMaterialChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = parseInt(e.target.value);
    setMaterialId(id);
    
    // Auto-fill supplier code if available
    const material = materials.find(m => m.id === id);
    if (material?.supplier_code) {
      setSupplierCode(material.supplier_code);
    }
  };

  const handleResponseChange = (field: string, value: string) => {
    setResponses(prev => ({
      ...prev,
      [field]: value
    }));
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
      
      // Create questionnaire
      const createResponse = await api.post('/questionnaires', {
        material_id: materialId,
        supplier_code: supplierCode.trim(),
        questionnaire_type: questionnaireType,
        responses: responses
      });
      
      const questionnaireId = createResponse.data.id;
      
      // Submit for review if requested
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

  if (loading) return <div className="loading">Cargando materiales...</div>;

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/questionnaires" className="link" style={{ marginBottom: '8px', display: 'inline-block' }}>
            ← Volver a Cuestionarios
          </Link>
          <h1>Nuevo Cuestionario</h1>
          <p style={{ color: '#6b7280', marginTop: '4px' }}>
            Complete el cuestionario de homologación para el material y proveedor
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
        {/* Basic Information */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0 }}>Información Básica</h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
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
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Código Proveedor *
              </label>
              <input
                type="text"
                value={supplierCode}
                onChange={(e) => setSupplierCode(e.target.value)}
                required
                placeholder="Ej: PROV-001"
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Tipo de Cuestionario
            </label>
            <select
              value={questionnaireType}
              onChange={(e) => setQuestionnaireType(e.target.value as any)}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '6px',
                border: '1px solid #e5e7eb'
              }}
            >
              <option value="INITIAL_HOMOLOGATION">Homologación Inicial</option>
              <option value="REHOMOLOGATION">Rehomologación</option>
            </select>
          </div>
        </div>

        {/* Company Information */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0 }}>Información de la Empresa</h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Nombre de la Empresa
              </label>
              <input
                type="text"
                value={responses.company_name}
                onChange={(e) => handleResponseChange('company_name', e.target.value)}
                placeholder="Ej: Global Ingredients Ltd."
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Persona de Contacto
              </label>
              <input
                type="text"
                value={responses.contact_person}
                onChange={(e) => handleResponseChange('contact_person', e.target.value)}
                placeholder="Ej: John Smith"
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Email de Contacto
              </label>
              <input
                type="email"
                value={responses.contact_email}
                onChange={(e) => handleResponseChange('contact_email', e.target.value)}
                placeholder="contacto@empresa.com"
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Teléfono
              </label>
              <input
                type="tel"
                value={responses.contact_phone}
                onChange={(e) => handleResponseChange('contact_phone', e.target.value)}
                placeholder="+34 XXX XXX XXX"
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

        {/* Quality & Certifications */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0 }}>Calidad y Certificaciones</h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Certificado de Calidad
              </label>
              <input
                type="text"
                value={responses.quality_certificate}
                onChange={(e) => handleResponseChange('quality_certificate', e.target.value)}
                placeholder="Ej: ISO 9001:2015"
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                País de Origen
              </label>
              <input
                type="text"
                value={responses.country_of_origin}
                onChange={(e) => handleResponseChange('country_of_origin', e.target.value)}
                placeholder="Ej: España"
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Certificado Orgánico
              </label>
              <select
                value={responses.organic_certified}
                onChange={(e) => handleResponseChange('organic_certified', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              >
                <option value="Yes">Sí</option>
                <option value="No">No</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Certificado Kosher
              </label>
              <select
                value={responses.kosher_certified}
                onChange={(e) => handleResponseChange('kosher_certified', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              >
                <option value="Yes">Sí</option>
                <option value="No">No</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Certificado Halal
              </label>
              <select
                value={responses.halal_certified}
                onChange={(e) => handleResponseChange('halal_certified', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              >
                <option value="Yes">Sí</option>
                <option value="No">No</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Libre de GMO
              </label>
              <select
                value={responses.gmo_free}
                onChange={(e) => handleResponseChange('gmo_free', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              >
                <option value="Yes">Sí</option>
                <option value="No">No</option>
              </select>
            </div>
          </div>
        </div>

        {/* Quality Parameters */}
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0 }}>Parámetros de Calidad</h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Pureza (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={responses.purity_percentage}
                onChange={(e) => handleResponseChange('purity_percentage', e.target.value)}
                placeholder="99.5"
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Contenido de Humedad (%)
              </label>
              <input
                type="number"
                step="0.1"
                value={responses.moisture_content}
                onChange={(e) => handleResponseChange('moisture_content', e.target.value)}
                placeholder="0.2"
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              />
            </div>

            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
                Sostenibilidad
              </label>
              <select
                value={responses.sustainable_sourcing}
                onChange={(e) => handleResponseChange('sustainable_sourcing', e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px',
                  borderRadius: '6px',
                  border: '1px solid #e5e7eb'
                }}
              >
                <option value="Yes">Sí</option>
                <option value="No">No</option>
              </select>
            </div>
          </div>

          <div style={{ marginTop: '16px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500' }}>
              Declaración de Alérgenos
            </label>
            <input
              type="text"
              value={responses.allergen_declaration}
              onChange={(e) => handleResponseChange('allergen_declaration', e.target.value)}
              placeholder="Ej: None, o 'Puede contener trazas de...'"
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '6px',
                border: '1px solid #e5e7eb'
              }}
            />
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
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
      </form>
    </div>
  );
}

