import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { materialsApi } from '../services/api';
import { Upload, FileJson, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = '/api';

interface Material {
  id: number;
  reference_code: string;
  name: string;
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
        // Look for Product Name field which contains [MATERIAL_CODE]
        const productNameField = json.data?.find((item: any) => 
          item.fieldCode === 'q3t1s2f16' || 
          (item.fieldName && item.fieldName.toLowerCase().includes('product name'))
        );
        
        if (productNameField?.value) {
          const productName = productNameField.value;
          // Extract code from format: [BASIL0003] H.E. BASILIC INDES
          if (productName.includes('[') && productName.includes(']')) {
            const code = productName.split(']')[0].replace('[', '');
            setMaterialCode(code);
            
            // Try to find matching material (materials might not be loaded yet)
            if (materials.length > 0) {
              const material = materials.find(m => m.reference_code === code);
              if (material) {
                setSelectedMaterialId(material.id);
                toast.success(`Material detectado: ${code}`);
              } else {
                toast.info(`Código de material detectado: ${code}. Por favor selecciona el material manualmente.`);
              }
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

      const questionnaire = await response.json();
      
      toast.success(`✅ Cuestionario importado exitosamente! ID: ${questionnaire.id}`);
      
      // Navigate to questionnaire detail
      setTimeout(() => {
        navigate(`/questionnaires/${questionnaire.id}`);
      }, 1500);

    } catch (error: any) {
      toast.error(`❌ Error al importar: ${error.message || 'Error desconocido'}`);
    } finally {
      setUploading(false);
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
