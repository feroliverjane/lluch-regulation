import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import '../components/Layout.css';
import { ChevronDown, ChevronUp } from 'lucide-react';
import CompositeComparison from '../components/CompositeComparison';

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
  reference_code: string;
  version: number;
  origin: string;
  composite_origin?: string;
  status: string;
  composite_type?: 'Z1' | 'Z2';
  extraction_confidence?: number;
  components: any[];
  created_at: string;
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
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [importing, setImporting] = useState(false);
  const [currentTab, setCurrentTab] = useState<number>(1);
  const [updatingToZ2, setUpdatingToZ2] = useState(false);
  const [showUploadZ2, setShowUploadZ2] = useState(false);
  const [selectedZ2File, setSelectedZ2File] = useState<File | null>(null);
  const [creatingZ1, setCreatingZ1] = useState(false);
  const [uploadingDocs, setUploadingDocs] = useState(false);
  const [extractingComposite, setExtractingComposite] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [showUploadDocs, setShowUploadDocs] = useState(false);
  const [importingZ2, setImportingZ2] = useState(false);
  const [selectedZ2ImportFile, setSelectedZ2ImportFile] = useState<File | null>(null);

  useEffect(() => {
    fetchBlueLineDetail();
  }, [id, material_id]);

  const fetchBlueLineDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      
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
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: `HTTP ${response.status}: ${response.statusText}` }));
        const errorMessage = errorData.detail || `Error loading blue line: ${response.status}`;
        setError(errorMessage);
        setLoading(false);
        return;
      }
      
      const data = await response.json();
      setBlueLine(data);
      
      // Debug: Log pending documents
      if (data.calculation_metadata?.pending_documents) {
        console.log('Pending documents found:', data.calculation_metadata.pending_documents.length);
      }

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
    } catch (error: any) {
      console.error('Error fetching blue line:', error);
      const errorMessage = error.message || 'Error desconocido al cargar la línea azul';
      setError(errorMessage);
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

  const handleUpdateToZ2 = async () => {
    if (!composite || !selectedZ2File) {
      alert('Por favor selecciona un archivo primero');
      return;
    }

    // Validate file type - accept Excel/CSV for Z2 import
    const fileExt = selectedZ2File.name.toLowerCase().split('.').pop();
    if (!fileExt || !['xlsx', 'xls', 'csv'].includes(fileExt)) {
      alert('Por favor selecciona un archivo Excel (.xlsx, .xls) o CSV (.csv)');
      return;
    }

    if (!confirm('¿Importar composite Z2 desde archivo Excel/CSV? Esta acción actualizará el composite a Z2 con los datos del archivo.')) {
      return;
    }

    setUpdatingToZ2(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedZ2File);

      // Use the new endpoint for importing Z2 from Excel
      await api.post(`/composites/${composite.id}/import-z2-from-excel`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      alert('✅ Composite Z2 importado exitosamente desde Excel/CSV');
      setShowUploadZ2(false);
      setSelectedZ2File(null);
      fetchBlueLineDetail(); // Refresh data
    } catch (error: any) {
      console.error('Error importing Z2:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Error al importar Z2';
      alert(`Error al importar Z2: ${errorMsg}`);
    } finally {
      setUpdatingToZ2(false);
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

    if (!blueLine) return;

    try {
      setUploadingDocs(true);
      const formData = new FormData();
      
      for (let i = 0; i < selectedFiles.length; i++) {
        formData.append('files', selectedFiles[i]);
      }

      const uploadResponse = await api.post(`/blue-line/${blueLine.id}/upload-documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setSelectedFiles(null);
      setShowUploadDocs(false);
      
      // Check upload response
      const docCount = uploadResponse.data.total_documents || 0;
      const uploadedCount = uploadResponse.data.uploaded_files?.length || 0;
      
      console.log('Upload response:', uploadResponse.data);
      
      if (docCount === 0 && uploadedCount === 0) {
        alert('⚠️ Error: No se pudieron subir los documentos. Por favor, intenta nuevamente.');
        return;
      }
      
      // Reload blue line to get updated metadata with pending documents
      await fetchBlueLineDetail();
      
      // Verify documents are in metadata before extracting
      const updatedBlueLine = await api.get(`/blue-line/${blueLine.id}`);
      const pendingDocs = updatedBlueLine.data.calculation_metadata?.pending_documents || [];
      
      if (pendingDocs.length === 0) {
        alert(`⚠️ Advertencia: Los documentos se subieron pero no se encontraron en metadata.\n\nSubidos: ${uploadedCount}\nPendientes: ${pendingDocs.length}\n\nPor favor, intenta extraer manualmente con el botón de abajo.`);
        return;
      }
      
      // Automatically extract composite after uploading documents
      try {
        setExtractingComposite(true);
        const extractResponse = await api.post(`/blue-line/${blueLine.id}/extract-composite`);
        
        // Reload again to show the extracted composite
        await fetchBlueLineDetail();
        
        const compCount = extractResponse.data.components_count || 0;
        const confidence = extractResponse.data.extraction_confidence || 0;
        
        alert(`✅ Documentos subidos y composite extraído exitosamente!\n\n📄 Documentos: ${docCount}\n🧪 Componentes extraídos: ${compCount}\n📊 Confianza: ${confidence.toFixed(1)}%`);
      } catch (extractErr: any) {
        console.error('Error extracting composite:', extractErr);
        alert(`✅ Documentos subidos exitosamente (${docCount} documento(s)).\n\n⚠️ Error al extraer automáticamente: ${extractErr.response?.data?.detail || extractErr.message}\n\nPuedes intentar extraer manualmente con el botón de abajo.`);
      } finally {
        setExtractingComposite(false);
      }
    } catch (err: any) {
      console.error('Error uploading documents:', err);
      alert(err.response?.data?.detail || 'Error al subir documentos');
    } finally {
      setUploadingDocs(false);
    }
  };

  const handleExtractComposite = async () => {
    if (!blueLine) return;

    try {
      setExtractingComposite(true);
      const response = await api.post(`/blue-line/${blueLine.id}/extract-composite`);
      
      alert(`✅ Composite Z1 extraído exitosamente: ${response.data.components_count} componentes con ${response.data.extraction_confidence.toFixed(1)}% confianza`);
      fetchBlueLineDetail(); // Refresh data
    } catch (err: any) {
      console.error('Error extracting composite:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Error al extraer composite';
      alert(`Error al extraer composite: ${errorMessage}`);
    } finally {
      setExtractingComposite(false);
    }
  };

  const handleCreateZ1 = () => {
    if (!blueLine) return;
    setShowUploadDocs(true);
  };

  const handleImportZ2 = async (file?: File) => {
    const fileToUse = file || selectedZ2ImportFile;
    if (!blueLine || !fileToUse) {
      if (!fileToUse) {
        alert('Por favor selecciona un archivo primero');
      }
      return;
    }

    // Validate file type
    const fileExt = fileToUse.name.toLowerCase().split('.').pop();
    if (!['xlsx', 'xls', 'csv'].includes(fileExt)) {
      alert('Por favor selecciona un archivo Excel (.xlsx, .xls) o CSV (.csv)');
      return;
    }

    if (!confirm('¿Importar composite Z2 desde archivo Excel/CSV? Esta acción actualizará el composite a Z2 con los datos del archivo.')) {
      return;
    }

    setImportingZ2(true);
    try {
      const formData = new FormData();
      formData.append('file', fileToUse);
      
      // Use the new endpoint for importing Z2 from Excel
      const compositeId = composite?.id || blueLine.composite_id;
      if (compositeId) {
        // Update existing composite to Z2 from Excel
        await api.post(`/composites/${compositeId}/import-z2-from-excel`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        alert('✅ Composite Z2 importado exitosamente desde Excel/CSV');
      } else {
        // If no composite exists, create Z1 first then update to Z2
        const z1Response = await api.post(`/blue-line/${blueLine.id}/create-composite`);
        await api.post(`/composites/${z1Response.data.composite_id}/import-z2-from-excel`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        alert('✅ Composite Z2 importado exitosamente desde Excel/CSV');
      }

      setSelectedZ2ImportFile(null);
      setShowUploadZ2(false);
      fetchBlueLineDetail(); // Refresh data
    } catch (error: any) {
      console.error('Error importing Z2:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Error al importar Z2';
      alert(`Error al importar Z2: ${errorMsg}`);
    } finally {
      setImportingZ2(false);
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

  if (error) {
    return (
      <div className="container" style={{ padding: '24px' }}>
        <div className="card" style={{ backgroundColor: '#7f1d1d', border: '1px solid #991b1b', color: 'white' }}>
          <h2 style={{ color: '#fca5a5' }}>❌ Error al cargar Línea Azul</h2>
          <p style={{ color: '#fca5a5' }}>{error}</p>
          <button 
            onClick={() => fetchBlueLineDetail()} 
            className="btn-primary"
            style={{ marginTop: '16px' }}
          >
            🔄 Reintentar
          </button>
          <Link 
            to="/blue-line" 
            className="btn-secondary"
            style={{ marginLeft: '8px', marginTop: '16px', display: 'inline-block' }}
          >
            ← Volver a Lista
          </Link>
        </div>
      </div>
    );
  }

  if (!blueLine || !material) {
    return (
      <div className="container" style={{ padding: '24px' }}>
        <div className="card" style={{ backgroundColor: '#7f1d1d', border: '1px solid #991b1b', color: 'white' }}>
          <h2 style={{ color: '#fca5a5' }}>⚠️ Línea Azul no encontrada</h2>
          <p style={{ color: '#fca5a5' }}>
            No se encontró una línea azul con el ID proporcionado.
            {id && ` ID: ${id}`}
            {material_id && ` Material ID: ${material_id}`}
          </p>
          <Link 
            to="/blue-line" 
            className="btn-secondary"
            style={{ marginTop: '16px' }}
          >
            ← Volver a Lista
          </Link>
        </div>
      </div>
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

      {/* Material Suppliers Section - Moved to top */}
      <div className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px' }}>
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
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>
                          Score de Validación
                        </div>
                        <div style={{
                          fontSize: '18px',
                          fontWeight: '600',
                          color: supplier.validation_score >= 80 ? '#10b981' : supplier.validation_score >= 50 ? '#f59e0b' : '#ef4444'
                        }}>
                          {supplier.validation_score}%
                        </div>
                      </div>
                      <div style={{
                        padding: '4px 12px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: '600',
                        backgroundColor: supplier.status === 'ACTIVE' ? '#065f46' : '#991b1b',
                        color: 'white'
                      }}>
                        {supplier.status}
                      </div>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isExpanded && (
                    <div style={{ padding: '16px', borderTop: '1px solid #374151' }}>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', marginBottom: '16px' }}>
                        <div>
                          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>
                            Questionario ID
                          </div>
                          <div style={{ fontWeight: '500', color: 'white' }}>
                            #{supplier.questionnaire_id}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>
                            Validado el
                          </div>
                          <div style={{ fontWeight: '500', color: 'white' }}>
                            {supplier.validated_at ? new Date(supplier.validated_at).toLocaleString() : 'N/A'}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>
                            Campos con diferencias
                          </div>
                          <div style={{ fontWeight: '500', color: 'white' }}>
                            {supplier.mismatch_fields?.length || 0}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '4px' }}>
                            Diferencias aceptadas
                          </div>
                          <div style={{ fontWeight: '500', color: 'white' }}>
                            {supplier.accepted_mismatches?.length || 0}
                          </div>
                        </div>
                      </div>

                      {supplier.mismatch_fields && supplier.mismatch_fields.length > 0 && (
                        <div style={{ marginTop: '16px' }}>
                          <h3 style={{ fontSize: '14px', fontWeight: '600', color: 'white', marginBottom: '12px' }}>
                            Campos con Diferencias:
                          </h3>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                            {supplier.mismatch_fields.map((mismatch: any, idx: number) => (
                              <div
                                key={idx}
                                style={{
                                  padding: '12px',
                                  backgroundColor: mismatch.severity === 'CRITICAL' ? '#7f1d1d' : mismatch.severity === 'WARNING' ? '#78350f' : '#1e293b',
                                  borderRadius: '4px',
                                  border: `1px solid ${mismatch.severity === 'CRITICAL' ? '#991b1b' : mismatch.severity === 'WARNING' ? '#92400e' : '#334155'}`
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                                  <div style={{ fontWeight: '600', color: 'white' }}>
                                    {mismatch.field_name} ({mismatch.field_code})
                                  </div>
                                  <div style={{
                                    padding: '2px 8px',
                                    borderRadius: '4px',
                                    fontSize: '11px',
                                    fontWeight: '600',
                                    backgroundColor: mismatch.severity === 'CRITICAL' ? '#dc2626' : mismatch.severity === 'WARNING' ? '#f59e0b' : '#3b82f6',
                                    color: 'white'
                                  }}>
                                    {mismatch.severity}
                                  </div>
                                </div>
                                {mismatch.expected_value && (
                                  <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '2px' }}>
                                    Esperado: <span style={{ color: '#d1d5db' }}>{mismatch.expected_value}</span>
                                  </div>
                                )}
                                <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                                  Actual: <span style={{ color: '#d1d5db' }}>{mismatch.actual_value || 'N/A'}</span>
                                </div>
                                {mismatch.accepted && (
                                  <div style={{ marginTop: '8px', fontSize: '11px', color: '#10b981' }}>
                                    ✓ Diferencia aceptada
                                  </div>
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
        <div className="card" style={{ 
          marginBottom: '24px', 
          backgroundColor: composite.composite_type === 'Z2' ? '#064e3b' : '#1e3a8a', 
          border: composite.composite_type === 'Z2' ? '1px solid #065f46' : '1px solid #1e40af',
          color: 'white' 
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
            <h2 style={{ marginTop: 0, color: 'white' }}>
              Composite Asociado
              {composite.composite_type && (
                <span className={`badge ${composite.composite_type === 'Z2' ? 'badge-success' : 'badge-info'}`} style={{ marginLeft: '12px', fontSize: '14px' }}>
                  {composite.composite_type}
                </span>
              )}
            </h2>
            
            {composite.composite_type === 'Z1' && !showUploadZ2 && (
              <button 
                onClick={() => setShowUploadZ2(true)}
                className="btn-primary"
                style={{ fontSize: '13px' }}
              >
                ⬆️ Actualizar a Z2
              </button>
            )}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '16px' }}>
            <div>
              <div style={{ fontSize: '12px', color: composite.composite_type === 'Z2' ? '#6ee7b7' : '#bfdbfe' }}>ID</div>
              <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>#{composite.id}</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: composite.composite_type === 'Z2' ? '#6ee7b7' : '#bfdbfe' }}>Versión</div>
              <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>v{composite.version}</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: composite.composite_type === 'Z2' ? '#6ee7b7' : '#bfdbfe' }}>Origen</div>
              <div style={{ marginTop: '4px' }}>
                <span className="badge badge-secondary">{composite.composite_origin || composite.origin}</span>
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: composite.composite_type === 'Z2' ? '#6ee7b7' : '#bfdbfe' }}>Componentes</div>
              <div style={{ fontWeight: '500', marginTop: '4px', color: 'white' }}>
                {composite.components?.length || 0}
              </div>
            </div>
          </div>

          {composite.extraction_confidence && (
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', color: composite.composite_type === 'Z2' ? '#6ee7b7' : '#bfdbfe', marginBottom: '4px' }}>
                Confianza de Extracción
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ flex: 1, height: '8px', backgroundColor: '#111827', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    width: `${composite.extraction_confidence}%`,
                    height: '100%',
                    backgroundColor: composite.extraction_confidence >= 80 ? '#10b981' : 
                                     composite.extraction_confidence >= 60 ? '#f59e0b' : '#ef4444',
                    transition: 'width 0.3s'
                  }} />
                </div>
                <div style={{ fontWeight: '600', color: 'white' }}>
                  {composite.extraction_confidence.toFixed(1)}%
                </div>
              </div>
            </div>
          )}

          {composite.composite_type === 'Z2' && (
            <div style={{ 
              padding: '12px', 
              backgroundColor: '#065f46',
              border: '1px solid #059669',
              borderRadius: '6px',
              marginBottom: '16px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6ee7b7' }}>
                <span style={{ fontSize: '20px' }}>🔒</span>
                <div>
                  <div style={{ fontWeight: '600', fontSize: '14px' }}>Composite Z2 - Definitivo</div>
                  <div style={{ fontSize: '12px', marginTop: '2px' }}>
                    Este composite ha sido validado en laboratorio y no se puede modificar.
                  </div>
                </div>
              </div>
            </div>
          )}

          {showUploadZ2 && composite.composite_type === 'Z1' && (
            <div style={{
              padding: '16px',
              backgroundColor: '#111827',
              border: '1px solid #374151',
              borderRadius: '6px',
              marginBottom: '16px'
            }}>
              <h3 style={{ marginTop: 0, fontSize: '14px', fontWeight: '600', color: 'white', marginBottom: '12px' }}>
                Importar Composite Z2 desde Excel/CSV
              </h3>
              <p style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '12px' }}>
                Sube un archivo Excel (.xlsx, .xls) o CSV con el formato SAP que contiene los componentes del composite. 
                El archivo debe tener columnas: Espec./compon. (CAS), Nombre del producto, Cl.Componente (COMPONENT), 
                Valor Lím.inf., Valor Lím.sup., y Unidad.
              </p>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <input
                  type="file"
                  accept=".xlsx,.xls,.csv"
                  onChange={(e) => setSelectedZ2File(e.target.files?.[0] || null)}
                  style={{
                    flex: 1,
                    padding: '8px',
                    backgroundColor: '#1f2937',
                    border: '1px solid #4b5563',
                    borderRadius: '4px',
                    color: 'white'
                  }}
                />
                <button 
                  onClick={handleUpdateToZ2}
                  className="btn-primary"
                  disabled={updatingToZ2 || !selectedZ2File}
                >
                  {updatingToZ2 ? 'Actualizando...' : '✅ Confirmar Z2'}
                </button>
                <button 
                  onClick={() => {
                    setShowUploadZ2(false);
                    setSelectedZ2File(null);
                  }}
                  className="btn-secondary"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {(!composite.components || composite.components.length === 0) && (
            <div style={{ 
              padding: '16px', 
              backgroundColor: '#111827', 
              borderRadius: '6px', 
              border: '1px solid #374151',
              marginBottom: '16px'
            }}>
              <div style={{ marginBottom: '12px' }}>
                <span style={{ color: '#f59e0b', fontWeight: '600' }}>⚠️ Este composite está vacío</span>
              </div>
              
              {!showUploadDocs ? (
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                  <button 
                    onClick={handleCreateZ1}
                    className="btn-primary"
                    disabled={creatingZ1 || uploadingDocs}
                    style={{ fontSize: '13px' }}
                  >
                    📊 Calcular Z1 con IA
                  </button>
                  <button 
                    onClick={() => {
                      const input = document.createElement('input');
                      input.type = 'file';
                      input.accept = '.pdf,.xlsx,.csv';
                      input.onchange = async (e: any) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          setSelectedZ2ImportFile(file);
                          setTimeout(() => {
                            handleImportZ2(file);
                          }, 100);
                        }
                      };
                      input.click();
                    }}
                    className="btn-secondary"
                    disabled={importingZ2}
                    style={{ fontSize: '13px' }}
                  >
                    {importingZ2 ? 'Importando...' : '📥 Importar Z2'}
                  </button>
                </div>
              ) : (
                <div style={{
                  padding: '16px',
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  marginBottom: '12px'
                }}>
                  <h3 style={{ marginTop: 0, fontSize: '14px', fontWeight: '600', color: 'white', marginBottom: '12px' }}>
                    📤 Subir Documentos PDF para Extracción con IA
                  </h3>
                  <p style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '12px' }}>
                    Sube los documentos PDF (IFRA, SDS, etc.) y la IA extraerá automáticamente la composición química.
                  </p>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
                    <input
                      type="file"
                      accept=".pdf"
                      multiple
                      onChange={handleFileSelect}
                      style={{
                        flex: 1,
                        minWidth: '200px',
                        padding: '8px',
                        backgroundColor: '#111827',
                        border: '1px solid #4b5563',
                        borderRadius: '4px',
                        color: 'white'
                      }}
                    />
                    <button 
                      onClick={handleUploadDocuments}
                      className="btn-primary"
                      disabled={uploadingDocs || !selectedFiles || selectedFiles.length === 0}
                      style={{ fontSize: '13px' }}
                    >
                      {uploadingDocs ? 'Subiendo...' : '📤 Subir Documentos'}
                    </button>
                    <button 
                      onClick={() => {
                        setShowUploadDocs(false);
                        setSelectedFiles(null);
                      }}
                      className="btn-secondary"
                      style={{ fontSize: '13px' }}
                    >
                      Cancelar
                    </button>
                  </div>
                  {selectedFiles && selectedFiles.length > 0 && (
                    <div style={{ marginTop: '12px', fontSize: '12px', color: '#9ca3af' }}>
                      {selectedFiles.length} archivo(s) seleccionado(s)
                    </div>
                  )}
                </div>
              )}

              {/* Show extract button if documents are uploaded */}
              {(() => {
                const pendingDocs = blueLine?.calculation_metadata?.pending_documents;
                const hasDocs = pendingDocs && Array.isArray(pendingDocs) && pendingDocs.length > 0;
                
                // Debug log
                if (blueLine) {
                  console.log('🔍 Blue Line calculation_metadata:', blueLine.calculation_metadata);
                  console.log('🔍 Pending documents:', pendingDocs);
                  console.log('🔍 Has docs:', hasDocs);
                }
                
                return hasDocs;
              })() && (
                <div 
                  data-extraction-area
                  style={{
                    padding: '12px',
                    backgroundColor: '#065f46',
                    border: '1px solid #059669',
                    borderRadius: '6px',
                    marginTop: '12px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                    <div>
                      <div style={{ fontWeight: '600', color: '#6ee7b7', marginBottom: '4px' }}>
                        ✅ Documentos listos para extracción
                      </div>
                      <div style={{ fontSize: '12px', color: '#6ee7b7' }}>
                        {blueLine.calculation_metadata.pending_documents.length} documento(s) subido(s)
                      </div>
                    </div>
                    <button 
                      onClick={handleExtractComposite}
                      className="btn-primary"
                      disabled={extractingComposite}
                      style={{ fontSize: '13px', whiteSpace: 'nowrap' }}
                    >
                      {extractingComposite ? '⏳ Extrayendo...' : '🤖 Extraer Composite con IA'}
                    </button>
                  </div>
                </div>
              )}

              <div style={{ fontSize: '12px', color: '#9ca3af', marginTop: '12px' }}>
                <div>• <strong>Calcular Z1 con IA:</strong> Sube PDFs y la IA extraerá automáticamente los componentes químicos</div>
                <div>• <strong>Importar Z2:</strong> Importa un composite Z2 definitivo desde un archivo de laboratorio</div>
              </div>
            </div>
          )}

          <div style={{ marginTop: '16px' }}>
            <Link 
              to={`/composites/${composite.id}`}
              className="btn-secondary"
              style={{ fontSize: '13px' }}
            >
              Ver Composite Detallado
            </Link>
          </div>
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