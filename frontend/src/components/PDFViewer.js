import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Document, Page, pdfjs } from 'react-pdf';
import axios from 'axios';

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;

const PDFViewer = () => {
  const { fileId } = useParams();
  const navigate = useNavigate();
  const [fileInfo, setFileInfo] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [selections, setSelections] = useState([]);
  const [isSelecting, setIsSelecting] = useState(false);
  const [currentSelection, setCurrentSelection] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionResult, setExtractionResult] = useState(null);
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const pageRef = useRef(null);
  const selectionRef = useRef(null);

  useEffect(() => {
    loadFileInfo();
  }, [fileId]);

  const loadFileInfo = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/files/${fileId}`);
      setFileInfo(response.data);
      setPdfUrl(`${process.env.REACT_APP_BACKEND_URL}/api/files/${fileId}/pdf`);
      setLoading(false);
    } catch (error) {
      setError('Failed to load file information');
      setLoading(false);
    }
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const handleMouseDown = (e) => {
    if (!isSelecting) return;
    
    const rect = pageRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setCurrentSelection({
      startX: x,
      startY: y,
      endX: x,
      endY: y,
      page: pageNumber - 1
    });
    
    selectionRef.current = { startX: x, startY: y };
  };

  const handleMouseMove = (e) => {
    if (!isSelecting || !currentSelection || !selectionRef.current) return;
    
    const rect = pageRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setCurrentSelection(prev => ({
      ...prev,
      endX: x,
      endY: y
    }));
  };

  const handleMouseUp = () => {
    if (!isSelecting || !currentSelection) return;
    
    // Only save selection if it's large enough
    const width = Math.abs(currentSelection.endX - currentSelection.startX);
    const height = Math.abs(currentSelection.endY - currentSelection.startY);
    
    if (width > 10 && height > 10) {
      const selection = {
        page: currentSelection.page,
        x1: Math.min(currentSelection.startX, currentSelection.endX) / scale,
        y1: Math.min(currentSelection.startY, currentSelection.endY) / scale,
        x2: Math.max(currentSelection.startX, currentSelection.endX) / scale,
        y2: Math.max(currentSelection.startY, currentSelection.endY) / scale,
        width: width / scale,
        height: height / scale
      };
      
      setSelections(prev => [...prev, selection]);
    }
    
    setCurrentSelection(null);
    selectionRef.current = null;
    setIsSelecting(false);
  };

  const removeSelection = (index) => {
    setSelections(prev => prev.filter((_, i) => i !== index));
  };

  const clearAllSelections = () => {
    setSelections([]);
  };

  const extractTables = async () => {
    if (selections.length === 0) {
      alert('Please select at least one table area');
      return;
    }

    setIsExtracting(true);
    setExtractionResult(null);

    try {
      const formData = new FormData();
      formData.append('file_id', fileId);
      formData.append('selections', JSON.stringify(selections));

      const response = await axios.post(
        `${process.env.REACT_APP_BACKEND_URL}/api/extract`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setExtractionResult(response.data);
    } catch (error) {
      alert('Failed to extract tables: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsExtracting(false);
    }
  };

  const downloadCSV = async () => {
    if (!extractionResult) return;

    try {
      const response = await axios.get(
        `${process.env.REACT_APP_BACKEND_URL}/api/jobs/${extractionResult.job_id}/download`,
        {
          responseType: 'blob',
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `extracted_tables_${extractionResult.job_id}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      alert('Failed to download CSV: ' + (error.response?.data?.detail || error.message));
    }
  };

  const renderSelection = (selection, index) => {
    if (selection.page !== pageNumber - 1) return null;

    const x = Math.min(selection.x1, selection.x2) * scale;
    const y = Math.min(selection.y1, selection.y2) * scale;
    const width = Math.abs(selection.x2 - selection.x1) * scale;
    const height = Math.abs(selection.y2 - selection.y1) * scale;

    return (
      <div
        key={index}
        className="selection-rectangle"
        style={{
          left: x,
          top: y,
          width: width,
          height: height,
        }}
        onClick={() => removeSelection(index)}
        title="Click to remove selection"
      />
    );
  };

  const renderCurrentSelection = () => {
    if (!currentSelection) return null;

    const x = Math.min(currentSelection.startX, currentSelection.endX);
    const y = Math.min(currentSelection.startY, currentSelection.endY);
    const width = Math.abs(currentSelection.endX - currentSelection.startX);
    const height = Math.abs(currentSelection.endY - currentSelection.startY);

    return (
      <div
        className="selection-overlay"
        style={{
          left: x,
          top: y,
          width: width,
          height: height,
        }}
      />
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner"></div>
        <span className="ml-3 text-gray-600">Loading PDF...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-red-800 mb-2">Error</h3>
          <p className="text-red-700">{error}</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{fileInfo?.filename}</h2>
            <p className="text-gray-600">
              Page {pageNumber} of {numPages} | {selections.length} selection(s)
            </p>
          </div>
          <button
            onClick={() => navigate('/')}
            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
          >
            Back to Home
          </button>
        </div>

        {/* Controls */}
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPageNumber(Math.max(1, pageNumber - 1))}
              disabled={pageNumber <= 1}
              className="bg-gray-100 hover:bg-gray-200 disabled:opacity-50 px-3 py-1 rounded"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600">
              {pageNumber} / {numPages}
            </span>
            <button
              onClick={() => setPageNumber(Math.min(numPages, pageNumber + 1))}
              disabled={pageNumber >= numPages}
              className="bg-gray-100 hover:bg-gray-200 disabled:opacity-50 px-3 py-1 rounded"
            >
              Next
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setScale(Math.max(0.5, scale - 0.1))}
              className="bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded"
            >
              Zoom Out
            </button>
            <span className="text-sm text-gray-600">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={() => setScale(Math.min(2.0, scale + 0.1))}
              className="bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded"
            >
              Zoom In
            </button>
          </div>

          <button
            onClick={() => setIsSelecting(!isSelecting)}
            className={`px-4 py-2 rounded ${
              isSelecting
                ? 'bg-red-500 hover:bg-red-600 text-white'
                : 'bg-primary-500 hover:bg-primary-600 text-white'
            }`}
          >
            {isSelecting ? 'Stop Selecting' : 'Select Table Area'}
          </button>

          {selections.length > 0 && (
            <button
              onClick={clearAllSelections}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
            >
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
        <div className="flex justify-center">
          <div
            ref={pageRef}
            className="pdf-page"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            style={{ cursor: isSelecting ? 'crosshair' : 'default' }}
          >
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              loading={<div className="spinner"></div>}
              error={<div className="text-red-600">Failed to load PDF</div>}
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                renderTextLayer={false}
                renderAnnotationLayer={false}
              />
            </Document>
            
            {/* Render saved selections */}
            {selections.map((selection, index) => renderSelection(selection, index))}
            
            {/* Render current selection */}
            {renderCurrentSelection()}
          </div>
        </div>
      </div>

      {/* Extraction Controls */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Extract Tables</h3>
        
        {selections.length === 0 ? (
          <p className="text-gray-600 mb-4">
            Select table areas by clicking "Select Table Area" and drawing rectangles around tables.
          </p>
        ) : (
          <div className="mb-4">
            <p className="text-gray-600 mb-2">
              {selections.length} area(s) selected across {new Set(selections.map(s => s.page)).size} page(s)
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              {selections.map((selection, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded">
                  <span className="text-sm text-gray-600">
                    Page {selection.page + 1} ({Math.round(selection.width)}x{Math.round(selection.height)})
                  </span>
                  <button
                    onClick={() => removeSelection(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex space-x-4">
          <button
            onClick={extractTables}
            disabled={selections.length === 0 || isExtracting}
            className="bg-primary-500 hover:bg-primary-600 disabled:opacity-50 text-white px-6 py-2 rounded"
          >
            {isExtracting ? 'Extracting...' : 'Extract Tables'}
          </button>

          {extractionResult && (
            <button
              onClick={downloadCSV}
              className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded"
            >
              Download CSV
            </button>
          )}
        </div>

        {extractionResult && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
            <h4 className="font-semibold text-green-800 mb-2">Extraction Complete!</h4>
            <p className="text-green-700">
              Tables extracted successfully. Click "Download CSV" to save the results.
            </p>
            {extractionResult.csv_data && (
              <div className="mt-3">
                <h5 className="font-medium text-green-800 mb-1">Preview:</h5>
                <pre className="text-sm text-green-700 bg-white p-2 rounded border max-h-32 overflow-y-auto">
                  {extractionResult.csv_data.split('\n').slice(0, 5).join('\n')}
                  {extractionResult.csv_data.split('\n').length > 5 && '\n...'}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PDFViewer;