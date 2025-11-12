import { useState, useEffect } from 'react';

interface Component {
  id: number;
  cas_number?: string;
  component_name: string;
  percentage: number;
  function_category?: string;
}

interface Composite {
  id: number;
  reference_code: string;
  composite_type?: string;
  composite_origin?: string;
  components: Component[];
  extraction_confidence?: number;
  created_at: string;
}

interface ComparisonResult {
  match_score: number;
  total_components_composite1: number;
  total_components_composite2: number;
  matched_components: number;
  only_in_composite1: Component[];
  only_in_composite2: Component[];
  differences: Array<{
    component_name: string;
    cas_number?: string;
    percentage_composite1: number;
    percentage_composite2: number;
    percentage_difference: number;
  }>;
}

interface Props {
  composite1: Composite;
  composite2: Composite;
  showDetailedComparison?: boolean;
}

export default function CompositeComparison({ composite1, composite2, showDetailedComparison = true }: Props) {
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (showDetailedComparison && composite1 && composite2) {
      calculateComparison();
    }
  }, [composite1, composite2, showDetailedComparison]);

  const calculateComparison = () => {
    setLoading(true);

    try {
      // Simple client-side comparison
      const components1Map = new Map(
        composite1.components.map(c => [c.cas_number || c.component_name, c])
      );
      const components2Map = new Map(
        composite2.components.map(c => [c.cas_number || c.component_name, c])
      );

      const onlyIn1: Component[] = [];
      const onlyIn2: Component[] = [];
      const differences: ComparisonResult['differences'] = [];
      let matchedCount = 0;

      // Check components in composite1
      composite1.components.forEach(comp1 => {
        const key = comp1.cas_number || comp1.component_name;
        const comp2 = components2Map.get(key);

        if (!comp2) {
          onlyIn1.push(comp1);
        } else {
          matchedCount++;
          const percentDiff = Math.abs(comp1.percentage - comp2.percentage);
          if (percentDiff > 0.1) {
            differences.push({
              component_name: comp1.component_name,
              cas_number: comp1.cas_number,
              percentage_composite1: comp1.percentage,
              percentage_composite2: comp2.percentage,
              percentage_difference: percentDiff
            });
          }
        }
      });

      // Check components only in composite2
      composite2.components.forEach(comp2 => {
        const key = comp2.cas_number || comp2.component_name;
        if (!components1Map.has(key)) {
          onlyIn2.push(comp2);
        }
      });

      // Calculate match score
      const totalUnique = components1Map.size + components2Map.size - matchedCount;
      const matchScore = totalUnique > 0 ? (matchedCount / totalUnique) * 100 : 0;

      setComparison({
        match_score: matchScore,
        total_components_composite1: composite1.components.length,
        total_components_composite2: composite2.components.length,
        matched_components: matchedCount,
        only_in_composite1: onlyIn1,
        only_in_composite2: onlyIn2,
        differences
      });
    } catch (error) {
      console.error('Error calculating comparison:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMatchScoreColor = (score: number) => {
    if (score >= 90) return '#10b981'; // green
    if (score >= 70) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div>
      {/* Header Comparison */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        {/* Composite 1 */}
        <div className="card" style={{ backgroundColor: '#1e3a8a', border: '1px solid #1e40af' }}>
          <h3 style={{ marginTop: 0, color: '#bfdbfe', fontSize: '16px' }}>Composite 1</h3>
          <div style={{ fontSize: '13px', color: '#bfdbfe', marginBottom: '8px' }}>
            <div style={{ marginBottom: '4px' }}>
              <strong>Código:</strong> {composite1.reference_code}
            </div>
            {composite1.composite_type && (
              <div style={{ marginBottom: '4px' }}>
                <strong>Tipo:</strong> <span className="badge badge-info" style={{ fontSize: '11px' }}>{composite1.composite_type}</span>
              </div>
            )}
            {composite1.composite_origin && (
              <div style={{ marginBottom: '4px' }}>
                <strong>Origen:</strong> {composite1.composite_origin}
              </div>
            )}
            <div style={{ marginBottom: '4px' }}>
              <strong>Componentes:</strong> {composite1.components.length}
            </div>
            {composite1.extraction_confidence && (
              <div style={{ marginBottom: '4px' }}>
                <strong>Confianza:</strong> {composite1.extraction_confidence.toFixed(1)}%
              </div>
            )}
            <div style={{ marginBottom: '4px' }}>
              <strong>Fecha:</strong> {formatDate(composite1.created_at)}
            </div>
          </div>
        </div>

        {/* Composite 2 */}
        <div className="card" style={{ backgroundColor: '#064e3b', border: '1px solid #065f46' }}>
          <h3 style={{ marginTop: 0, color: '#6ee7b7', fontSize: '16px' }}>Composite 2</h3>
          <div style={{ fontSize: '13px', color: '#6ee7b7', marginBottom: '8px' }}>
            <div style={{ marginBottom: '4px' }}>
              <strong>Código:</strong> {composite2.reference_code}
            </div>
            {composite2.composite_type && (
              <div style={{ marginBottom: '4px' }}>
                <strong>Tipo:</strong> <span className="badge badge-success" style={{ fontSize: '11px' }}>{composite2.composite_type}</span>
              </div>
            )}
            {composite2.composite_origin && (
              <div style={{ marginBottom: '4px' }}>
                <strong>Origen:</strong> {composite2.composite_origin}
              </div>
            )}
            <div style={{ marginBottom: '4px' }}>
              <strong>Componentes:</strong> {composite2.components.length}
            </div>
            {composite2.extraction_confidence && (
              <div style={{ marginBottom: '4px' }}>
                <strong>Confianza:</strong> {composite2.extraction_confidence.toFixed(1)}%
              </div>
            )}
            <div style={{ marginBottom: '4px' }}>
              <strong>Fecha:</strong> {formatDate(composite2.created_at)}
            </div>
          </div>
        </div>
      </div>

      {/* Match Score */}
      {comparison && (
        <div>
          <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1f2937', color: 'white', textAlign: 'center' }}>
            <h3 style={{ marginTop: 0, color: 'white', fontSize: '16px' }}>Score de Coincidencia</h3>
            <div style={{ 
              fontSize: '48px', 
              fontWeight: 'bold',
              color: getMatchScoreColor(comparison.match_score),
              marginBottom: '8px'
            }}>
              {comparison.match_score.toFixed(1)}%
            </div>
            <div style={{ fontSize: '13px', color: '#9ca3af' }}>
              {comparison.matched_components} componentes coinciden de {comparison.total_components_composite1 + comparison.total_components_composite2 - comparison.matched_components} únicos
            </div>
          </div>

          {showDetailedComparison && (
            <div>
              {/* Differences in Percentages */}
              {comparison.differences.length > 0 && (
                <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1f2937', color: 'white' }}>
                  <h3 style={{ marginTop: 0, color: 'white', fontSize: '16px' }}>
                    ⚠️ Diferencias en Porcentajes ({comparison.differences.length})
                  </h3>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Componente</th>
                        <th>CAS</th>
                        <th>% Composite 1</th>
                        <th>% Composite 2</th>
                        <th>Diferencia</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.differences.map((diff, idx) => (
                        <tr key={idx}>
                          <td style={{ fontSize: '13px' }}>{diff.component_name}</td>
                          <td style={{ fontSize: '12px', fontFamily: 'monospace', color: '#9ca3af' }}>
                            {diff.cas_number || '-'}
                          </td>
                          <td style={{ fontWeight: '500', color: '#60a5fa' }}>
                            {diff.percentage_composite1.toFixed(2)}%
                          </td>
                          <td style={{ fontWeight: '500', color: '#34d399' }}>
                            {diff.percentage_composite2.toFixed(2)}%
                          </td>
                          <td>
                            <span style={{
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '12px',
                              fontWeight: '500',
                              backgroundColor: diff.percentage_difference > 5 ? '#7f1d1d' : '#7c2d12',
                              color: diff.percentage_difference > 5 ? '#fca5a5' : '#fdba74'
                            }}>
                              {diff.percentage_difference > 0 ? '+' : ''}{diff.percentage_difference.toFixed(2)}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Only in Composite 1 */}
              {comparison.only_in_composite1.length > 0 && (
                <div className="card" style={{ marginBottom: '24px', backgroundColor: '#1e3a8a', border: '1px solid #1e40af' }}>
                  <h3 style={{ marginTop: 0, color: '#bfdbfe', fontSize: '16px' }}>
                    📘 Solo en Composite 1 ({comparison.only_in_composite1.length})
                  </h3>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Componente</th>
                        <th>CAS</th>
                        <th>Porcentaje</th>
                        <th>Función</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.only_in_composite1.map((comp) => (
                        <tr key={comp.id}>
                          <td style={{ fontSize: '13px' }}>{comp.component_name}</td>
                          <td style={{ fontSize: '12px', fontFamily: 'monospace', color: '#9ca3af' }}>
                            {comp.cas_number || '-'}
                          </td>
                          <td style={{ fontWeight: '500', color: '#60a5fa' }}>
                            {comp.percentage.toFixed(2)}%
                          </td>
                          <td style={{ fontSize: '12px', color: '#9ca3af' }}>
                            {comp.function_category || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Only in Composite 2 */}
              {comparison.only_in_composite2.length > 0 && (
                <div className="card" style={{ marginBottom: '24px', backgroundColor: '#064e3b', border: '1px solid #065f46' }}>
                  <h3 style={{ marginTop: 0, color: '#6ee7b7', fontSize: '16px' }}>
                    📗 Solo en Composite 2 ({comparison.only_in_composite2.length})
                  </h3>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Componente</th>
                        <th>CAS</th>
                        <th>Porcentaje</th>
                        <th>Función</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.only_in_composite2.map((comp) => (
                        <tr key={comp.id}>
                          <td style={{ fontSize: '13px' }}>{comp.component_name}</td>
                          <td style={{ fontSize: '12px', fontFamily: 'monospace', color: '#9ca3af' }}>
                            {comp.cas_number || '-'}
                          </td>
                          <td style={{ fontWeight: '500', color: '#34d399' }}>
                            {comp.percentage.toFixed(2)}%
                          </td>
                          <td style={{ fontSize: '12px', color: '#9ca3af' }}>
                            {comp.function_category || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* All Good */}
              {comparison.differences.length === 0 && 
               comparison.only_in_composite1.length === 0 && 
               comparison.only_in_composite2.length === 0 && (
                <div className="card" style={{ backgroundColor: '#064e3b', border: '1px solid #065f46' }}>
                  <div style={{ textAlign: 'center', padding: '20px', color: '#6ee7b7' }}>
                    <div style={{ fontSize: '48px', marginBottom: '12px' }}>✅</div>
                    <h3 style={{ marginTop: 0, color: '#6ee7b7' }}>Composites Idénticos</h3>
                    <p style={{ fontSize: '14px', color: '#6ee7b7', marginTop: '8px' }}>
                      Los composites tienen exactamente los mismos componentes con los mismos porcentajes.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#9ca3af' }}>
          Calculando comparación...
        </div>
      )}
    </div>
  );
}












