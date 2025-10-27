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
    const colors: Record<string, string> = {
      SYNCED: '#10b981',
      PENDING: '#f59e0b',
      FAILED: '#ef4444',
      NOT_REQUIRED: '#6b7280',
    };

    return (
      <span
        style={{
          padding: '4px 12px',
          borderRadius: '12px',
          fontSize: '12px',
          fontWeight: '500',
          backgroundColor: `${colors[status]}20`,
          color: colors[status],
        }}
      >
        {status}
      </span>
    );
  };

  const getMaterialTypeBadge = (type: string) => {
    const colors: Record<string, string> = {
      Z001: '#8b5cf6',
      Z002: '#3b82f6',
    };

    return (
      <span
        style={{
          padding: '4px 12px',
          borderRadius: '12px',
          fontSize: '12px',
          fontWeight: '500',
          backgroundColor: `${colors[type]}20`,
          color: colors[type],
        }}
      >
        {type}
      </span>
    );
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <h1 style={{ margin: 0 }}>Blue Line Management</h1>
        <Link to="/blue-line/field-logic" className="button">
          Configure Field Logic
        </Link>
      </div>

      {/* Filters */}
      <div style={{ marginBottom: '24px', display: 'flex', gap: '16px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
            Material Type
          </label>
          <select
            value={filter.materialType}
            onChange={(e) => setFilter({ ...filter, materialType: e.target.value })}
            style={{ padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}
          >
            <option value="">All Types</option>
            <option value="Z001">Z001 (Provisional)</option>
            <option value="Z002">Z002 (Homologated)</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
            Sync Status
          </label>
          <select
            value={filter.syncStatus}
            onChange={(e) => setFilter({ ...filter, syncStatus: e.target.value })}
            style={{ padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}
          >
            <option value="">All Statuses</option>
            <option value="SYNCED">Synced</option>
            <option value="PENDING">Pending</option>
            <option value="FAILED">Failed</option>
            <option value="NOT_REQUIRED">Not Required</option>
          </select>
        </div>
      </div>

      {/* Blue Lines Table */}
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Material</th>
              <th>Supplier Code</th>
              <th>Type</th>
              <th>Sync Status</th>
              <th>SAP Status</th>
              <th>Calculated At</th>
              <th>Last Synced</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredBlueLines.length === 0 ? (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', padding: '32px', color: '#6b7280' }}>
                  No Blue Lines found
                </td>
              </tr>
            ) : (
              filteredBlueLines.map((blueLine) => {
                const material = materials.get(blueLine.material_id);
                return (
                  <tr key={blueLine.id}>
                    <td>{blueLine.id}</td>
                    <td>
                      {material ? (
                        <div>
                          <div style={{ fontWeight: '500' }}>{material.reference_code}</div>
                          <div style={{ fontSize: '12px', color: '#6b7280' }}>{material.name}</div>
                        </div>
                      ) : (
                        `Material ${blueLine.material_id}`
                      )}
                    </td>
                    <td>{blueLine.supplier_code}</td>
                    <td>{getMaterialTypeBadge(blueLine.material_type)}</td>
                    <td>{getSyncStatusBadge(blueLine.sync_status)}</td>
                    <td>
                      {material?.sap_status ? (
                        <span style={{ fontFamily: 'monospace' }}>{material.sap_status}</span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>{new Date(blueLine.calculated_at).toLocaleDateString()}</td>
                    <td>
                      {blueLine.last_synced_at
                        ? new Date(blueLine.last_synced_at).toLocaleDateString()
                        : '-'}
                    </td>
                    <td>
                      <Link
                        to={`/blue-line/${blueLine.id}`}
                        style={{ color: '#3b82f6', textDecoration: 'none', fontWeight: '500' }}
                      >
                        View Details
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
      <div style={{ marginTop: '32px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#3b82f6' }}>{blueLines.length}</div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>Total Blue Lines</div>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#10b981' }}>
            {blueLines.filter((bl) => bl.sync_status === 'SYNCED').length}
          </div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>Synced</div>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#f59e0b' }}>
            {blueLines.filter((bl) => bl.sync_status === 'PENDING').length}
          </div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>Pending Sync</div>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#ef4444' }}>
            {blueLines.filter((bl) => bl.sync_status === 'FAILED').length}
          </div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>Failed</div>
        </div>
      </div>
    </div>
  );
}

