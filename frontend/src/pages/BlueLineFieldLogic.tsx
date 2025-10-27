import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import '../components/Layout.css';

interface FieldLogic {
  id: number;
  field_name: string;
  field_label?: string;
  field_category?: string;
  field_type: string;
  material_type_filter: string;
  logic_expression: Record<string, any>;
  priority: number;
  is_active: boolean;
  description?: string;
}

export default function BlueLineFieldLogic() {
  const [fieldLogics, setFieldLogics] = useState<FieldLogic[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    is_active: '',
    field_category: '',
    material_type_filter: '',
  });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingLogic, setEditingLogic] = useState<FieldLogic | null>(null);

  useEffect(() => {
    fetchFieldLogics();
  }, []);

  const fetchFieldLogics = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/blue-line/field-logic');
      const data = await response.json();
      setFieldLogics(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching field logics:', error);
      setLoading(false);
    }
  };

  const filteredLogics = fieldLogics.filter((logic) => {
    if (filter.is_active && logic.is_active !== (filter.is_active === 'true')) return false;
    if (filter.field_category && logic.field_category !== filter.field_category) return false;
    if (filter.material_type_filter && logic.material_type_filter !== filter.material_type_filter) return false;
    return true;
  });

  const categories = [...new Set(fieldLogics.map((fl) => fl.field_category).filter(Boolean))];

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this field logic?')) return;

    try {
      await fetch(`http://localhost:8000/api/blue-line/field-logic/${id}`, {
        method: 'DELETE',
      });
      fetchFieldLogics();
    } catch (error) {
      console.error('Error deleting field logic:', error);
      alert('Error deleting field logic');
    }
  };

  const handleToggleActive = async (logic: FieldLogic) => {
    try {
      await fetch(`http://localhost:8000/api/blue-line/field-logic/${logic.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !logic.is_active }),
      });
      fetchFieldLogics();
    } catch (error) {
      console.error('Error updating field logic:', error);
      alert('Error updating field logic');
    }
  };

  if (loading) {
    return (
      <div>
        <h1>Field Logic Configuration</h1>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <Link to="/blue-line" style={{ color: '#3b82f6', textDecoration: 'none' }}>
          ← Back to Blue Lines
        </Link>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <h1 style={{ margin: 0 }}>Field Logic Configuration</h1>
        <button onClick={() => setShowCreateModal(true)} className="button">
          Create New Field Logic
        </button>
      </div>

      {/* Info Box */}
      <div
        style={{
          padding: '16px',
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '8px',
          marginBottom: '24px',
        }}
      >
        <h3 style={{ margin: '0 0 8px 0', color: '#1e40af' }}>About Field Logic</h3>
        <p style={{ margin: 0, color: '#1e40af', fontSize: '14px' }}>
          Configure the logic for each of the 446 Blue Line fields. Each field can have different logic depending on
          the material type (Z001 or Z002). The logic is defined as JSON expressions that determine how field values
          are calculated from material data, composites, and homologation records.
        </p>
      </div>

      {/* Filters */}
      <div style={{ marginBottom: '24px', display: 'flex', gap: '16px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
            Active Status
          </label>
          <select
            value={filter.is_active}
            onChange={(e) => setFilter({ ...filter, is_active: e.target.value })}
            style={{ padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}
          >
            <option value="">All</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
            Category
          </label>
          <select
            value={filter.field_category}
            onChange={(e) => setFilter({ ...filter, field_category: e.target.value })}
            style={{ padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}
          >
            <option value="">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '4px', fontSize: '14px', fontWeight: '500' }}>
            Material Type
          </label>
          <select
            value={filter.material_type_filter}
            onChange={(e) => setFilter({ ...filter, material_type_filter: e.target.value })}
            style={{ padding: '8px', borderRadius: '6px', border: '1px solid #e5e7eb' }}
          >
            <option value="">All Types</option>
            <option value="ALL">ALL</option>
            <option value="Z001">Z001</option>
            <option value="Z002">Z002</option>
          </select>
        </div>
      </div>

      {/* Field Logics Table */}
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Priority</th>
              <th>Field Name</th>
              <th>Label</th>
              <th>Category</th>
              <th>Type</th>
              <th>Material Filter</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogics.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '32px', color: '#6b7280' }}>
                  No field logics found. Create your first field logic to get started.
                </td>
              </tr>
            ) : (
              filteredLogics
                .sort((a, b) => a.priority - b.priority)
                .map((logic) => (
                  <tr key={logic.id}>
                    <td style={{ fontFamily: 'monospace' }}>{logic.priority}</td>
                    <td style={{ fontFamily: 'monospace', fontWeight: '500' }}>{logic.field_name}</td>
                    <td>{logic.field_label || '-'}</td>
                    <td>{logic.field_category || '-'}</td>
                    <td>
                      <span
                        style={{
                          padding: '2px 8px',
                          borderRadius: '8px',
                          fontSize: '11px',
                          backgroundColor: '#f3f4f6',
                          fontFamily: 'monospace',
                        }}
                      >
                        {logic.field_type}
                      </span>
                    </td>
                    <td style={{ fontFamily: 'monospace' }}>{logic.material_type_filter}</td>
                    <td>
                      <span
                        style={{
                          padding: '4px 12px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: '500',
                          backgroundColor: logic.is_active ? '#10b98120' : '#6b728020',
                          color: logic.is_active ? '#10b981' : '#6b7280',
                        }}
                      >
                        {logic.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          onClick={() => setEditingLogic(logic)}
                          style={{
                            padding: '4px 12px',
                            fontSize: '12px',
                            backgroundColor: '#3b82f6',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                          }}
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleToggleActive(logic)}
                          style={{
                            padding: '4px 12px',
                            fontSize: '12px',
                            backgroundColor: logic.is_active ? '#f59e0b' : '#10b981',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                          }}
                        >
                          {logic.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button
                          onClick={() => handleDelete(logic.id)}
                          style={{
                            padding: '4px 12px',
                            fontSize: '12px',
                            backgroundColor: '#ef4444',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: 'pointer',
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
            )}
          </tbody>
        </table>
      </div>

      {/* Summary */}
      <div style={{ marginTop: '32px', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#3b82f6' }}>{fieldLogics.length}</div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>Total Fields</div>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#10b981' }}>
            {fieldLogics.filter((fl) => fl.is_active).length}
          </div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>Active</div>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#6b7280' }}>
            {446 - fieldLogics.length}
          </div>
          <div style={{ fontSize: '14px', color: '#6b7280', marginTop: '8px' }}>Remaining to Configure</div>
        </div>
      </div>

      {/* Create/Edit Modal would go here - simplified for this implementation */}
      {(showCreateModal || editingLogic) && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          onClick={() => {
            setShowCreateModal(false);
            setEditingLogic(null);
          }}
        >
          <div
            className="card"
            style={{ maxWidth: '600px', width: '90%' }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2>{editingLogic ? 'Edit Field Logic' : 'Create Field Logic'}</h2>
            <p style={{ color: '#6b7280' }}>
              Field logic configuration form would go here. For now, use the API directly or import field logics via
              bulk import.
            </p>
            <button
              onClick={() => {
                setShowCreateModal(false);
                setEditingLogic(null);
              }}
              className="button"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

