export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database?: string;
}

export interface ApiError {
  detail: string;
}