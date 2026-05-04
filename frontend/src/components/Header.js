import React from "react";

const Header = ({
  sidebarOpen,
  setSidebarOpen,
  currentView,
  setCurrentView,
  messages,
  downloadConversation,
  downloadConversationPDF,
  nodesCount,
  webSearch,
  setWebSearch,
  newChat,
  queryMode,
  setQueryMode,
  hasImage
}) => {
  return (
    <header className="app-header">
      <div className="logo-section">
        <button 
          className="hamburger-menu" 
          onClick={() => setSidebarOpen(!sidebarOpen)}
          title="Toggle Sidebar"
        >
          ☰
        </button>
        <h1><span className="logo-icon">📁</span> priyankx AI</h1>
      </div>
      
      <div className="title-section">
        <h2>{currentView === 'chat' ? 'Conversational Agent' : 'Knowledge Canvas'}</h2>
      </div>
      
      <div className="controls-section">
        {messages.length > 0 && (
          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              className="secondary-button" 
              onClick={downloadConversation}
              style={{ fontSize: '0.8rem', padding: '6px 12px', display: 'flex', alignItems: 'center', gap: '6px' }}
              title="Download Chat History (TXT)"
            >
              📥 TXT
            </button>
            <button 
              className="secondary-button" 
              onClick={downloadConversationPDF}
              style={{ 
                fontSize: '0.8rem', 
                padding: '6px 12px', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '6px',
                backgroundColor: '#fee2e2',
                color: '#dc2626',
                borderColor: '#fecaca'
              }}
              title="Download Chat History (PDF)"
            >
              📄 PDF
            </button>
          </div>
        )}
        <div className="view-toggle">
          <button 
            className={currentView === 'chat' ? 'active' : ''} 
            onClick={() => setCurrentView('chat')}
          >
            💬 Chat {'>'}
          </button>
          <button 
            className={currentView === 'canvas' ? 'active' : ''} 
            onClick={() => setCurrentView('canvas')}
          >
            🎨 Canvas ({nodesCount})
          </button>
        </div>

        <div className="web-toggle">
          <button 
            className={webSearch ? 'active' : ''} 
            onClick={() => setWebSearch(!webSearch)}
            title={webSearch ? "Web Search is ENABLED" : "Web Search is DISABLED"}
          >
            {webSearch ? '🌐 Web ON' : '🌐 Web OFF'}
          </button>
        </div>
        
        {hasImage && (
          <div className="image-badge" title="Image Analysis Mode Active">
            <span>🖼️ Image Mode</span>
          </div>
        )}
        
        <div style={{ marginRight: '16px' }}>
          <button className="new-chat-btn" onClick={newChat}>
            + New Chat
          </button>
        </div>
        
        <div className="mode-toggle">
          <button 
            className={queryMode === 'basic' ? 'active' : ''} 
            onClick={() => setQueryMode('basic')}
          >
            Basic
          </button>
          <button 
            className={queryMode === 'advanced' ? 'active' : ''} 
            onClick={() => setQueryMode('advanced')}
          >
            Advanced AI
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
