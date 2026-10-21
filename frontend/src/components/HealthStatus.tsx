import { useHealth } from '@/hooks/useHealth';

export function HealthStatus() {
  const { health, loading, error } = useHealth();

  if (loading) {
    return (
      <div className="health-status loading" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true"></span>
        <span>Checking backend connection...</span>
      </div>
    );
  }

  if (error || !health) {
    return (
      <div className="health-status error" role="alert">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <circle cx="12" cy="12" r="10" />
          <line x1="15" y1="9" x2="9" y2="15" />
          <line x1="9" y1="9" x2="15" y2="15" />
        </svg>
        <span>Backend disconnected: {error || 'Unknown error'}</span>
      </div>
    );
  }

  return (
    <div className={`health-status ${health.status === 'healthy' ? 'healthy' : 'degraded'}`}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
        {health.status === 'healthy' ? (
          <>
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </>
        ) : (
          <>
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </>
        )}
      </svg>
      <span>
        Backend connected (v{health.version}) · {health.environment}
      </span>
    </div>
  );
}