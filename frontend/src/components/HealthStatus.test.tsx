import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { HealthStatus } from '@/components/HealthStatus';
import { apiClient } from '@/api/client';

vi.mock('@/api/client', () => ({
  apiClient: {
    getHealth: vi.fn(),
  },
}));

describe('HealthStatus', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading state initially', () => {
    render(<HealthStatus />);
    expect(screen.getByText('Checking backend connection...')).toBeInTheDocument();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows connected state when backend is healthy', async () => {
    (apiClient.getHealth as ReturnType<typeof vi.fn>).mockResolvedValue({
      status: 'healthy',
      version: '1.0.0',
      environment: 'development',
    });

    render(<HealthStatus />);

    await waitFor(() => {
      expect(screen.getByText('Backend connected (v1.0.0) · development')).toBeInTheDocument();
    });
  });

  it('shows error state when backend fails', async () => {
    (apiClient.getHealth as ReturnType<typeof vi.fn>).mockRejectedValue({
      detail: 'Network error',
    });

    render(<HealthStatus />);

    await waitFor(() => {
      expect(screen.getByText('Backend disconnected: Network error')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});