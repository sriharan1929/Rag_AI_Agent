import React, { useEffect } from "react";

const UploadSection = ({ uploadFiles, isUploading, lastLogs }) => {
  useEffect(() => {
    const logsTerminal = document.getElementById("logs-terminal");
    if (logsTerminal) {
      logsTerminal.scrollTop = logsTerminal.scrollHeight;
    }
  }, [lastLogs]);

  return (
    <div className="card">
      <h2>Knowledge Source</h2>
      <div className="upload-zone">
        <span className="upload-icon">📤</span>
        <div className="upload-text">
          <strong>Click to upload</strong> or drag and drop
          <p style={{ margin: '4px 0 0', fontSize: '0.75rem', opacity: 0.7 }}>
            PDF, Word, Excel, ZIP or Code files
          </p>
        </div>
        <input 
          type="file" 
          accept=".zip,.pdf,.doc,.docx,.xls,.xlsx,.txt,.js,.ts,.jsx,.tsx,.css,.html,.htm,.py,.json,.xml,.csv,.md,.c,.cpp,.cs,.go,.java,.rb,.php,.ppt,.pptx,.odt,.ods,.odp,.rtf"
          multiple 
          onChange={uploadFiles} 
          disabled={isUploading}
        />
      </div>
      
      {isUploading && (
        <div className="ai-loader-container" style={{ marginTop: '16px', padding: '12px', background: '#f8fafc', borderRadius: '8px' }}>
          <div className="ai-loader-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span style={{ fontSize: '0.85rem', color: '#6366f1', fontWeight: '500' }}>
            {lastLogs && lastLogs.length > 0 ? "Indexing knowledge..." : "Uploading files..."}
          </span>
        </div>
      )}

      {lastLogs && lastLogs.length > 0 && (
        <div className="indexing-logs" style={{ marginTop: isUploading ? '8px' : '16px' }}>
          <div className="logs-header">Indexing Logs {isUploading && " (Live)"}</div>
          <div className="logs-content" id="logs-terminal">
            {lastLogs.map((log, i) => (
              <div key={i} className="log-line">
                <span className="log-marker">›</span> {log}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadSection;
