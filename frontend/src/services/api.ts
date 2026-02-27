import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ChatRequest {
  question: string;
}

export interface Source {
  filename: string;
  pdf_path: string | null;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

export interface FileProcessingResult {
  filename: string;
  success: boolean;
  documents_processed: number;
  error_message?: string;
  file_type: string;
}

export interface UploadResponse {
  message: string;
  filename?: string;
  documents_processed: number;
}

export interface FolderUploadResponse {
  message: string;
  total_files_processed: number;
  successful_files: number;
  failed_files: number;
  total_documents_processed: number;
  file_results: FileProcessingResult[];
  processing_summary: Record<string, number>;
}



export const apiService = {
  // Chat endpoint
  async chat(question: string): Promise<ChatResponse> {
    const response = await api.post<ChatResponse>('/chat', { question });
    return response.data;
  },

  // Single file upload
  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },



  // ZIP file upload
  async uploadZipFolder(file: File): Promise<FolderUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<FolderUploadResponse>('/upload_zip_folder', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },



  // Health check
  async healthCheck(): Promise<{ status: string }> {
    const response = await api.get('/health');
    return response.data;
  },

  // Box Integration
  async getBoxFolders(): Promise<BoxFolder[]> {
    const response = await api.get<BoxFolder[]>('/box/folders');
    return response.data;
  },

  // Dispatch Box ingestion as a background job, returns job_id immediately
  async ingestBoxFolders(folderIds: string[]): Promise<JobResponse> {
    const response = await api.post<JobResponse>('/box/ingest', { folder_ids: folderIds });
    return response.data;
  },

  // Poll job status by job_id
  async getJobStatus(jobId: string): Promise<JobStatusResponse> {
    const response = await api.get<JobStatusResponse>(`/box/job/${jobId}`);
    return response.data;
  },
};

export interface BoxFolder {
  id: string;
  name: string;
}

export interface JobResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: 'queued' | 'running' | 'complete' | 'failed';
  current: number;
  total: number;
  processed_count?: number;
  details: string[];
}
