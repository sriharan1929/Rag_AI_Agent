import React from "react";
import FileTree from "./FileTree";

const ProjectStructure = ({ structure, selectedFiles, setSelectedFiles, handleFileSelect, onDelete }) => {
  return (
    <div className="card">
      <h2>
        Project Files
        {selectedFiles.length > 0 && (
          <button 
            className="secondary-button"
            onClick={() => setSelectedFiles([])}
            style={{ 
              fontSize: '0.7rem', 
              padding: '2px 6px', 
              background: 'transparent',
              color: '#ef4444',
              border: '1px solid #fee2e2',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Clear ({selectedFiles.length})
          </button>
        )}
      </h2>
      {Object.keys(structure).length === 0 ? (
        <p className="empty-text" style={{ fontSize: '0.8125rem' }}>No files uploaded yet.</p>
      ) : (
        <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
          <FileTree 
            data={structure} 
            selectedFiles={selectedFiles} 
            onSelect={handleFileSelect} 
            onDelete={onDelete}
          />
        </div>
      )}
    </div>
  );
};

export default ProjectStructure;
