import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, Folder, Archive, BookOpen, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { apiService, UploadResponse, FolderUploadResponse, PDFManualUploadResponse } from '../services/api';
import './FileUpload.css';

interface FileUploadProps {
  onUploadSuccess: (message: string) => void;
  onUploadError: (error: string) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess, onUploadError }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadMode, setUploadMode] = useState<'single' | 'multiple' | 'zip' | 'manual'>('single');
  const [uploadResults, setUploadResults] = useState<any>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setUploadResults(null);

    try {
      let result: UploadResponse | FolderUploadResponse | PDFManualUploadResponse;

      if (uploadMode === 'manual' && acceptedFiles.length === 1) {
        const file = acceptedFiles[0];
        if (!file.name.toLowerCase().endsWith('.pdf')) {
          throw new Error('Only PDF files are supported for manual upload');
        }
        result = await apiService.uploadPDFManual(file);
      } else if (uploadMode === 'single' && acceptedFiles.length === 1) {
        const file = acceptedFiles[0];
        if (file.name.endsWith('.zip')) {
          result = await apiService.uploadZipFolder(file);
        } else {
          result = await apiService.uploadFile(file);
        }
      } else if (uploadMode === 'zip' && acceptedFiles.length === 1 && acceptedFiles[0].name.endsWith('.zip')) {
        result = await apiService.uploadZipFolder(acceptedFiles[0]);
      } else {
        result = await apiService.uploadFolder(acceptedFiles);
      }

      setUploadResults(result);
      onUploadSuccess(`Successfully processed files: ${result.message}`);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Upload failed';
      onUploadError(errorMessage);
    } finally {
      setUploading(false);
    }
  }, [uploadMode, onUploadSuccess, onUploadError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: uploadMode === 'manual' ? {
      'application/pdf': ['.pdf']
    } : {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/zip': ['.zip']
    },
    multiple: uploadMode !== 'single' && uploadMode !== 'manual',
    disabled: uploading
  });

  const renderUploadResults = () => {
    if (!uploadResults) return null;

    const isFolderUpload = 'total_files_processed' in uploadResults;
    const isPDFManual = 'extraction_method' in uploadResults;

    return (
      <div className="upload-results">
        <div className="results-header">
          <CheckCircle className="success-icon" size={20} />
          <h3>Upload Complete</h3>
        </div>
        
        {isPDFManual ? (
          <div className="pdf-manual-results">
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">File:</span>
                <span className="stat-value">{uploadResults.filename}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Pages:</span>
                <span className="stat-value">{uploadResults.page_count}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Text Length:</span>
                <span className="stat-value">{uploadResults.text_length.toLocaleString()} chars</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Documents:</span>
                <span className="stat-value success">{uploadResults.documents_processed}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Processing Time:</span>
                <span className="stat-value">{uploadResults.processing_time.toFixed(2)}s</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Extraction Method:</span>
                <span className="stat-value">{uploadResults.extraction_method}</span>
              </div>
            </div>
          </div>
        ) : isFolderUpload ? (
          <div className="folder-results">
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Total Files:</span>
                <span className="stat-value">{uploadResults.total_files_processed}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Successful:</span>
                <span className="stat-value success">{uploadResults.successful_files}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Failed:</span>
                <span className="stat-value error">{uploadResults.failed_files}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Documents Processed:</span>
                <span className="stat-value">{uploadResults.total_documents_processed}</span>
              </div>
            </div>

            {uploadResults.file_results && uploadResults.file_results.length > 0 && (
              <div className="file-results">
                <h4>File Processing Details:</h4>
                {uploadResults.file_results.map((result: any, index: number) => (
                  <div key={index} className={`file-result ${result.success ? 'success' : 'error'}`}>
                    <div className="file-info">
                      {result.success ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                      <span className="filename">{result.filename}</span>
                      <span className="file-type">({result.file_type})</span>
                    </div>
                    <div className="file-stats">
                      {result.success ? (
                        <span>{result.documents_processed} documents</span>
                      ) : (
                        <span className="error-message">{result.error_message}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="single-file-results">
            <p><strong>File:</strong> {uploadResults.filename}</p>
            <p><strong>Documents Processed:</strong> {uploadResults.documents_processed}</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="file-upload-container">
      <div className="upload-mode-selector">
        <button
          className={`mode-btn ${uploadMode === 'single' ? 'active' : ''}`}
          onClick={() => setUploadMode('single')}
          disabled={uploading}
        >
          <File size={16} />
          Single File
        </button>
        <button
          className={`mode-btn ${uploadMode === 'multiple' ? 'active' : ''}`}
          onClick={() => setUploadMode('multiple')}
          disabled={uploading}
        >
          <Folder size={16} />
          Multiple Files
        </button>
        <button
          className={`mode-btn ${uploadMode === 'zip' ? 'active' : ''}`}
          onClick={() => setUploadMode('zip')}
          disabled={uploading}
        >
          <Archive size={16} />
          ZIP Folder
        </button>
        <button
          className={`mode-btn ${uploadMode === 'manual' ? 'active' : ''}`}
          onClick={() => setUploadMode('manual')}
          disabled={uploading}
        >
          <BookOpen size={16} />
          PDF Manual
        </button>
      </div>

      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        
        {uploading ? (
          <div className="upload-progress">
            <Loader className="spinner" size={48} />
            <p>Processing files...</p>
          </div>
        ) : (
          <div className="upload-prompt">
            <Upload size={48} />
            <h3>
              {uploadMode === 'single' && 'Drop a file here or click to browse'}
              {uploadMode === 'multiple' && 'Drop multiple files here or click to browse'}
              {uploadMode === 'zip' && 'Drop a ZIP file here or click to browse'}
              {uploadMode === 'manual' && 'Drop a PDF manual here or click to browse'}
            </h3>
            <p>
              {uploadMode === 'manual' 
                ? 'PDF manuals only - extracts full text content for AI chat'
                : 'Supported formats: PDF, Excel (.xlsx, .xls), ZIP'
              }
            </p>
          </div>
        )}
      </div>

      {renderUploadResults()}
    </div>
  );
};
