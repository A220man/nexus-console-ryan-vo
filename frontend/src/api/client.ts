import axios, { AxiosInstance, AxiosError } from 'axios';
import type { HealthResponse } from '@/types/api';

declare global {
  interface ImportMetaEnv {
    readonly VITE_API_BASE_URL: string;
  }
  interface ImportMeta {
    readonly env: ImportMetaEnv;
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response) {
          return Promise.reject({
            status: error.response.status,
            detail: (error.response.data as { detail?: string })?.detail || error.message,
          });
        }
        return Promise.reject({
          status: 0,
          detail: 'Network error - cannot reach backend',
        });
      }
    );
  }

  async getHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }
}

export const apiClient = new ApiClient();