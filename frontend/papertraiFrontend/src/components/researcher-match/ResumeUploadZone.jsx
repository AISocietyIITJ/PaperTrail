import React from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, File } from 'lucide-react';
import './researcher-match.css';

export default function ResumeUploadZone({ onFileSelect, selectedFile }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: acceptedFiles => {
      if (acceptedFiles.length > 0) {
        onFileSelect(acceptedFiles[0]);
      }
    },
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1
  });

  return (
    <div 
      {...getRootProps()} 
      className={`upload-zone ${isDragActive ? 'active' : ''} ${selectedFile ? 'has-file' : ''}`}
    >
      <input {...getInputProps()} />
      
      {selectedFile ? (
        <div className="upload-content file-selected">
          <File size={32} className="file-icon" />
          <div className="file-info">
            <span className="file-name">{selectedFile.name}</span>
            <span className="file-size">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</span>
          </div>
          <p className="upload-hint">Click or drag to replace</p>
        </div>
      ) : (
        <div className="upload-content">
          <UploadCloud size={40} className="upload-icon" />
          <p className="upload-text">
            {isDragActive ? "Drop resume here..." : "Drag & drop resume here, or click to select"}
          </p>
          <p className="upload-hint">PDF only</p>
        </div>
      )}
    </div>
  );
}
