import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../components/Layout.css';

interface BlueLine {
  id: number;
  material_id: number;
  supplier_code: string;
  material_type: 'Z001' | 'Z002';
  sync_status: 'PENDING' | 'SYNCED' | 'FAILED' | 'NOT_REQUIRED';
  calculated_at: string;
  last_synced_at?: string;
  blue_line_data: Record<string, any>;
}

interface Material {
  id: number;
  reference_code: string;
  name: string;
  sap_status?: string;
}

export default function BlueLine() {
  const [blueLines, setBlueLines] = useState<BlueLine[]>([]);
  const [materials, setMaterials] = useState<Map<number, Material>>(new Map());
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    materialType: '',
    syncStatus: '',
  });

  useEffect(() => {
    fetchBlueLines();
  }, []);

  const fetchBlueLines = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/blue-line');
      const data = await response.json();
      setBlueLines(data);

      // Fetch materials for each blue line
      const materialIds = [...new Set(data.map((bl: BlueLine) => bl.material_id))];
      const materialsMap = new Map<number, Material>();

      for (const materialId of materialIds) {
        const matResponse = await fetch(`http://localhost:8000/api/materials/${materialId}`);
        const material = await matResponse.json();
        materialsMap.set(materialId, material);
      }

      setMaterials(materialsMap);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching blue lines:', error);
      setLoading(false);
    }
  };

  const filteredBlueLines = blueLines.filter((bl) => {
    if (filter.materialType && bl.material_type !== filter.materialType) return false;
    if (filter.syncStatus && bl.sync_status !== filter.syncStatus) return false;
    return true;
  });

  const getSyncStatusBadge = (status: string) => {
    const badges: Record<string, { class: string; label: string }> = {
      SYNCED: { class: 'badge-success', label: 'Sincronizado' },
      PENDING: { class: 'badge-warning', label: 'Pendiente' },
      FAILED: { class: 'badge-danger', label: 'Fallido' },
      NOT_REQUIRED: { class: 'badge-secondary', label: 'No Requerido' },
    };

    const badge = badges[status] || { class: 'badge-secondary', label: status };

    return <span className={`badge ${badge.class}`}>{badge.label}</span>;
  };

  const getMaterialTypeBadge = (type: string) => {
    const badges: Record<string, { class: string; label: string }> = {
      Z001: { class: 'badge-warning', label: 'Z001 (Provisional)' },
      Z002: { class: 'badge-info', label: 'Z002 (Homologado)' },
    };

    const badge = badges[type] || { class: 'badge-secondary', label: type };

    return <span className={`badge ${badge.class}`}>{badge.label}</span>;
  };

  if (loading) {
    return (
      <div>
        <h1>Blue Line Management</h1>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Línea Azul</h1>
          <p>Homologación LLUCH 103721 - Material-Proveedor</p>
        </div>
        <Link 
          to="/blue-line/field-logic" 
          className="btn btn-primary"
          style={{ textDecoration: 'none' }}
        >
          ⚙️ Configurar Lógica de Campos
        </Link>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <div style={{ flex: 1 }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '0.5rem', 
              fontSize: '0.875rem', 
              fontWeight: '500'
            }}>
              Tipo de Material
            </label>
            <select
              value={filter.materialType}
              onChange={(e) => setFilter({ ...filter, materialType: e.target.value })}
              style={{ 
                width: '100%',
                padding: '0.5rem', 
                borderRadius: '0.375rem', 
                border: '1px solid #d1d5db',
                fontSize: '0.875rem'
              }}
            >
              <option value="">Todos los Tipos</option>
              <option value="Z001">Z001 (Provisional - Estimado)</option>
              <option value="Z002">Z002 (Homologado - Analizado)</option>
            </select>
          </div>

          <div style={{ flex: 1 }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '0.5rem', 
              fontSize: '0.875rem', 
              fontWeight: '500'
            }}>
              Estado de Sincronización
            </label>
            <select
              value={filter.syncStatus}
              onChange={(e) => setFilter({ ...filter, syncStatus: e.target.value })}
              style={{ 
                width: '100%',
                padding: '0.5rem', 
                borderRadius: '0.375rem', 
                border: '1px solid #d1d5db',
                fontSize: '0.875rem'
              }}
            >
              <option value="">Todos los Estados</option>
              <option value="SYNCED">✅ Sincronizado</option>
              <option value="PENDING">⏳ Pendiente</option>
              <option value="FAILED">❌ Fallido</option>
              <option value="NOT_REQUIRED">➖ No Requerido</option>
            </select>
          </div>
        </div>
      </div>

      {/* Blue Lines Table */}
      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Material</th>
              <th>Código Proveedor</th>
              <th>Tipo</th>
              <th>Estado Sync</th>
              <th>Estado SAP</th>
              <th>Calculado</th>
              <th>Último Sync</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {filteredBlueLines.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '2rem' }}>
                  No se encontraron registros de Línea Azul
                </td>
              </tr>
            ) : (
              filteredBlueLines.map((blueLine) => {
                const material = materials.get(blueLine.material_id);
                return (
                  <tr key={blueLine.id}>
                    <td>#{blueLine.id}</td>
                    <td>
                      {material ? (
                        <div>
                          <div style={{ fontWeight: '500' }}>
                            <Link to={`/materials/${material.id}`} className="link">
                              {material.reference_code}
                            </Link>
                          </div>
                          <div style={{ fontSize: '0.875rem', color: '#6b7280', marginTop: '0.25rem' }}>
                            {material.name}
                          </div>
                        </div>
                      ) : (
                        `Material ${blueLine.material_id}`
                      )}
                    </td>
                    <td>
                      <code style={{ fontSize: '0.875rem' }}>{blueLine.supplier_code}</code>
                    </td>
                    <td>{getMaterialTypeBadge(blueLine.material_type)}</td>
                    <td>{getSyncStatusBadge(blueLine.sync_status)}</td>
                    <td>
                      {material?.sap_status ? (
                        <span className="badge badge-secondary">
                          {material.sap_status}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>
                      {new Date(blueLine.calculated_at).toLocaleDateString('es-ES', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                      })}
                    </td>
                    <td>
                      {blueLine.last_synced_at
                        ? new Date(blueLine.last_synced_at).toLocaleDateString('es-ES', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric'
                          })
                        : <span style={{ color: '#9ca3af' }}>Nunca</span>}
                    </td>
                    <td>
                      <Link to={`/blue-line/${blueLine.id}`} className="link">
                        Ver Detalles
                      </Link>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Summary Stats */}
      <div style={{ marginTop: '32px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
        <div className="card" style={{ 
          textAlign: 'center', 
          padding: '24px',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          border: 'none'
        }}>
          <div style={{ fontSize: '40px', fontWeight: 'bold', marginBottom: '8px' }}>{blueLines.length}</div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Total Líneas Azul</div>
        </div>

        <div className="card" style={{ 
          textAlign: 'center', 
          padding: '24px',
          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          color: 'white',
          border: 'none'
        }}>
          <div style={{ fontSize: '40px', fontWeight: 'bold', marginBottom: '8px' }}>
            {blueLines.filter((bl) => bl.sync_status === 'SYNCED').length}
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Sincronizadas</div>
        </div>

        <div className="card" style={{ 
          textAlign: 'center', 
          padding: '24px',
          background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
          color: 'white',
          border: 'none'
        }}>
          <div style={{ fontSize: '40px', fontWeight: 'bold', marginBottom: '8px' }}>
            {blueLines.filter((bl) => bl.sync_status === 'PENDING').length}
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Pendientes</div>
        </div>

        <div className="card" style={{ 
          textAlign: 'center', 
          padding: '24px',
          background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
          color: 'white',
          border: 'none'
        }}>
          <div style={{ fontSize: '40px', fontWeight: 'bold', marginBottom: '8px' }}>
            {blueLines.filter((bl) => bl.sync_status === 'FAILED').length}
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>Fallidas</div>
        </div>
      </div>
    </div>
  );
}

