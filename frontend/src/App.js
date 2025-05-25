import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import config from './config';
import './App.css';

function App() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fileInfo, setFileInfo] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStage, setProcessingStage] = useState('');

  const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200MB

  const validateFile = (file) => {
    if (!file) {
      throw new Error('No file selected');
    }

    if (file.size > MAX_FILE_SIZE) {
      throw new Error(`File size exceeds the maximum limit of ${MAX_FILE_SIZE / (1024 * 1024)}MB`);
    }

    const validExtensions = ['.nii', '.nii.gz'];
    const fileExtension = file.name.toLowerCase().slice(file.name.lastIndexOf('.'));
    if (!validExtensions.includes(fileExtension)) {
      throw new Error('Invalid file format. Please upload a NIfTI file (.nii or .nii.gz)');
    }
  };

  const onDrop = async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setLoading(true);
    setError(null);
    setResults(null);
    setFileInfo(null);
    setUploadProgress(0);
    setProcessingStage('Validating file...');

    try {
      validateFile(file);
      
      setProcessingStage('Uploading file...');
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${config.apiUrl}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        },
      });

      setProcessingStage('Processing results...');
      setResults(response.data);
      setFileInfo(response.data.image_info);
    } catch (err) {
      let errorMessage = 'An error occurred while processing the file';
      if (err.response?.data?.error) {
        errorMessage = err.response.data.error;
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
      setProcessingStage('');
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/x-nifti': ['.nii', '.nii.gz'],
    },
    multiple: false,
    maxSize: MAX_FILE_SIZE,
  });

  const renderMatrix = (matrix) => {
    if (!matrix) return null;
    
    const maxValue = Math.max(...matrix.flat());
    const minValue = Math.min(...matrix.flat());
    const range = maxValue - minValue;

    return (
      <div className="matrix-container">
        <div className="matrix-legend">
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: 'rgba(0, 128, 255, 1)' }}></span>
            <span>Strong Connection ({maxValue.toFixed(2)})</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: 'rgba(0, 128, 255, 0.5)' }}></span>
            <span>Medium Connection</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: 'rgba(0, 128, 255, 0)' }}></span>
            <span>Weak Connection ({minValue.toFixed(2)})</span>
          </div>
        </div>
        <table>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) => {
                  const normalizedValue = (cell - minValue) / range;
                  return (
                    <td 
                      key={j}
                      style={{
                        backgroundColor: `rgba(0, 128, 255, ${normalizedValue})`,
                      }}
                      title={`Value: ${cell.toFixed(3)}`}
                    >
                      {cell.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderConnectionTable = (table) => {
    if (!table) return null;
    
    return (
      <div className="connection-table-container">
        <table>
          <thead>
            <tr>
              <th>Region 1</th>
              <th>Region 2</th>
              <th>Connection Strength</th>
            </tr>
          </thead>
          <tbody>
            {table.map((row, i) => (
              <tr key={i}>
                <td>{row['Region 1']}</td>
                <td>{row['Region 2']}</td>
                <td>{row['Connection Strength'].toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Brain Connectivity Analysis</h1>
        <p>Upload your NIfTI file to analyze brain connectivity</p>
      </header>

      <main>
        <div className="upload-section">
          <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            {isDragActive ? (
              <p>Drop the brain imaging file here...</p>
            ) : (
              <div>
                <p>Drag and drop a NIfTI file here, or click to select one</p>
                <p className="file-types">Supported formats: .nii, .nii.gz (Max size: 200MB)</p>
              </div>
            )}
          </div>
        </div>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>{processingStage}</p>
            {uploadProgress > 0 && (
              <div className="progress-bar">
                <div 
                  className="progress-bar-fill"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
                <span className="progress-text">{uploadProgress}%</span>
              </div>
            )}
          </div>
        )}
        
        {error && (
          <div className="error">
            <h3>Error</h3>
            <p>{error}</p>
            <p className="error-help">Please ensure you're uploading a valid NIfTI file (.nii or .nii.gz) under 200MB.</p>
          </div>
        )}

        {fileInfo && (
          <div className="file-info">
            <h3>File Information</h3>
            <p>Image Shape: {fileInfo.shape.join(' x ')}</p>
            <p>Header: {fileInfo.header}</p>
          </div>
        )}

        {results && (
          <div className="results">
            <h2>Analysis Results</h2>
            
            <div className="visualization-grid">
              <div className="connectome-image">
                <h3>Brain Connectome</h3>
                <p className="matrix-description">
                  The brain connectome visualization shows the network of connections between different brain regions.
                  Each node represents a brain region, and the lines between nodes show the strength of their connections.
                </p>
                {results.files?.connectome && (
                  <img 
                    src={`${config.apiUrl}/api/connectome/${results.files.connectome}`} 
                    alt="Brain Connectome" 
                    className="connectome-img"
                  />
                )}
              </div>

              <div className="connectivity-matrix">
                <h3>Connectivity Matrix</h3>
                <p className="matrix-description">
                  The connectivity matrix shows the strength of connections between different brain regions.
                  Darker colors indicate stronger connections, while lighter colors indicate weaker connections.
                  Hover over cells to see exact values.
                </p>
                {results.files?.matrix && (
                  <img 
                    src={`${config.apiUrl}/api/matrix/${results.files.matrix}`} 
                    alt="Connectivity Matrix" 
                    className="matrix-img"
                  />
                )}
                {renderMatrix(results.connectivity_matrix)}
              </div>

              <div className="connection-table">
                <h3>Connection Strength Table</h3>
                <p className="table-description">
                  This table shows the detailed view of connections between brain regions, sorted by connection strength.
                  Positive values indicate positive correlations, while negative values indicate negative correlations.
                </p>
                {results.metrics?.connection_table && (
                  renderConnectionTable(results.metrics.connection_table)
                )}
                {results.files?.connections && (
                  <a 
                    href={`${config.apiUrl}/api/connections/${results.files.connections}`}
                    className="download-link"
                    download
                  >
                    Download Full Connection Table (CSV)
                  </a>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="help-section">
          <h3>How to Use</h3>
          <ol>
            <li>Prepare your NIfTI file (.nii or .nii.gz format)</li>
            <li>Upload the file using the drag-and-drop area or click to select</li>
            <li>Wait for the processing to complete</li>
            <li>View the brain connectome, connectivity matrix, and connection strength table</li>
          </ol>
        </div>
      </main>
    </div>
  );
}

export default App; 