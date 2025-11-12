import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileJson, AlertCircle, CheckCircle, Loader2, ChevronDown, ChevronUp, X } from 'lucide-react';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { materialsApi } from '../services/api';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api';

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
  const [materialCode, setMaterialCode] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [filePreview, setFilePreview] = useState<string>('');
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [acceptedMismatches, setAcceptedMismatches] = useState<Set<string>>(new Set());
  const [creatingBlueLine, setCreatingBlueLine] = useState(false);
  const [creatingComposite, setCreatingComposite] = useState(false);
  const [acceptingQuestionnaire, setAcceptingQuestionnaire] = useState(false);
  const [newMaterialDetected, setNewMaterialDetected] = useState<{ code: string; productName?: string } | null>(null);
  const [similarMaterials, setSimilarMaterials] = useState<Array<{ code: string; name: string; cas?: string; casWarning?: boolean; einecs?: string; einecsMatch?: boolean }> | null>(null);
  const [detectedCAS, setDetectedCAS] = useState<string | null>(null);
  const [detectedEINECS, setDetectedEINECS] = useState<string | null>(null);
  const [showCreateMaterialModal, setShowCreateMaterialModal] = useState(false);
  const [creatingMaterial, setCreatingMaterial] = useState(false);
  const [newMaterial, setNewMaterial] = useState({
    reference_code: '',
    name: '',
    material_type: 'NATURAL',
    supplier: '',
    cas_number: '',
    description: '',
    is_active: true
  });

  // Material detection is automatic from JSON, no need to load materials list

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.json') && !file.name.endsWith('.txt')) {
      toast.error('Por favor selecciona un archivo JSON (.json o .txt)');
      return;
    }

    setSelectedFile(file);
    
    // Reset states when selecting a new file
    setNewMaterialDetected(null);
    setImportResult(null);
    setMaterialCode('');

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
          toast.success(`✅ Código de material detectado: ${detectedCode}`);
        }
      } catch (err) {
        // Not valid JSON preview, that's ok
      }
    };
    reader.readAsText(file);
  };

  // Material detection is automatic from JSON

  const handleImport = async () => {
    if (!selectedFile) {
      toast.error('Por favor selecciona un archivo JSON');
      return;
    }

    // Allow import without material selection - backend will try to detect from JSON
    // if (!selectedMaterialId && !materialCode) {
    //   toast.error('Por favor selecciona un material o ingresa un código de material');
    //   return;
    // }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Don't send material_id or material_code - let backend detect it automatically from JSON
      // This ensures proper handling of new materials

      const response = await fetch(`${API_URL}${API_PREFIX}/questionnaires/import/json`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData.detail || 'Error al importar cuestionario';
        
        console.log('Import error:', errorMessage); // Debug log
        
        // Check if similar materials were found
        if (errorMessage.includes('SIMILAR_MATERIALS_FOUND:')) {
          console.log('Similar materials found!'); // Debug log
          
          // Extract material code from error message
          const match = errorMessage.match(/material '([^']+)'/);
          const detectedCode = match ? match[1] : materialCode || 'UNKNOWN';
          
          // Extract similar materials from error message
          // Format: "SIMILAR_MATERIALS_FOUND: ... BASC005 (BASIL INDIA OIL) - EINECS: 283-900-8✅ - CAS: 84775-71-3 ⚠️ (CAS diferente) | ..."
          const similarMatch = errorMessage.match(/materiales similares: (.+?)\./);
          let similarMaterialsList: Array<{ code: string; name: string; cas?: string; casWarning?: boolean; einecs?: string; einecsMatch?: boolean }> = [];
          
          if (similarMatch) {
            const similarText = similarMatch[1];
            // Parse format: "BASC005 (BASIL INDIA OIL) - EINECS: 283-900-8✅ - CAS: 84775-71-3 ⚠️ (CAS diferente) | BASIL0003 (H.E. BASILIC INDES) - EINECS: N/A - CAS: 8015-73-4"
            const materials = similarText.split('|').map((m: string) => m.trim());
            similarMaterialsList = materials.map((m: string) => {
              // Extract code and name: "BASC005 (BASIL INDIA OIL)" or "BASIL0003 (H.E. BASILIC INDES)"
              // Improved regex: match code (letters/numbers) followed by optional space and parentheses with name
              // Use non-greedy match to handle names with parentheses
              const codeNameMatch = m.match(/^([A-Z0-9]+)\s*\(([^)]+(?:\([^)]*\)[^)]*)*)\)/);
              if (codeNameMatch) {
                const code = codeNameMatch[1].trim();
                const name = codeNameMatch[2].trim();
                
                // Validate code: should only contain letters and numbers, no spaces or special chars
                if (!/^[A-Z0-9]+$/.test(code)) {
                  console.warn(`Invalid material code extracted: "${code}" from "${m}"`);
                  // Try to extract just the first word as code
                  const firstWord = m.split(/\s+/)[0];
                  if (/^[A-Z0-9]+$/.test(firstWord)) {
                    return { code: firstWord, name: m.replace(firstWord, '').trim(), cas: undefined, casWarning: false };
                  }
                }
                
                // Extract EINECS: "EINECS: 283-900-8✅" or "EINECS: N/A"
                const einecsMatch = m.match(/EINECS:\s*([\d-]+|N\/A)/);
                const einecs = einecsMatch && einecsMatch[1] !== 'N/A' ? einecsMatch[1] : undefined;
                const einecsMatchIndicator = m.includes('✅') && einecs !== undefined;
                
                // Extract CAS: "CAS: 84775-71-3"
                const casMatch = m.match(/CAS:\s*([\d-]+)/);
                const cas = casMatch ? casMatch[1] : undefined;
                
                // Check if there's a CAS warning
                const casWarning = m.includes('⚠️') || m.includes('CAS diferente');
                
                return { code, name, cas, casWarning, einecs, einecsMatch: einecsMatchIndicator };
              }
              
              // Fallback: try to extract code as first word (before any space or parenthesis)
              const firstPart = m.split(/\s|\(/)[0];
              if (/^[A-Z0-9]+$/.test(firstPart)) {
                return { code: firstPart, name: m.replace(firstPart, '').trim(), cas: undefined, casWarning: false };
              }
              
              // Last fallback: use whole string as code (shouldn't happen)
              console.warn(`Could not parse material code from: "${m}"`);
              return { code: m.split(/\s/)[0] || m, name: m };
            });
          }
          
          // Try to extract product name, CAS and EINECS from JSON
          let productName = '';
          let casNumber = '';
          let einecsNumber = '';
          try {
            const jsonContent = filePreview || (selectedFile ? await selectedFile.text() : '');
            if (jsonContent) {
              const json = JSON.parse(jsonContent);
              const productNameField = json.data?.find((item: any) => 
                item.fieldCode === 'q3t1s2f16' || 
                (item.fieldName && item.fieldName.toLowerCase().includes('product name'))
              );
              if (productNameField?.value) {
                productName = productNameField.value;
              }
              
              const casField = json.data?.find((item: any) => 
                item.fieldCode === 'q3t1s2f23' || 
                (item.fieldName && item.fieldName.toLowerCase().includes('cas'))
              );
              if (casField?.value) {
                casNumber = casField.value;
              }
              
              const einecsField = json.data?.find((item: any) => 
                item.fieldCode === 'q3t1s2f24' || 
                (item.fieldName && item.fieldName.toLowerCase().includes('einecs'))
              );
              if (einecsField?.value) {
                einecsNumber = einecsField.value;
              }
            }
          } catch (e) {
            console.error('Error parsing JSON for product info:', e);
          }
          
          // Set state to show similar materials UI
          setSimilarMaterials(similarMaterialsList);
          setDetectedCAS(casNumber || null);
          setDetectedEINECS(einecsNumber || null);
          setNewMaterialDetected({ code: detectedCode, productName });
          
          // Show toast notification
          toast.info(`🔍 Se encontraron ${similarMaterialsList.length} material(es) similar(es). ¿Es uno de estos?`);
          
          // Scroll to the similar materials section after a short delay
          setTimeout(() => {
            const similarSection = document.getElementById('similar-materials-section');
            if (similarSection) {
              similarSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          }, 300);
          
          return; // Don't throw error, show UI instead
        }
        
        // Check if this is a new material detection
        if (errorMessage.includes('NEW_MATERIAL_DETECTED:')) {
          console.log('New material detected!'); // Debug log
          
          // Extract material code from error message
          const match = errorMessage.match(/material '([^']+)'/);
          const detectedCode = match ? match[1] : materialCode || 'UNKNOWN';
          
          console.log('Detected code:', detectedCode); // Debug log
          
          // Try to extract product name from JSON (use filePreview if available)
          let productName = '';
          try {
            // Always use filePreview if available, otherwise try to read file again
            const jsonContent = filePreview || (selectedFile ? await selectedFile.text() : '');
            if (jsonContent) {
              const json = JSON.parse(jsonContent);
              const productNameField = json.data?.find((item: any) => 
                item.fieldCode === 'q3t1s2f16' || 
                (item.fieldName && item.fieldName.toLowerCase().includes('product name'))
              );
              if (productNameField?.value) {
                productName = productNameField.value;
                console.log('Product name extracted:', productName); // Debug log
              }
            }
          } catch (e) {
            console.error('Error parsing JSON for product name:', e); // Debug log
            // Ignore parsing errors
          }
          
          // Extract additional info from JSON for material creation
          let casNumber = '';
          let supplierName = '';
          try {
            const jsonContent = filePreview || (selectedFile ? await selectedFile.text() : '');
            if (jsonContent) {
              const json = JSON.parse(jsonContent);
              // Extract CAS
              const casField = json.data?.find((item: any) => 
                item.fieldCode === 'q3t1s2f23' || 
                (item.fieldName && item.fieldName.toLowerCase().includes('cas'))
              );
              if (casField?.value) {
                casNumber = casField.value;
              }
              // Extract Supplier Name
              const supplierField = json.data?.find((item: any) => 
                item.fieldCode === 'q3t1s2f15' || 
                (item.fieldName && item.fieldName.toLowerCase().includes('supplier name'))
              );
              if (supplierField?.value) {
                supplierName = supplierField.value;
              }
            }
          } catch (e) {
            console.error('Error extracting material info:', e);
          }
          
          // Clear similar materials if any
          setSimilarMaterials(null);
          
          // Set state to show new material UI
          setNewMaterialDetected({ code: detectedCode, productName });
          
          // Pre-fill material form with detected info
          setNewMaterial({
            reference_code: detectedCode,
            name: productName.replace(/\[.*?\]\s*/, '').trim() || detectedCode, // Remove [CODE] prefix
            material_type: 'NATURAL',
            supplier: supplierName,
            cas_number: casNumber,
            description: `Material creado automáticamente desde cuestionario importado`,
            is_active: true
          });
          
          console.log('Setting newMaterialDetected state'); // Debug log
          
          // Show toast notification
          toast.warning(`⚠️ Material nuevo detectado: ${detectedCode}`);
          
          // Scroll to the new material section after a short delay
          setTimeout(() => {
            const newMaterialSection = document.getElementById('new-material-section');
            if (newMaterialSection) {
              newMaterialSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
          }, 300);
          
          return; // Don't throw error, show UI instead
        }
        
        // For other errors, show error toast
        toast.error(`❌ Error al importar: ${errorMessage}`);
        throw new Error(errorMessage);
      }

      const result: ImportResult = await response.json();
      
      // Debug: log the result
      console.log('Import result:', result);
      console.log('Comparison:', result.comparison);
      
      // Check if this is a duplicate (same questionnaire already imported)
      // The backend will return the existing questionnaire if request_id matches
      const isDuplicate = importResult !== null && importResult.id === result.id;
      
      if (isDuplicate) {
        toast.info(`ℹ️ Este cuestionario ya fue importado anteriormente (ID: ${result.id}). Mostrando cuestionario existente.`);
      } else {
        toast.success(`✅ Cuestionario importado exitosamente! ID: ${result.id}`);
      }
      
      // Store result to show comparison
      setImportResult(result);
      
      // Scroll to comparison section after a short delay
      setTimeout(() => {
        const comparisonSection = document.getElementById('comparison-section');
        if (comparisonSection) {
          comparisonSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }, 300);
      
      // Don't auto-navigate - let user decide when to go to questionnaire
      // Show comparison results and let user manually navigate

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
      
      // Don't auto-navigate - let user decide when to go to questionnaire
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
      
      // Update importResult to reflect that Blue Line now exists
      // This allows the UI to show the success state and enable continuation
      setImportResult({
        ...importResult,
        comparison: {
          blue_line_exists: true,
          matches: 0,
          mismatches: [],
          score: 100,
          message: "Blue Line creada exitosamente desde este cuestionario. El MaterialSupplier ha sido creado automáticamente."
        }
      });
      
      // Ask if user wants to create composite
      const createComposite = window.confirm('¿Crear composite Z1 ahora?');
      if (createComposite) {
        await handleCreateComposite(result.blue_line_id);
      }
      // Don't auto-navigate - let user decide when to go to questionnaire
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
      
      // Don't auto-navigate - let user decide when to go to questionnaire
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
          <input
            id="file-input"
            type="file"
            accept=".json,.txt"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
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
              transition: 'background-color 0.2s',
              userSelect: 'none'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#4b5563'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#374151'}
          >
            <Upload size={18} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            {selectedFile ? selectedFile.name : 'Seleccionar archivo JSON'}
          </label>
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

      {materialCode && (
        <div className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px', border: '2px solid #10b981' }}>
          <h2 style={{ marginTop: 0, color: '#10b981', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={24} style={{ color: '#10b981' }} />
            Material Detectado Automáticamente
          </h2>
          
          <div style={{
            padding: '16px',
            backgroundColor: '#065f46',
            borderRadius: '6px',
            border: '1px solid #10b981',
            marginBottom: '16px'
          }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '4px' }}>Código del Material:</div>
              <div style={{ fontSize: '20px', fontWeight: '600', color: '#10b981' }}>{materialCode}</div>
            </div>
            
            <div style={{
              padding: '12px',
              backgroundColor: '#064e3b',
              borderRadius: '6px',
              border: '1px solid #047857',
              marginTop: '12px'
            }}>
              <CheckCircle size={18} style={{ color: '#10b981', marginRight: '8px', verticalAlign: 'middle' }} />
              <span style={{ color: '#d1d5db', fontSize: '14px' }}>
                El código del material fue detectado automáticamente del JSON. 
                Haz clic en "Validar Cuestionario" para importar y comparar con la Blue Line.
                Si el material no existe, el sistema te guiará para crearlo.
              </span>
            </div>
          </div>
        </div>
      )}

      {!materialCode && (
        <div className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0, color: 'white', marginBottom: '20px' }}>
            Información del Material
          </h2>
          
          <div style={{
            padding: '16px',
            backgroundColor: '#111827',
            borderRadius: '6px',
            border: '1px solid #374151'
          }}>
            <AlertCircle size={20} style={{ color: '#f59e0b', marginRight: '8px', verticalAlign: 'middle' }} />
            <span style={{ color: '#d1d5db', fontSize: '14px' }}>
              <strong>💡 El material se detecta automáticamente del JSON.</strong> 
              El sistema buscará el código del material en el campo "Product Name" o "Supplier's product code" 
              con formato [MATERIAL_CODE]. Si el material no existe, el sistema te guiará para crearlo después de importar.
            </span>
          </div>
        </div>
      )}

      {similarMaterials && similarMaterials.length > 0 && (
        <div id="similar-materials-section" className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px', border: '2px solid #3b82f6' }}>
          <h2 style={{ marginTop: 0, color: '#3b82f6', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={24} style={{ color: '#3b82f6' }} />
            Materiales Similares Encontrados
          </h2>
          
          <div style={{
            padding: '16px',
            backgroundColor: '#111827',
            borderRadius: '6px',
            border: '1px solid #374151',
            marginBottom: '16px'
          }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '4px' }}>Código detectado:</div>
              <div style={{ fontSize: '18px', fontWeight: '600', color: '#3b82f6' }}>{newMaterialDetected?.code || 'N/A'}</div>
              {detectedEINECS && (
                <div style={{ marginTop: '8px' }}>
                  <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '4px' }}>EINECS del cuestionario:</div>
                  <div style={{ fontSize: '16px', fontWeight: '500', color: '#10b981' }}>{detectedEINECS} ✅</div>
                  <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px', fontStyle: 'italic' }}>
                    Si coincide exactamente con otro material, es muy probable que sea el mismo (incluso si el CAS es diferente)
                  </div>
                </div>
              )}
              {detectedCAS && (
                <div style={{ marginTop: '8px' }}>
                  <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '4px' }}>CAS del cuestionario:</div>
                  <div style={{ fontSize: '16px', fontWeight: '500', color: '#d1d5db' }}>{detectedCAS}</div>
                </div>
              )}
            </div>
            
            <div style={{
              padding: '12px',
              backgroundColor: '#1e3a5f',
              borderRadius: '6px',
              border: '1px solid #3b82f6',
              marginTop: '16px',
              marginBottom: '16px'
            }}>
              <AlertCircle size={18} style={{ color: '#3b82f6', marginRight: '8px', verticalAlign: 'middle' }} />
              <span style={{ color: '#d1d5db', fontSize: '14px' }}>
                El sistema encontró materiales similares en la base de datos. ¿Es uno de estos el material correcto?
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '16px' }}>
              {similarMaterials.map((mat, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '16px',
                    backgroundColor: '#1e3a5f',
                    borderRadius: '6px',
                    border: '2px solid #3b82f6',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#2563eb';
                    e.currentTarget.style.borderColor = '#60a5fa';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#1e3a5f';
                    e.currentTarget.style.borderColor = '#3b82f6';
                  }}
                  onClick={async () => {
                    // Use this material for import
                    let selectedMaterialCode = mat.code.trim();
                    
                    // Validate and clean the material code
                    // Remove any spaces, parentheses, or special characters that might have been included
                    selectedMaterialCode = selectedMaterialCode.split(/\s|\(/)[0].trim();
                    
                    // Final validation: code should only contain letters and numbers
                    if (!/^[A-Z0-9]+$/.test(selectedMaterialCode)) {
                      console.error(`Invalid material code: "${selectedMaterialCode}" (original: "${mat.code}")`);
                      toast.error(`❌ Código de material inválido: ${selectedMaterialCode}. Por favor, intenta de nuevo.`);
                      return;
                    }
                    
                    console.log(`Selected material code: "${selectedMaterialCode}" (from "${mat.code}")`);
                    
                    setMaterialCode(selectedMaterialCode);
                    setSimilarMaterials(null);
                    setNewMaterialDetected(null);
                    toast.success(`✅ Material seleccionado: ${selectedMaterialCode} - ${mat.name}`);
                    
                    // Retry import with selected material code
                    if (selectedFile) {
                      setUploading(true);
                      try {
                        const formData = new FormData();
                        formData.append('file', selectedFile);
                        formData.append('material_code', selectedMaterialCode);

                        const response = await fetch(`${API_URL}${API_PREFIX}/questionnaires/import/json`, {
                          method: 'POST',
                          body: formData,
                        });

                        if (!response.ok) {
                          const errorData = await response.json();
                          const errorMessage = errorData.detail || 'Error al importar cuestionario';
                          toast.error(`❌ Error al importar: ${errorMessage}`);
                          setUploading(false);
                          return;
                        }

                        const result: ImportResult = await response.json();
                        toast.success(`✅ Cuestionario importado exitosamente! ID: ${result.id}`);
                        setImportResult(result);
                        
                        setTimeout(() => {
                          const comparisonSection = document.getElementById('comparison-section');
                          if (comparisonSection) {
                            comparisonSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
                          }
                        }, 300);
                      } catch (error: any) {
                        toast.error(`❌ Error al importar: ${error.message || 'Error desconocido'}`);
                      } finally {
                        setUploading(false);
                      }
                    }
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div 
                      style={{ 
                        fontSize: '16px', 
                        fontWeight: '600', 
                        color: 'white', 
                        marginBottom: '4px',
                        wordBreak: 'break-word',
                        overflowWrap: 'break-word'
                      }}
                      title={mat.code}
                    >
                      {mat.code}
                    </div>
                    <div style={{ 
                      fontSize: '14px', 
                      color: '#9ca3af', 
                      marginBottom: '4px',
                      wordBreak: 'break-word',
                      overflowWrap: 'break-word'
                    }}>
                      {mat.name}
                    </div>
                    {mat.einecs && (
                      <div style={{ fontSize: '12px', color: mat.einecsMatch ? '#10b981' : '#6b7280', marginTop: '4px', fontWeight: mat.einecsMatch ? '600' : 'normal' }}>
                        EINECS: {mat.einecs}
                        {mat.einecsMatch && (
                          <span style={{ marginLeft: '6px' }}>✅ Coincide exactamente</span>
                        )}
                      </div>
                    )}
                    {mat.cas && (
                      <div style={{ fontSize: '12px', color: mat.casWarning ? '#f59e0b' : '#6b7280', marginTop: '4px' }}>
                        CAS: {mat.cas}
                        {mat.casWarning && (
                          <span style={{ marginLeft: '6px', fontWeight: '600' }}>⚠️ Diferente al cuestionario</span>
                        )}
                      </div>
                    )}
                  </div>
                  <div style={{
                    padding: '6px 12px',
                    backgroundColor: '#3b82f6',
                    color: 'white',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: '600'
                  }}>
                    Usar este
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button
              onClick={() => {
                setSimilarMaterials(null);
                setNewMaterialDetected(null);
                setMaterialCode('');
              }}
              className="btn-secondary"
              style={{ backgroundColor: '#374151', color: 'white', border: '1px solid #4b5563' }}
            >
              Cancelar
            </button>
            <button
              onClick={() => {
                // Show new material creation UI
                setSimilarMaterials(null);
                // Keep newMaterialDetected to show creation form
              }}
              className="btn-primary"
              style={{ backgroundColor: '#f59e0b', color: 'white', border: 'none' }}
            >
              Crear Material Nuevo
            </button>
          </div>
        </div>
      )}

      {newMaterialDetected && !similarMaterials && (
        <div id="new-material-section" className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px', border: '2px solid #f59e0b' }}>
          <h2 style={{ marginTop: 0, color: '#f59e0b', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={24} style={{ color: '#f59e0b' }} />
            Material Nuevo Detectado
          </h2>
          
          <div style={{
            padding: '16px',
            backgroundColor: '#111827',
            borderRadius: '6px',
            border: '1px solid #374151',
            marginBottom: '16px'
          }}>
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '4px' }}>Código del Material:</div>
              <div style={{ fontSize: '18px', fontWeight: '600', color: '#f59e0b' }}>{newMaterialDetected.code}</div>
            </div>
            
            {newMaterialDetected.productName && (
              <div style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '14px', color: '#9ca3af', marginBottom: '4px' }}>Nombre del Producto:</div>
                <div style={{ fontSize: '16px', color: '#d1d5db' }}>{newMaterialDetected.productName}</div>
              </div>
            )}
            
            <div style={{
              padding: '12px',
              backgroundColor: '#78350f',
              borderRadius: '6px',
              border: '1px solid #92400e',
              marginTop: '16px'
            }}>
              <AlertCircle size={18} style={{ color: '#f59e0b', marginRight: '8px', verticalAlign: 'middle' }} />
              <span style={{ color: '#fbbf24', fontSize: '14px' }}>
                Este material no existe en el sistema. Por favor, crea primero el material antes de importar el cuestionario.
              </span>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button
              onClick={() => {
                setNewMaterialDetected(null);
                setMaterialCode('');
              }}
              className="btn-secondary"
              style={{ backgroundColor: '#374151', color: 'white', border: '1px solid #4b5563' }}
            >
              Cerrar
            </button>
            <button
              onClick={() => {
                setShowCreateMaterialModal(true);
              }}
              className="btn-primary"
              style={{ backgroundColor: '#3b82f6', color: 'white', border: 'none' }}
            >
              Crear Material Ahora
            </button>
          </div>
        </div>
      )}

      {importResult && (
        <div id="comparison-section" className="card" style={{ backgroundColor: '#1f2937', color: 'white', marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0, color: 'white', marginBottom: '20px' }}>
            Resultado de la Importación
          </h2>
          
          {/* Success message when Blue Line exists */}
          {importResult.comparison?.blue_line_exists && (
            <div style={{
              marginBottom: '20px',
              padding: '16px',
              backgroundColor: '#065f46',
              borderRadius: '6px',
              border: '1px solid #10b981',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <CheckCircle size={24} style={{ color: '#10b981', flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ color: 'white', fontWeight: '600', marginBottom: '4px' }}>
                  ✅ {importResult.comparison.message || 'Cuestionario validado con Blue Line'}
                </div>
                <div style={{ color: '#d1d5db', fontSize: '14px' }}>
                  {importResult.comparison.message 
                    ? importResult.comparison.message
                    : 'El cuestionario ha sido importado exitosamente y comparado con la Blue Line existente. Puedes revisar los detalles de la comparación a continuación.'}
                </div>
              </div>
            </div>
          )}
          
          {importResult.comparison ? (
            importResult.comparison.blue_line_exists ? (
              <>
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '16px', 
                    marginBottom: '16px',
                    padding: '16px',
                    backgroundColor: importResult.comparison.score >= 80 ? '#065f46' : importResult.comparison.score >= 50 ? '#92400e' : '#991b1b',
                    borderRadius: '8px',
                    border: `2px solid ${importResult.comparison.score >= 80 ? '#10b981' : importResult.comparison.score >= 50 ? '#f59e0b' : '#dc2626'}`
                  }}>
                    <div style={{
                      padding: '10px 20px',
                      borderRadius: '6px',
                      backgroundColor: 'rgba(0, 0, 0, 0.3)',
                      color: 'white',
                      fontWeight: '700',
                      fontSize: '18px'
                    }}>
                      Score de Validación: {importResult.comparison.score}%
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ color: 'white', fontWeight: '600', marginBottom: '4px' }}>
                        Comparación Completa con Blue Line
                      </div>
                      <div style={{ color: '#d1d5db', fontSize: '14px' }}>
                        {importResult.comparison.matches + importResult.comparison.mismatches.length} campos comparados • {importResult.comparison.matches} coinciden • {importResult.comparison.mismatches.length} con diferencias
                      </div>
                    </div>
                  </div>
                  
                  {importResult.comparison.mismatches.length > 0 && (
                    <div style={{
                      marginTop: '20px',
                      padding: '20px',
                      backgroundColor: '#111827',
                      borderRadius: '8px',
                      border: '2px solid #dc2626',
                      boxShadow: '0 4px 6px rgba(220, 38, 38, 0.2)'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                        <h3 style={{ margin: 0, color: '#fee2e2', fontSize: '18px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <AlertCircle size={20} style={{ color: '#dc2626' }} />
                          Campos que NO coinciden ({importResult.comparison.mismatches.length}):
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
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {importResult.comparison.mismatches.map((mismatch, idx) => (
                          <div key={idx} style={{
                            padding: '16px',
                            backgroundColor: '#7f1d1d',
                            borderRadius: '6px',
                            border: '2px solid #dc2626',
                            boxShadow: '0 2px 4px rgba(220, 38, 38, 0.3)'
                          }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                              <div style={{ flex: 1 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                                  <input
                                    type="checkbox"
                                    checked={acceptedMismatches.has(mismatch.field_code)}
                                    onChange={() => handleToggleMismatch(mismatch.field_code)}
                                    style={{ 
                                      cursor: 'pointer',
                                      width: '18px',
                                      height: '18px',
                                      accentColor: '#10b981'
                                    }}
                                  />
                                  <div style={{ fontWeight: '700', color: '#fee2e2', fontSize: '15px' }}>
                                    ❌ {mismatch.field_name}
                                  </div>
                                  <span style={{
                                    padding: '4px 10px',
                                    borderRadius: '4px',
                                    fontSize: '11px',
                                    fontWeight: '700',
                                    backgroundColor: '#dc2626',
                                    color: 'white',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.5px'
                                  }}>
                                    {mismatch.severity}
                                  </span>
                                </div>
                                <div style={{ 
                                  padding: '10px',
                                  backgroundColor: '#991b1b',
                                  borderRadius: '4px',
                                  marginBottom: '8px',
                                  border: '1px solid #dc2626'
                                }}>
                                  <div style={{ fontSize: '12px', color: '#fca5a5', marginBottom: '4px', fontWeight: '600' }}>
                                    Esperado (Blue Line):
                                  </div>
                                  <div style={{ fontSize: '14px', color: '#fee2e2', fontWeight: '500' }}>
                                    {mismatch.expected_value || 'No especificado'}
                                  </div>
                                </div>
                                <div style={{ 
                                  padding: '10px',
                                  backgroundColor: '#7f1d1d',
                                  borderRadius: '4px',
                                  border: '1px solid #dc2626'
                                }}>
                                  <div style={{ fontSize: '12px', color: '#fca5a5', marginBottom: '4px', fontWeight: '600' }}>
                                    Actual (Cuestionario):
                                  </div>
                                  <div style={{ fontSize: '14px', color: '#fee2e2', fontWeight: '500' }}>
                                    {mismatch.actual_value || 'N/A'}
                                  </div>
                                </div>
                                <div style={{ 
                                  fontSize: '11px', 
                                  color: '#9ca3af', 
                                  marginTop: '8px',
                                  fontStyle: 'italic'
                                }}>
                                  Código: {mismatch.field_code}
                                </div>
                              </div>
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
                        {importResult.comparison.message?.includes('creada exitosamente') 
                          ? '✅ Blue Line creada exitosamente. El MaterialSupplier ha sido creado automáticamente.'
                          : '¡Perfecto! Todos los campos coinciden con la Blue Line.'}
                      </span>
                      <div style={{ marginTop: '12px' }}>
                        <button
                          onClick={() => navigate(`/questionnaires/${importResult.id}`)}
                          className="btn-primary"
                          style={{
                            backgroundColor: '#10b981',
                            color: 'white',
                            border: 'none',
                            padding: '8px 16px',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontWeight: '500'
                          }}
                        >
                          Ver Cuestionario Importado
                        </button>
                      </div>
                    </div>
                  )}
                </div>
                
                <div style={{ display: 'flex', gap: '12px', marginTop: '20px', flexWrap: 'wrap' }}>
                  {/* Only show "Accept Questionnaire" button if MaterialSupplier hasn't been created yet */}
                  {!importResult.comparison.message?.includes('MaterialSupplier ha sido creado') && (
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
                  )}
                  <button
                    onClick={() => navigate(`/questionnaires/${importResult.id}`)}
                    className="btn-secondary"
                    style={{
                      backgroundColor: '#374151',
                      color: 'white',
                      border: '1px solid #4b5563'
                    }}
                  >
                    Ver Cuestionario Importado
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
          disabled={!selectedFile || uploading || (importResult !== null && !newMaterialDetected && !similarMaterials)}
          className="btn-primary"
          style={{
            opacity: (!selectedFile || (importResult !== null && !newMaterialDetected && !similarMaterials)) ? 0.5 : 1,
            cursor: (!selectedFile || (importResult !== null && !newMaterialDetected && !similarMaterials)) ? 'not-allowed' : 'pointer',
            backgroundColor: materialCode ? '#3b82f6' : '#059669'
          }}
        >
          {uploading ? (
            <>
              <Loader2 size={18} style={{ marginRight: '8px', animation: 'spin 1s linear infinite' }} />
              {materialCode ? 'Validando...' : 'Importando...'}
            </>
          ) : (
            <>
              {importResult !== null && !newMaterialDetected && !similarMaterials ? (
                <>
                  <CheckCircle size={18} style={{ marginRight: '8px' }} />
                  Ya Importado
                </>
              ) : materialCode ? (
                <>
                  <CheckCircle size={18} style={{ marginRight: '8px' }} />
                  Validar Cuestionario
                </>
              ) : (
                <>
                  <Upload size={18} style={{ marginRight: '8px' }} />
                  Importar Cuestionario
                </>
              )}
            </>
          )}
        </button>
      </div>

      {/* Modal para crear material */}
      {showCreateMaterialModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: '#1f2937',
            borderRadius: '12px',
            padding: '2rem',
            maxWidth: '600px',
            width: '90%',
            maxHeight: '90vh',
            overflow: 'auto',
            border: '2px solid #374151'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ margin: 0, color: 'white', fontSize: '1.5rem', fontWeight: 600 }}>Crear Nuevo Material</h2>
              <button 
                onClick={() => setShowCreateMaterialModal(false)}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  fontSize: '1.5rem', 
                  cursor: 'pointer',
                  color: '#9ca3af',
                  padding: '0.25rem',
                  borderRadius: '4px',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseEnter={(e) => (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#374151'}
                onMouseLeave={(e) => (e.currentTarget as HTMLButtonElement).style.backgroundColor = 'transparent'}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'white', fontSize: '0.9rem' }}>
                  Código de Referencia *
                </label>
                <input
                  type="text"
                  value={newMaterial.reference_code}
                  onChange={(e) => setNewMaterial({ ...newMaterial, reference_code: e.target.value })}
                  placeholder="Ej: JASMINE001"
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #4b5563', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: '#374151',
                    color: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'white', fontSize: '0.9rem' }}>
                  Nombre *
                </label>
                <input
                  type="text"
                  value={newMaterial.name}
                  onChange={(e) => setNewMaterial({ ...newMaterial, name: e.target.value })}
                  placeholder="Nombre del material"
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #4b5563', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: '#374151',
                    color: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'white', fontSize: '0.9rem' }}>
                  Tipo de Material
                </label>
                <select
                  value={newMaterial.material_type}
                  onChange={(e) => setNewMaterial({ ...newMaterial, material_type: e.target.value })}
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #4b5563', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: '#374151',
                    color: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                >
                  <option value="NATURAL">Natural</option>
                  <option value="SYNTHETIC">Sintético</option>
                  <option value="BLEND">Mezcla</option>
                </select>
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'white', fontSize: '0.9rem' }}>
                  Proveedor
                </label>
                <input
                  type="text"
                  value={newMaterial.supplier}
                  onChange={(e) => setNewMaterial({ ...newMaterial, supplier: e.target.value })}
                  placeholder="Nombre del proveedor"
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #4b5563', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: '#374151',
                    color: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'white', fontSize: '0.9rem' }}>
                  Número CAS
                </label>
                <input
                  type="text"
                  value={newMaterial.cas_number}
                  onChange={(e) => setNewMaterial({ ...newMaterial, cas_number: e.target.value })}
                  placeholder="Ej: 8008-56-8"
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #4b5563', 
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    backgroundColor: '#374151',
                    color: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600, color: 'white', fontSize: '0.9rem' }}>
                  Descripción
                </label>
                <textarea
                  value={newMaterial.description}
                  onChange={(e) => setNewMaterial({ ...newMaterial, description: e.target.value })}
                  placeholder="Descripción del material"
                  rows={3}
                  style={{ 
                    width: '100%', 
                    padding: '0.75rem', 
                    border: '1px solid #4b5563', 
                    borderRadius: '8px', 
                    resize: 'vertical',
                    fontSize: '0.9rem',
                    backgroundColor: '#374151',
                    color: 'white',
                    transition: 'border-color 0.2s ease'
                  }}
                />
              </div>
            </div>

            <div style={{ 
              display: 'flex', 
              gap: '1rem', 
              marginTop: '2rem',
              paddingTop: '1rem',
              borderTop: '1px solid #374151'
            }}>
              <button 
                className="btn-primary"
                onClick={async () => {
                  if (!newMaterial.name || !newMaterial.reference_code) {
                    toast.error('Por favor completa los campos obligatorios (Nombre y Código de Referencia)');
                    return;
                  }

                  setCreatingMaterial(true);
                  try {
                    const createdMaterial = await materialsApi.create(newMaterial);
                    toast.success(`✅ Material creado exitosamente: ${createdMaterial.reference_code}`);
                    setShowCreateMaterialModal(false);
                    setNewMaterialDetected(null);
                    
                    // Automatically retry import after creating material
                    if (selectedFile) {
                      toast.info('Reintentando importar cuestionario...');
                      setTimeout(() => {
                        handleImport();
                      }, 1000);
                    }
                  } catch (error: any) {
                    toast.error(`❌ Error al crear material: ${error.message || 'Error desconocido'}`);
                  } finally {
                    setCreatingMaterial(false);
                  }
                }}
                disabled={creatingMaterial}
                style={{ 
                  flex: 1,
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  borderRadius: '8px',
                  backgroundColor: creatingMaterial ? '#4b5563' : '#3b82f6',
                  color: 'white',
                  border: 'none',
                  cursor: creatingMaterial ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                {creatingMaterial ? (
                  <>
                    <Loader2 size={18} style={{ marginRight: '8px', animation: 'spin 1s linear infinite', display: 'inline-block' }} />
                    Creando...
                  </>
                ) : (
                  'Crear Material'
                )}
              </button>
              <button 
                onClick={() => setShowCreateMaterialModal(false)}
                style={{ 
                  flex: 1, 
                  background: '#374151',
                  color: 'white',
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.9rem',
                  fontWeight: 600,
                  borderRadius: '8px',
                  border: '1px solid #4b5563',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
