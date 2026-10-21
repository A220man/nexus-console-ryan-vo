import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/api/client';
import type { HealthResponse } from '@/types/api';

export function useHealth(pollInterval = 30000) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const data = await apiClient.getHealth();
      setHealth(data);
      setError(null);
    } catch (err: unknown) {
      const error = err as { detail?: string };
      setError(error.detail || 'Failed to fetch health');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    
    const interval = setInterval(fetchHealth, pollInterval);
    return () => clearInterval(interval);
  }, [fetchHealth, pollInterval]);

  return { health, loading, error, refetch: fetchHealth };
}