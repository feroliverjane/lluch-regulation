import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import '../components/Layout.css';

interface BlueLine {
  id: number;
  material_id: number;
  supplier_code: string;
  material_type: 'Z001' | 'Z002';
  sync_status: 'PENDING' | 'SYNCED' | 'FAILED' | 'NOT_REQUIRED';
  calculated_at: string;
  last_synced_at?: string;
  sync_error_message?: string;
  blue_line_data: Record<string, any>;
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

export default function BlueLineDetail() {
  const { id } = useParams<{ id: string }>();
  const [blueLine, setBlueLine] = useState<BlueLine | null>(null);
  const [material, setMaterial] = useState<Material | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [importing, setImporting] = useState(false);

  useEffect(() => {
    fetchBlueLineDetail();
  }, [id]);

  const fetchBlueLineDetail = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/blue-line/${id}`);
      const data = await response.json();
      setBlueLine(data);

      // Fetch material
      const matResponse = await fetch(`http://localhost:8000/api/materials/${data.material_id}`);
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
      const response = await fetch(`http://localhost:8000/api/blue-line/${blueLine.id}/sync-to-sap`, {
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
        `http://localhost:8000/api/blue-line/material/${blueLine.material_id}/import-from-sap`,
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

  if (loading) {
    return (
      <div>
        <h1>Blue Line Detail</h1>
        <p>Loading...</p>
      </div>
    );
  }

  if (!blueLine) {
    return (
      <div>
        <h1>Blue Line Detail</h1>
        <p>Blue Line not found</p>
      </div>
    );
  }

  // Group fields by category
  const groupedFields: Record<string, Array<[string, any]>> = {};
  Object.entries(blueLine.blue_line_data).forEach(([key, value]) => {
    // Simple categorization - in production you'd have proper categories
    const category = key.startsWith('sap_') ? 'SAP Fields' : 'Calculated Fields';
    if (!groupedFields[category]) {
      groupedFields[category] = [];
    }
    groupedFields[category].push([key, value]);
  });

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <Link to="/blue-line" style={{ color: '#3b82f6', textDecoration: 'none' }}>
          ← Back to Blue Lines
        </Link>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <h1 style={{ margin: 0 }}>Blue Line #{blueLine.id}</h1>
        <div style={{ display: 'flex', gap: '12px' }}>
          {material?.sap_status === 'Z1' && (
            <button onClick={handleSyncToSAP} disabled={syncing} className="button">
              {syncing ? 'Syncing...' : 'Sync to SAP'}
            </button>
          )}
          {material?.sap_status === 'Z2' && (
            <button onClick={handleImportFromSAP} disabled={importing} className="button">
              {importing ? 'Importing...' : 'Import from SAP'}
            </button>
          )}
        </div>
      </div>

      {/* Material Info Card */}
      {material && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <h2 style={{ marginTop: 0 }}>Material Information</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Reference Code</div>
              <div style={{ fontWeight: '500' }}>{material.reference_code}</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Material Name</div>
              <div style={{ fontWeight: '500' }}>{material.name}</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Supplier</div>
              <div style={{ fontWeight: '500' }}>{material.supplier || '-'}</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>SAP Status</div>
              <div style={{ fontWeight: '500' }}>{material.sap_status || '-'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Blue Line Info Card */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h2 style={{ marginTop: 0 }}>Blue Line Information</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Supplier Code</div>
            <div style={{ fontWeight: '500' }}>{blueLine.supplier_code}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Material Type</div>
            <div>
              <span
                style={{
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '500',
                  backgroundColor: blueLine.material_type === 'Z001' ? '#8b5cf620' : '#3b82f620',
                  color: blueLine.material_type === 'Z001' ? '#8b5cf6' : '#3b82f6',
                }}
              >
                {blueLine.material_type}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Sync Status</div>
            <div>
              <span
                style={{
                  padding: '4px 12px',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontWeight: '500',
                  backgroundColor:
                    blueLine.sync_status === 'SYNCED'
                      ? '#10b98120'
                      : blueLine.sync_status === 'FAILED'
                      ? '#ef444420'
                      : '#f59e0b20',
                  color:
                    blueLine.sync_status === 'SYNCED'
                      ? '#10b981'
                      : blueLine.sync_status === 'FAILED'
                      ? '#ef4444'
                      : '#f59e0b',
                }}
              >
                {blueLine.sync_status}
              </span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Calculated At</div>
            <div style={{ fontWeight: '500' }}>{new Date(blueLine.calculated_at).toLocaleString()}</div>
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>Last Synced</div>
            <div style={{ fontWeight: '500' }}>
              {blueLine.last_synced_at ? new Date(blueLine.last_synced_at).toLocaleString() : 'Never'}
            </div>
          </div>
          {blueLine.sync_error_message && (
            <div style={{ gridColumn: 'span 3' }}>
              <div style={{ fontSize: '12px', color: '#ef4444', marginBottom: '4px' }}>Sync Error</div>
              <div style={{ color: '#ef4444', fontSize: '14px' }}>{blueLine.sync_error_message}</div>
            </div>
          )}
        </div>
      </div>

      {/* 446 Fields Display */}
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Blue Line Fields (446 Fields)</h2>

        {Object.keys(groupedFields).length === 0 ? (
          <p style={{ color: '#6b7280' }}>No fields calculated yet</p>
        ) : (
          Object.entries(groupedFields).map(([category, fields]) => (
            <div key={category} style={{ marginBottom: '32px' }}>
              <h3 style={{ fontSize: '18px', marginBottom: '16px', color: '#374151' }}>{category}</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                {fields.map(([key, value]) => (
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
          ))
        )}
      </div>

      {/* Metadata */}
      {blueLine.calculation_metadata && Object.keys(blueLine.calculation_metadata).length > 0 && (
        <div className="card" style={{ marginTop: '24px' }}>
          <h2 style={{ marginTop: 0 }}>Calculation Metadata</h2>
          <pre
            style={{
              backgroundColor: '#f9fafb',
              padding: '16px',
              borderRadius: '6px',
              overflow: 'auto',
              fontSize: '12px',
              color: '#111827',
            }}
          >
            {JSON.stringify(blueLine.calculation_metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

