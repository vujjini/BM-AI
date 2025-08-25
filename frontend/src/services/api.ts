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

export interface ChatResponse {
  answer: string;
  sources: string[];
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

export interface PDFManualUploadResponse {
  message: string;
  filename: string;
  file_size: number;
  page_count: number;
  text_length: number;
  documents_processed: number;
  extraction_method: string;
  processing_time: number;
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

  // Multiple files upload
  async uploadFolder(files: File[]): Promise<FolderUploadResponse> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await api.post<FolderUploadResponse>('/upload_folder', formData, {
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

  // PDF manual upload
  async uploadPDFManual(file: File): Promise<PDFManualUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post<PDFManualUploadResponse>('/upload_manual', formData, {
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
};
