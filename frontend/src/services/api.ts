import axios from 'axios';

// Interfaces mapping to our backend SQLAlchemy models / Pydantic schemas
export interface ResumeResult {
  file_name: string;
  status: 'SUCCESS' | 'FAILED';
  error_message: string | null;
  skills: string[];
  people: string[];
  info: string[]; // Our backend currently returns a list and falls back to dict, but let's treat it as string[] for display
}

export interface BatchJobResponse {
  job_id: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  total_files: number;
  processed_files: number;
  results: ResumeResult[];
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const apiService = {
  /**
   * Uploads a batch of PDFs to the server.
   * @param files Array of File objects to upload
   * @param sessionId A unique session identifier for the pragmatic auth
   * @returns The job_id string
   */
  async uploadBatch(files: File[], sessionId: string): Promise<string> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    const response = await api.post<{ job_id: string }>('/upload-batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'X-Session-ID': sessionId,
      },
    });

    return response.data.job_id;
  },

  /**
   * Fetches the final results of a completed batch job.
   * @param jobId The UUID of the job
   * @returns The full BatchJob payload including results
   */
  async getJobResults(jobId: string): Promise<BatchJobResponse> {
    const response = await api.get<BatchJobResponse>(`/jobs/${jobId}`);
    return response.data;
  },
};
