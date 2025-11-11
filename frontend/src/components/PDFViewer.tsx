import React from 'react';
import { X } from 'lucide-react';
import './PDFViewer.css';

interface PDFViewerProps {
  filename: string;
  pdfPath: string | null;
  onClose: () => void;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({ filename, pdfPath, onClose }) => {
  if (!pdfPath) {
    return null;
  }

  const pdfUrl = `http://localhost:8000/api/files/${pdfPath}`;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="pdf-viewer-overlay" onClick={handleBackdropClick}>
      <div className="pdf-viewer-container">
        <div className="pdf-viewer-header">
          <h3>{filename}</h3>
          <button className="close-button" onClick={onClose} aria-label="Close">
            <X size={24} />
          </button>
        </div>
        <div className="pdf-viewer-content">
          <iframe
            src={pdfUrl}
            title={filename}
            className="pdf-iframe"
          />
        </div>
      </div>
    </div>
  );
};
