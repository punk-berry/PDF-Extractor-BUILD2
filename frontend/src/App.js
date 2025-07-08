import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage';
import PDFViewer from './components/PDFViewer';
import Header from './components/Header';

function App() {
  const [currentFile, setCurrentFile] = useState(null);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <Routes>
          <Route 
            path="/" 
            element={
              <HomePage 
                onFileUploaded={setCurrentFile} 
                currentFile={currentFile}
              />
            } 
          />
          <Route 
            path="/extract/:fileId" 
            element={<PDFViewer />} 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;