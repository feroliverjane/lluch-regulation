import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { materialsApi } from '../services/api';
import { Upload, FileJson, AlertCircle, CheckCircle, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api';

interface Material {
  id: number;
  reference_code: string;
  name: string;
}

interface MismatchField {
  field_code: string;
  field_name: string;
  expected_value?: string;
  actual_value?: string;
  severity: string;
  accepted: boolean;
}

interface ComparisonResult {
  blue_line_exists: boolean;
  matches: number;
  mismatches: MismatchField[];
  score: number;
  message?: string;
}

interface ImportResult {
  id: number;
  material_id: number;
  supplier_code: string;
  questionnaire_type: string;
  version: number;
  status: string;
  created_at: string;
  comparison?: ComparisonResult;
}

export default function QuestionnaireImport() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [selectedMaterialId, setSelectedMaterialId] = useState<number | ''>('');
  const [materialCode, setMaterialCode] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [filePreview, setFilePreview] = useState<string>('');
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [acceptedMismatches, setAcceptedMismatches] = useState<Set<string>>(new Set());
  const [creatingBlueLine, setCreatingBlueLine] = useState(false);
  const [creatingComposite, setCreatingComposite] = useState(false);
  const [acceptingQuestionnaire, setAcceptingQuestionnaire] = useState(false);

  // Load materials on mount
  useEffect(() => {
    loadMaterials();
  }, []);

  const loadMaterials = async () => {
    try {
      const data = await materialsApi.getAll({ active_only: true });
      setMaterials(data);
    } catch (error: any) {
      toast.error(`Error loading materials: ${error.message}`);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.json') && !file.name.endsWith('.txt')) {
      toast.error('Por favor selecciona un archivo JSON (.json o .txt)');
      return;
    }

    setSelectedFile(file);

    // Preview file content
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      setFilePreview(content);
      
      // Try to extract material code from JSON if available
      try {
        const json = JSON.parse(content);
        let detectedCode: string | null = null;
        
        // Strategy 1: Look for Product Name field which contains [MATERIAL_CODE]
        const productNameField = json.data?.find((item: any) => 
          item.fieldCode === 'q3t1s2f16' || 
          (item.fieldName && item.fieldName.toLowerCase().includes('product name'))
        );
        
        if (productNameField?.value) {
          const productName = productNameField.value;
          // Extract code from format: [BASIL0003] H.E. BASILIC INDES
          if (productName.includes('[') && productName.includes(']')) {
            detectedCode = productName.split(']')[0].replace('[', '');
          }
        }
        
        // Strategy 2: If not found, try Supplier's product code field
        if (!detectedCode) {
          const productCodeField = json.data?.find((item: any) => 
            item.fieldCode === 'q3t1s2f17' || 
            (item.fieldName && item.fieldName.toLowerCase().includes("supplier's product code"))
          );
          
          if (productCodeField?.value) {
            const productCode = productCodeField.value.trim();
            // Try with brackets format: [BASIL0003]
            if (productCode.includes('[') && productCode.includes(']')) {
              detectedCode = productCode.split(']')[0].replace('[', '');
            } else if (productCode) {
              // Try without brackets: BASIL0003
              detectedCode = productCode;
            }
          }
        }
        
        if (detectedCode) {
          setMaterialCode(detectedCode);
          
          // Try to find matching material (materials might not be loaded yet)
          if (materials.length > 0) {
            const material = materials.find(m => m.reference_code === detectedCode);
            if (material) {
              setSelectedMaterialId(material.id);
              toast.success(`Material detectado: ${detectedCode}`);
            } else {
              toast.info(`Código de material detectado: ${detectedCode}. Por favor selecciona el material manualmente.`);
            }
          }
        }
      } catch (err) {
        // Not valid JSON preview, that's ok
      }
    };
    reader.readAsText(file);
  };

  // Update material selection when materials are loaded and materialCode is set
  useEffect(() => {
    if (materialCode && materials.length > 0 && !selectedMaterialId) {
      const material = materials.find(m => m.reference_code === materialCode);
      if (material) {
        setSelectedMaterialId(material.id);
      }
    }
  }, [materials, materialCode, selectedMaterialId]);

  const handleImport = async () => {
    if (!selectedFile) {
      toast.error('Por favor selecciona un archivo JSON');
      return;
    }

    if (!selectedMaterialId && !materialCode) {
      toast.error('Por favor selecciona un material o ingresa un código de material');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      if (selectedMaterialId) {
        formData.append('material_id', selectedMaterialId.toString());
      } else if (materialCode) {
        formData.append('material_code', materialCode);
      }

      const response = await fetch(`${API_URL}${API_PREFIX}/questionnaires/import/json`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al importar cuestionario');
      }

      const result: ImportResult = await response.json();
      
      // Debug: log the result
      console.log('Import result:', result);
      console.log('Comparison:', result.comparison);
      
      toast.success(`✅ Cuestionario importado exitosamente! ID: ${result.id}`);
      
      // Store result to show comparison
      setImportResult(result);
      
      // Scroll to comparison section after a short delay
      setTimeout(() => {
        const comparisonSection = document.getElementById('comparison-section');
        if (comparisonSection) {
          comparisonSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 300);
      
      // If no Blue Line exists, don't navigate yet - show option to create Blue Line
      if (!result.comparison?.blue_line_exists) {
        return;
      }
      
      // If Blue Line exists and no mismatches, auto-navigate
      if (result.comparison.mismatches.length === 0) {
        setTimeout(() => {
          navigate(`/questionnaires/${result.id}`);
        }, 1500);
      }

    } catch (error: any) {
      toast.error(`❌ Error al importar: ${error.message || 'Error desconocido'}`);
    } finally {
      setUploading(false);
    }
  };

  const handleToggleMismatch = (fieldCode: string) => {
    setAcceptedMismatches(prev => {
      const newSet = new Set(prev);
      if (newSet.has(fieldCode)) {
        newSet.delete(fieldCode);
      } else {
        newSet.add(fieldCode);
      }
      return newSet;
    });
  };

  const handleAcceptAllMismatches = () => {
    if (!importResult?.comparison) return;
    const allMismatchCodes = importResult.comparison.mismatches.map(m => m.field_code);
    setAcceptedMismatches(new Set(allMismatchCodes));
  };

  const handleAcceptQuestionnaire = async () => {
    if (!importResult) return;
    
    setAcceptingQuestionnaire(true);
    try {
      const response = await fetch(`${API_URL}${API_PREFIX}/material-suppliers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          questionnaire_id: importResult.id,
          accepted_mismatches: Array.from(acceptedMismatches)
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al aceptar cuestionario');
      }

      const materialSupplier = await response.json();
      toast.success(`✅ Cuestionario aceptado! MaterialSupplier creado (ID: ${materialSupplier.id})`);
      
      setTimeout(() => {
        navigate(`/questionnaires/${importResult.id}`);
      }, 1500);
    } catch (error: any) {
      toast.error(`❌ Error: ${error.message || 'Error desconocido'}`);
    } finally {
      setAcceptingQuestionnaire(false);
    }
  };

  const handleCreateBlueLine = async () => {
    if (!importResult) return;
    
    setCreatingBlueLine(true);
    try {
      const response = await fetch(`${API_URL}${API_PREFIX}/questionnaires/${importResult.id}/create-blue-line?create_composite=false`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al crear Blue Line');
      }

      const result = await response.json();
      toast.success(`✅ Blue Line creada exitosamente! ID: ${result.blue_line_id}`);
      
      // Ask if user wants to create composite
      const createComposite = window.confirm('¿Crear composite Z1 ahora?');
      if (createComposite) {
        await handleCreateComposite(result.blue_line_id);
      } else {
        setTimeout(() => {
          navigate(`/questionnaires/${importResult.id}`);
        }, 1500);
      }
    } catch (error: any) {
      toast.error(`❌ Error: ${error.message || 'Error desconocido'}`);
    } finally {
      setCreatingBlueLine(false);
    }
  };

  const handleCreateComposite = async (blueLineId: number) => {
    setCreatingComposite(true);
    try {
      const response = await fetch(`${API_URL}${API_PREFIX}/blue-line/${blueLineId}/create-composite`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al crear composite');
      }

      const result = await response.json();
      toast.success(`✅ Composite Z1 creado exitosamente! ID: ${result.composite_id}`);
      
      setTimeout(() => {
        navigate(`/questionnaires/${importResult?.id}`);
      }, 1500);
    } catch (error: any) {
      toast.error(`❌ Error: ${error.message || 'Error desconocido'}`);
    } finally {
      setCreatingComposite(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 style={{ color: 'white' }}>Importar Cuestionario JSON</h1>
          <p style={{ color: '#d1d5db', marginTop: '4px' }}>
            Importa un cuestionario en formato JSON de Lluch. El archivo debe seguir la estructura estándar con fieldCode, fieldName, fieldType y value.
          </p>
        </div>
      </div>

      <div className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px' }}>
        <h2 style={{ marginTop: 0, color: 'white', marginBottom: '20px' }}>
          <FileJson size={20} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
          Seleccionar Archivo JSON
        </h2>

        <div style={{ marginBottom: '24px' }}>
          <label
            htmlFor="file-input"
            style={{
              display: 'inline-block',
              padding: '12px 24px',
              backgroundColor: '#374151',
              color: 'white',
              borderRadius: '6px',
              cursor: 'pointer',
              border: '1px solid #4b5563',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#4b5563'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#374151'}
          >
            <Upload size={18} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            {selectedFile ? selectedFile.name : 'Seleccionar archivo JSON'}
          </label>
          <input
            id="file-input"
            type="file"
            accept=".json,.txt"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
        </div>

        {selectedFile && (
          <div style={{
            padding: '12px',
            backgroundColor: '#111827',
            borderRadius: '6px',
            border: '1px solid #374151',
            marginTop: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
              <CheckCircle size={16} style={{ color: '#10b981', marginRight: '8px' }} />
              <span style={{ fontWeight: '500' }}>Archivo seleccionado:</span>
              <span style={{ marginLeft: '8px', color: '#9ca3af' }}>{selectedFile.name}</span>
              <span style={{ marginLeft: '12px', fontSize: '12px', color: '#6b7280' }}>
                ({(selectedFile.size / 1024).toFixed(2)} KB)
              </span>
            </div>
          </div>
        )}

        {filePreview && (
          <div style={{
            marginTop: '16px',
            padding: '12px',
            backgroundColor: '#111827',
            borderRadius: '6px',
            border: '1px solid #374151',
            maxHeight: '200px',
            overflow: 'auto'
          }}>
            <div style={{ fontSize: '12px', color: '#9ca3af', marginBottom: '8px' }}>
              Vista previa del JSON:
            </div>
            <pre style={{
              fontSize: '11px',
              color: '#d1d5db',
              margin: 0,
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}>
              {filePreview.substring(0, 500)}
              {filePreview.length > 500 ? '...' : ''}
            </pre>
          </div>
        )}
      </div>

      <div className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px' }}>
        <h2 style={{ marginTop: 0, color: 'white', marginBottom: '20px' }}>
          Seleccionar Material
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: 'white' }}>
              Material *
            </label>
            <select
              value={selectedMaterialId}
              onChange={(e) => setSelectedMaterialId(e.target.value ? parseInt(e.target.value) : '')}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '6px',
                border: '1px solid #4b5563',
                backgroundColor: '#374151',
                color: 'white'
              }}
            >
              <option value="">Seleccionar Material</option>
              {materials.map(material => (
                <option key={material.id} value={material.id} style={{ backgroundColor: '#374151', color: 'white' }}>
                  {material.reference_code} - {material.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: 'white' }}>
              O ingresa código de material
            </label>
            <input
              type="text"
              value={materialCode}
              onChange={(e) => setMaterialCode(e.target.value)}
              placeholder="Ej: BASIL0003"
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '6px',
                border: '1px solid #4b5563',
                backgroundColor: '#374151',
                color: 'white'
              }}
            />
          </div>
        </div>

        <div style={{
          marginTop: '16px',
          padding: '12px',
          backgroundColor: '#111827',
          borderRadius: '6px',
          border: '1px solid #374151'
        }}>
          <AlertCircle size={16} style={{ color: '#f59e0b', marginRight: '8px', verticalAlign: 'middle' }} />
          <span style={{ fontSize: '14px', color: '#d1d5db' }}>
            El material se puede detectar automáticamente del JSON si contiene un código en formato [MATERIAL_CODE].
            También puedes seleccionarlo manualmente o ingresar el código aquí.
          </span>
        </div>
      </div>

      {importResult && (
        <div id="comparison-section" className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0, color: 'white', marginBottom: '20px' }}>
            Comparación con Blue Line
          </h2>
          
          {importResult.comparison ? (
            importResult.comparison.blue_line_exists ? (
              <>
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                    <div style={{
                      padding: '8px 16px',
                      borderRadius: '6px',
                      backgroundColor: importResult.comparison.score >= 80 ? '#065f46' : importResult.comparison.score >= 50 ? '#92400e' : '#991b1b',
                      color: 'white',
                      fontWeight: '600'
                    }}>
                      Score: {importResult.comparison.score}%
                    </div>
                    <span style={{ color: '#d1d5db' }}>
                      {importResult.comparison.matches} de 10 campos coinciden
                    </span>
                  </div>
                  
                  {importResult.comparison.mismatches.length > 0 && (
                    <div style={{
                      marginTop: '16px',
                      padding: '16px',
                      backgroundColor: '#111827',
                      borderRadius: '6px',
                      border: '1px solid #374151'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                        <h3 style={{ margin: 0, color: 'white', fontSize: '16px' }}>
                          Campos que no coinciden ({importResult.comparison.mismatches.length}):
                        </h3>
                        <button
                          onClick={handleAcceptAllMismatches}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#374151',
                            color: 'white',
                            border: '1px solid #4b5563',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '12px'
                          }}
                        >
                          Aceptar todas
                        </button>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {importResult.comparison.mismatches.map((mismatch, idx) => (
                          <div key={idx} style={{
                            padding: '12px',
                            backgroundColor: mismatch.severity === 'CRITICAL' ? '#7f1d1d' : mismatch.severity === 'WARNING' ? '#78350f' : '#1e293b',
                            borderRadius: '4px',
                            border: `1px solid ${mismatch.severity === 'CRITICAL' ? '#991b1b' : mismatch.severity === 'WARNING' ? '#92400e' : '#334155'}`
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                              <div style={{ flex: 1 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                  <input
                                    type="checkbox"
                                    checked={acceptedMismatches.has(mismatch.field_code)}
                                    onChange={() => handleToggleMismatch(mismatch.field_code)}
                                    style={{ cursor: 'pointer' }}
                                  />
                                  <div style={{ fontWeight: '600', color: 'white' }}>
                                    {mismatch.field_name} ({mismatch.field_code})
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
                              </div>
                              <span style={{
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                fontWeight: '600',
                                backgroundColor: mismatch.severity === 'CRITICAL' ? '#dc2626' : mismatch.severity === 'WARNING' ? '#f59e0b' : '#3b82f6',
                                color: 'white'
                              }}>
                                {mismatch.severity}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {importResult.comparison.mismatches.length === 0 && (
                    <div style={{
                      marginTop: '16px',
                      padding: '16px',
                      backgroundColor: '#065f46',
                      borderRadius: '6px',
                      border: '1px solid #10b981',
                      textAlign: 'center'
                    }}>
                      <CheckCircle size={20} style={{ color: '#10b981', marginRight: '8px', verticalAlign: 'middle' }} />
                      <span style={{ color: 'white', fontWeight: '500' }}>
                        ¡Perfecto! Todos los campos coinciden con la Blue Line.
                      </span>
                    </div>
                  )}
                </div>
                
                <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
                  <button
                    onClick={handleAcceptQuestionnaire}
                    disabled={acceptingQuestionnaire}
                    className="btn-primary"
                    style={{
                      backgroundColor: '#059669',
                      color: 'white',
                      border: 'none',
                      opacity: acceptingQuestionnaire ? 0.5 : 1
                    }}
                  >
                    {acceptingQuestionnaire ? (
                      <>
                        <Loader2 size={18} style={{ marginRight: '8px', animation: 'spin 1s linear infinite' }} />
                        Aceptando...
                      </>
                    ) : (
                      <>
                        <CheckCircle size={18} style={{ marginRight: '8px' }} />
                        Aceptar Cuestionario y Crear MaterialSupplier
                      </>
                    )}
                  </button>
                </div>
              </>
            ) : (
              <>
                <div style={{
                  padding: '16px',
                  backgroundColor: '#111827',
                  borderRadius: '6px',
                  border: '1px solid #374151',
                  marginBottom: '16px'
                }}>
                  <AlertCircle size={20} style={{ color: '#f59e0b', marginRight: '8px', verticalAlign: 'middle' }} />
                  <span style={{ color: '#d1d5db' }}>
                    No existe una Blue Line para este material. Puedes crear una nueva usando este cuestionario.
                  </span>
                </div>
                
                <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                  <button
                    onClick={handleCreateBlueLine}
                    disabled={creatingBlueLine || creatingComposite}
                    className="btn-primary"
                    style={{
                      backgroundColor: '#3b82f6',
                      color: 'white',
                      border: 'none',
                      opacity: (creatingBlueLine || creatingComposite) ? 0.5 : 1
                    }}
                  >
                    {creatingBlueLine ? (
                      <>
                        <Loader2 size={18} style={{ marginRight: '8px', animation: 'spin 1s linear infinite' }} />
                        Creando...
                      </>
                    ) : creatingComposite ? (
                      <>
                        <Loader2 size={18} style={{ marginRight: '8px', animation: 'spin 1s linear infinite' }} />
                        Creando Composite...
                      </>
                    ) : (
                      <>
                        <CheckCircle size={18} style={{ marginRight: '8px' }} />
                        Crear Blue Line desde este Cuestionario
                      </>
                    )}
                  </button>
                </div>
              </>
            )
          ) : (
            <div style={{
              padding: '16px',
              backgroundColor: '#111827',
              borderRadius: '6px',
              border: '1px solid #374151',
              marginBottom: '16px'
            }}>
              <AlertCircle size={20} style={{ color: '#f59e0b', marginRight: '8px', verticalAlign: 'middle' }} />
              <span style={{ color: '#d1d5db' }}>
                Comparación no disponible. Verificando estado...
              </span>
            </div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
        <button
          onClick={() => navigate('/questionnaires')}
          className="btn-secondary"
          style={{ backgroundColor: '#374151', color: 'white', border: '1px solid #4b5563' }}
        >
          Cancelar
        </button>
        <button
          onClick={handleImport}
          disabled={!selectedFile || uploading || (!selectedMaterialId && !materialCode)}
          className="btn-primary"
          style={{
            opacity: (!selectedFile || (!selectedMaterialId && !materialCode)) ? 0.5 : 1,
            cursor: (!selectedFile || (!selectedMaterialId && !materialCode)) ? 'not-allowed' : 'pointer'
          }}
        >
          {uploading ? (
            <>
              <Loader2 size={18} style={{ marginRight: '8px', animation: 'spin 1s linear infinite' }} />
              Importando...
            </>
          ) : (
            <>
              <Upload size={18} style={{ marginRight: '8px' }} />
              Importar Cuestionario
            </>
          )}
        </button>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
