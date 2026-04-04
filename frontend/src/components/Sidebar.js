import React from "react";
import UploadSection from "./UploadSection";
import ProjectStructure from "./ProjectStructure";
import FileSummaries from "./FileSummaries";

const Sidebar = ({
  isOpen,
  historyList,
  currentConversationId,
  loadConversation,
  deleteHistory,
  uploadFiles,
  isUploading,
  lastLogs,
  structure,
  selectedFiles,
  setSelectedFiles,
  handleFileSelect,
  handleDelete,
  summaries
}) => {
  return (
    <aside className={`sidebar ${!isOpen ? 'collapsed' : ''}`}>
      <div className="sidebar-scrollable">
        {/* History Section */}
        <div className="sidebar-section">
          <h3 className="section-title">🕒 Chat History</h3>
          <div className="history-list">
            {historyList.length === 0 ? (
              <p className="empty-msg">No history yet.</p>
            ) : (
              historyList.map(item => (
                <div key={item.filename} className={`history-item ${currentConversationId === item.filename ? 'active' : ''}`}>
                  <div className="history-info" onClick={() => loadConversation(item.filename)}>
                    <span className="history-title" title={item.title}>{item.title}</span>
                    <span className="history-date">
                      {new Date(item.timestamp.replace(/(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/, '$1-$2-$3 $4:$5:$6')).toLocaleDateString()}
                    </span>
                  </div>
                  <button className="delete-history" onClick={() => deleteHistory(item.filename)} title="Delete History">×</button>
                </div>
              ))
            )}
          </div>
        </div>

        <UploadSection uploadFiles={uploadFiles} isUploading={isUploading} lastLogs={lastLogs} />
      
        <ProjectStructure 
          structure={structure} 
          selectedFiles={selectedFiles}
          setSelectedFiles={setSelectedFiles}
          handleFileSelect={handleFileSelect}
          onDelete={handleDelete}
        />

        <FileSummaries summaries={summaries} />
      </div>
    </aside>
  );
};

export default Sidebar;
