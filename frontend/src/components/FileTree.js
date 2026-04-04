import React, { useState } from "react";

const FileTree = ({ data, path = "", selectedFiles, onSelect, onDelete }) => {
  const [expandedFolders, setExpandedFolders] = useState({});

  const toggleFolder = (folderPath, e) => {
    e.stopPropagation();
    setExpandedFolders(prev => ({ ...prev, [folderPath]: !prev[folderPath] }));
  };

  if (!data) return null;

  return (
    <ul className="file-tree" style={{ paddingLeft: path ? '16px' : '0' }}>
      {Object.entries(data).map(([key, value]) => {
        const isFile = value === null;
        const fullPath = path + key;
        const isSelected = selectedFiles.includes(fullPath);
        const isExpanded = expandedFolders[fullPath] !== false; // Default to expanded
        
        return (
          <li key={fullPath}>
            <div 
              className={`tree-node ${isSelected ? 'active' : ''}`}
              onClick={(e) => isFile ? onSelect(fullPath) : toggleFolder(fullPath, e)}
            >
              {isFile && (
                <input 
                  type="checkbox" 
                  checked={isSelected}
                  onChange={(e) => {
                    e.stopPropagation();
                    onSelect(fullPath);
                  }}
                />
              )}
              <span style={{ marginRight: '6px', opacity: isFile ? 0.7 : 1, minWidth: '16px', display: 'inline-block' }}>
                {isFile ? "📄" : (isExpanded ? "📂" : "📁")}
              </span>
              <span className="node-label" title={key} style={{ fontWeight: isFile ? 400 : 600, flex: 1, wordBreak: 'break-word', whiteSpace: 'normal', lineHeight: '1.2' }}>
                {key}
              </span>
              <button 
                className="delete-item-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(fullPath);
                }}
                title="Delete"
              >
                🗑️
              </button>
            </div>
            {!isFile && isExpanded && (
              <div style={{ borderLeft: '1px solid #e2e8f0', marginLeft: '8px' }}>
                <FileTree 
                  data={value} 
                  path={fullPath + "/"} 
                  selectedFiles={selectedFiles} 
                  onSelect={onSelect} 
                  onDelete={onDelete}
                />
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
};

export default FileTree;
