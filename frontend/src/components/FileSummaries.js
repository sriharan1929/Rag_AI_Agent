import React from "react";

const FileSummaries = ({ summaries }) => {
  return (
    <div className="card">
      <h2>Document Insights</h2>
      {Object.keys(summaries).length === 0 ? (
        <p className="empty-text" style={{ fontSize: '0.8125rem' }}>Upload files to see summaries.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {Object.entries(summaries).map(([file, summary]) => (
            <div 
              key={file}
              style={{ 
                padding: '10px', 
                background: '#f8fafc', 
                borderRadius: '8px', 
                borderLeft: '3px solid #6366f1' 
              }}
            >
              <div style={{ fontWeight: 600, fontSize: '0.75rem', marginBottom: '2px', color: '#475569' }}>
                {file}
              </div>
              <div style={{ fontSize: '0.8125rem', color: '#64748b', lineHeight: '1.4' }}>
                {summary}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileSummaries;
