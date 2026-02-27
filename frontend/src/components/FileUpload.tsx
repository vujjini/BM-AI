import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, Archive, CheckCircle, AlertCircle, Loader, Box as BoxIcon, CheckSquare, Square } from 'lucide-react';
import { apiService, UploadResponse, FolderUploadResponse, BoxFolder, JobStatusResponse } from '../services/api';
import './FileUpload.css';

interface FileUploadProps {
  onUploadSuccess: (message: string) => void;
  onUploadError: (error: string) => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess, onUploadError }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadMode, setUploadMode] = useState<'single' | 'zip' | 'box'>('single');
  const [uploadResults, setUploadResults] = useState<any>(null);

  // Box Integration State
  const [boxFolders, setBoxFolders] = useState<BoxFolder[]>([]);
  const [selectedFolderIds, setSelectedFolderIds] = useState<string[]>([]);
  const [loadingFolders, setLoadingFolders] = useState(false);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatusResponse | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (uploadMode === 'box') {
      fetchBoxFolders();
    }
  }, [uploadMode]);

  const fetchBoxFolders = async () => {
    setLoadingFolders(true);
    try {
      const folders = await apiService.getBoxFolders();
      setBoxFolders(folders);
    } catch (error: any) {
      console.error("Failed to fetch Box folders", error);
      onUploadError("Failed to fetch Box folders. Please check connection.");
    } finally {
      setLoadingFolders(false);
    }
  };

  const handleFolderToggle = (folderId: string) => {
    setSelectedFolderIds(prev => {
      if (prev.includes(folderId)) {
        return prev.filter(id => id !== folderId);
      } else {
        return [...prev, folderId];
      }
    });
  };

  // Poll job status every 3 seconds until complete or failed
  useEffect(() => {
    if (!activeJobId) return;

    pollingRef.current = setInterval(async () => {
      try {
        const status = await apiService.getJobStatus(activeJobId);
        setJobStatus(status);

        if (status.status === 'complete') {
          clearInterval(pollingRef.current!);
          pollingRef.current = null;
          setActiveJobId(null);
          setUploading(false);
          onUploadSuccess(`Box ingestion complete: ${status.processed_count ?? status.current} file(s) processed.`);
        } else if (status.status === 'failed') {
          clearInterval(pollingRef.current!);
          pollingRef.current = null;
          setActiveJobId(null);
          setUploading(false);
          onUploadError(`Box ingestion failed: ${status.details.join(', ')}`);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [activeJobId]);

  const handleBoxIngest = async () => {
    if (selectedFolderIds.length === 0) return;

    setUploading(true);
    setJobStatus(null);
    setUploadResults(null);

    try {
      const job = await apiService.ingestBoxFolders(selectedFolderIds);
      setActiveJobId(job.job_id);
      // Polling kicks off via the useEffect above
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Box Ingestion failed';
      onUploadError(errorMessage);
      setUploading(false);
    }
  };

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setUploadResults(null);

    try {
      let result: UploadResponse | FolderUploadResponse;

      if (uploadMode === 'single' && acceptedFiles.length === 1) {
        const file = acceptedFiles[0];
        if (file.name.endsWith('.zip')) {
          result = await apiService.uploadZipFolder(file);
        } else {
          result = await apiService.uploadFile(file);
        }
      } else if (uploadMode === 'zip' && acceptedFiles.length === 1 && acceptedFiles[0].name.endsWith('.zip')) {
        result = await apiService.uploadZipFolder(acceptedFiles[0]);
      } else {
        throw new Error('Invalid file or upload mode');
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
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/zip': ['.zip']
    },
    multiple: false,
    disabled: uploading || uploadMode === 'box'
  });

  const renderUploadResults = () => {
    if (!uploadResults) return null;

    const isFolderUpload = 'total_files_processed' in uploadResults;
    const isBoxUpload = uploadMode === 'box'; // reused structure mostly

    return (
      <div className="upload-results">
        <div className="results-header">
          <CheckCircle className="success-icon" size={20} />
          <h3>Processing Complete</h3>
        </div>

        {isFolderUpload ? (
          <div className="folder-results">
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Files Processed:</span>
                <span className="stat-value">{uploadResults.total_files_processed}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Successful:</span>
                <span className="stat-value success">{uploadResults.successful_files}</span>
              </div>
              {uploadResults.failed_files > 0 && (
                <div className="stat-item">
                  <span className="stat-label">Failed:</span>
                  <span className="stat-value error">{uploadResults.failed_files}</span>
                </div>
              )}
            </div>

            {uploadResults.file_results && uploadResults.file_results.length > 0 && (
              <div className="file-results">
                <h4>Details:</h4>
                {uploadResults.file_results.map((result: any, index: number) => (
                  <div key={index} className={`file-result ${result.success ? 'success' : 'error'}`}>
                    <div className="file-info">
                      {result.success ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                      <span className="filename">{result.filename}</span>
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
          className={`mode-btn ${uploadMode === 'zip' ? 'active' : ''}`}
          onClick={() => setUploadMode('zip')}
          disabled={uploading}
        >
          <Archive size={16} />
          ZIP Folder
        </button>
        <button
          className={`mode-btn ${uploadMode === 'box' ? 'active' : ''}`}
          onClick={() => setUploadMode('box')}
          disabled={uploading}
        >
          <BoxIcon size={16} />
          Box Import
        </button>
      </div>

      {uploadMode === 'box' ? (
        <div className="box-selection-area">
          {loadingFolders ? (
            <div className="upload-progress">
              <Loader className="spinner" size={48} />
              <p>Fetching Box folders...</p>
            </div>
          ) : uploading && jobStatus ? (
            // ── Live Progress Bar ──────────────────────────────────────────
            <div className="box-job-progress">
              <div className="job-header">
                <Loader className="spinner" size={20} />
                <h3>Ingesting from Box…</h3>
              </div>
              <div className="progress-bar-wrap">
                <div
                  className="progress-bar-fill"
                  style={{
                    width: jobStatus.total > 0
                      ? `${Math.round((jobStatus.current / jobStatus.total) * 100)}%`
                      : '5%',
                  }}
                />
              </div>
              <p className="progress-label">
                {jobStatus.total > 0
                  ? `${jobStatus.current} / ${jobStatus.total} files`
                  : 'Preparing…'}
              </p>
              {jobStatus.details.length > 0 && (
                <ul className="job-details-list">
                  {jobStatus.details.slice(-5).map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              )}
            </div>
          ) : uploading ? (
            // Queued — job dispatched but no status yet
            <div className="upload-progress">
              <Loader className="spinner" size={48} />
              <p>Job queued — waiting for worker…</p>
            </div>
          ) : (
            // ── Folder Selection ───────────────────────────────────────────
            <div className="box-folders-list">
              <h3>Select Months to Ingest</h3>
              {boxFolders.length === 0 ? (
                <p className="no-folders">No "Month 2025" folders found in Box.</p>
              ) : (
                <div className="folders-grid">
                  {boxFolders.map(folder => (
                    <div
                      key={folder.id}
                      className={`folder-item ${selectedFolderIds.includes(folder.id) ? 'selected' : ''}`}
                      onClick={() => handleFolderToggle(folder.id)}
                    >
                      {selectedFolderIds.includes(folder.id) ?
                        <CheckSquare size={20} className="checkbox checked" /> :
                        <Square size={20} className="checkbox" />
                      }
                      <span className="folder-name">{folder.name}</span>
                    </div>
                  ))}
                </div>
              )}

              <div className="box-actions">
                <button
                  className="ingest-btn"
                  onClick={handleBoxIngest}
                  disabled={selectedFolderIds.length === 0 || uploading}
                >
                  {`Ingest Selected (${selectedFolderIds.length})`}
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
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
                {uploadMode === 'zip' && 'Drop a ZIP file here or click to browse'}
              </h3>
              <p>
                Supported formats: PDF, Excel (.xlsx, .xls), ZIP
              </p>
            </div>
          )}
        </div>
      )}

      {renderUploadResults()}

      <style>{`
        .box-selection-area {
            padding: 20px;
            background: var(--bg-tertiary);
            border-radius: 16px;
            border: 1px solid var(--border-color);
        }
        .box-folders-list h3 {
            margin-top: 0;
            margin-bottom: 16px;
            color: var(--text-primary);
        }
        .folders-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 12px;
            margin-bottom: 24px;
            max-height: 300px;
            overflow-y: auto;
        }
        .folder-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .folder-item:hover {
            border-color: var(--accent-primary);
            background: var(--bg-hover);
        }
        .folder-item.selected {
            background: rgba(59, 130, 246, 0.1);
            border-color: var(--accent-primary);
        }
        .checkbox { color: var(--text-secondary); }
        .checkbox.checked { color: var(--accent-primary); }
        .folder-name { font-weight: 500; color: var(--text-primary); }
        .box-actions { display: flex; justify-content: flex-end; }
        .ingest-btn {
            background: var(--accent-primary);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .ingest-btn:hover:not(:disabled) { background: var(--accent-secondary); }
        .ingest-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .no-folders { color: var(--text-secondary); font-style: italic; }

        /* Progress bar */
        .box-job-progress { padding: 8px 0; }
        .job-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
        }
        .job-header h3 { margin: 0; color: var(--text-primary); }
        .progress-bar-wrap {
            width: 100%;
            background: var(--bg-secondary);
            border-radius: 999px;
            height: 10px;
            overflow: hidden;
            margin-bottom: 8px;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
            border-radius: 999px;
            transition: width 0.4s ease;
        }
        .progress-label {
            font-size: 13px;
            color: var(--text-secondary);
            margin: 0 0 12px 0;
        }
        .job-details-list {
            list-style: none;
            margin: 0;
            padding: 0;
            font-size: 12px;
            color: var(--text-secondary);
            max-height: 120px;
            overflow-y: auto;
        }
        .job-details-list li {
            padding: 3px 0;
            border-bottom: 1px solid var(--border-color);
        }
        .job-details-list li:last-child { border-bottom: none; }
      `}</style>
    </div>
  );
};
