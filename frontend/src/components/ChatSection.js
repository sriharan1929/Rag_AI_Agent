import React, { useRef, useEffect } from "react";
import Markdown from "./Markdown";

const ChatSection = ({
  inputRef,
  question,
  handleInputChange,
  handleKeyDown,
  askQuestion,
  showAutocomplete,
  filteredFiles,
  autocompleteIndex,
  setAutocompleteIndex,
  selectFile,
  loading,
  setSelectedFiles,
  messages,
  downloadConversation,
  streamingAnswer,
  streamingAnswers,
  compareMode,
  setCompareMode,
  selectedModels,
  setSelectedModels,
  availableModels,
  pinToCanvas,
  selectedFiles,
  handleImageChange,
  imagePreview,
  removeImage,
  retryLastQuery
}) => {
  const scrollRef = useRef(null);
  const hasMessages = messages.length > 0 || streamingAnswer;

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingAnswer, loading]);

  const removeFocusedFile = (file) => {
    setSelectedFiles(prev => prev.filter(f => f !== file));
  };

  return (
    <>
      <div className="chat-container" ref={scrollRef}>
        {!hasMessages && (
          <div className="chat-welcome">
            <div style={{ fontSize: '3rem', marginBottom: '20px' }}>🤖</div>
            <h2>How can I help you today?</h2>
            <p>
              Upload your files, select them from the sidebar, and ask anything. 
              Use <strong>@filename</strong> to reference specific documents.
            </p>
          </div>
        )}

        <div className="message-list">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role === 'user' ? 'message-user' : msg.isComparative ? 'message-comparative-container' : 'message-ai'}`}>
              <div className={`message-avatar ${msg.role === 'user' ? 'avatar-user' : 'avatar-ai'}`}>
                {msg.role === 'user' ? '' : 'Ai'}
              </div>
              
              {msg.isComparative ? (
                <div className="comparative-grid">
                  {msg.responses.map((resp, rIdx) => (
                    <div key={rIdx} className="comparative-column">
                      <div className="model-tag">{resp.model}</div>
                      <div className="message-body">
                        <strong>Focus: {resp.topic || 'Document'}</strong>
                        <div className="markdown-content">
                          <Markdown>{resp.content}</Markdown>
                        </div>
                        <div className="message-meta">Source: {resp.source}</div>
                        <button className="pin-button" onClick={() => pinToCanvas(resp.content, resp.source)}>
                          📌 Pin
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="message-body">
                  {msg.role === 'user' && msg.image && (
                    <div className="user-message-image">
                      <img src={msg.image} alt="User upload" onClick={() => window.open(msg.image, '_blank')} />
                    </div>
                  )}
                  {msg.role === 'assistant' && (
                    <strong>{msg.isRelevant ? `Focus: ${msg.topic || 'Document'}` : 'General Knowledge'}</strong>
                  )}
                  <div className="markdown-content">
                    <Markdown>{msg.content}</Markdown>
                  </div>
                  {msg.role === 'assistant' && msg.images && msg.images.length > 0 && (
                    <div className="message-images">
                      {msg.images.map((img, i) => (
                        <div key={i} className="image-card" onClick={() => window.open(img.url, '_blank')}>
                          <img src={img.url} alt={img.title} loading="lazy" />
                          <div className="image-title">{img.title}</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {msg.role === 'assistant' && msg.web_results && msg.web_results.length > 0 && (
                    <div className="web-sources-section">
                      <h4>🌐 Web Sources</h4>
                      <div className="web-sources-list">
                        {msg.web_results.map((res, i) => (
                          <div key={i} className="web-source-item">
                            <a href={res.link} target="_blank" rel="noopener noreferrer" className="web-source-title">
                              {res.title}
                            </a>
                            <p className="web-source-snippet">{res.snippet}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {msg.role === 'assistant' && msg.source && (
                    <div className="message-meta">Source: {msg.source}</div>
                  )}
                  {msg.role === 'assistant' && (
                    <button className="pin-button" onClick={() => pinToCanvas(msg.content, msg.source)}>
                      📌 Pin to Canvas
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Streaming Bubble(s) */}
          {loading && (
            <div className={`message ${compareMode ? 'message-comparative-container' : 'message-ai'}`}>
              <div className="message-avatar avatar-ai">Ai</div>
              
              {compareMode && Object.keys(streamingAnswers).length > 0 ? (
                <div className="comparative-grid">
                  {Object.entries(streamingAnswers).map(([model, content], sIdx) => (
                    <div key={sIdx} className="comparative-column">
                      <div className="model-tag">{model}</div>
                      <div className="message-body">
                        <strong>Answering...</strong>
                        <Markdown>{content}</Markdown>
                        <span className="streaming-cursor" />
                      </div>
                    </div>
                  ))}
                  {/* Show empty columns for models that haven't started yet */}
                  {selectedModels.filter(m => !streamingAnswers[m]).map(m => (
                    <div key={m} className="comparative-column">
                      <div className="model-tag">{m}</div>
                      <div className="message-body">
                        <div className="ai-loader-dots"><span></span><span></span><span></span></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : streamingAnswer ? (
                <div className="message-body">
                  <strong>Focus: Answering...</strong>
                  <Markdown>{streamingAnswer}</Markdown>
                  <span className="streaming-cursor" />
                </div>
              ) : (
                <div className="message-body">
                  <div className="ai-loader-container">
                    <div className="ai-loader-dots"><span></span><span></span><span></span></div>
                    <span style={{ fontSize: '0.875rem', color: '#64748b' }}>AI is specialized in processing your data...</span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="chat-input-wrapper">
        {selectedFiles.length > 0 && (
          <div className="focus-tags-container">
            <span className="focus-label">Focusing: </span>
            {selectedFiles.map(file => (
              <div key={file} className="focus-tag">
                <span className="focus-filename" title={file}>@{file}</span>
                <button onClick={() => removeFocusedFile(file)} className="remove-tag">×</button>
              </div>
            ))}
          </div>
        )}
        <div className="chat-controls-bar">
          <div className="compare-toggle">
            <label className="switch-label">
              <input 
                type="checkbox" 
                checked={compareMode} 
                onChange={(e) => setCompareMode(e.target.checked)} 
              />
              <span className="switch-text">⚖️ Compare Mode</span>
            </label>
          </div>
          {compareMode && (
            <div className="model-selectors">
              {(availableModels.length > 0 ? availableModels : ["mistral", "llama3"]).map(m => (
                <label key={m} className="model-checkbox">
                  <input 
                    type="checkbox" 
                    checked={selectedModels.includes(m)}
                    onChange={(e) => {
                      if (e.target.checked) setSelectedModels([...selectedModels, m]);
                      else setSelectedModels(selectedModels.filter(sm => sm !== m));
                    }}
                  />
                  <span>{m}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        {imagePreview && (
          <div className="image-preview-container">
            <img src={imagePreview} alt="Preview" />
            <button className="remove-image-btn" onClick={removeImage}>×</button>
          </div>
        )}

        <div className="chat-input-container">
          <label className="image-upload-label" title="Upload Image">
            <span style={{ fontSize: '1.2rem', cursor: 'pointer' }}>🖼️</span>
            <input 
              type="file" 
              accept="image/*" 
              onChange={handleImageChange} 
              style={{ display: 'none' }} 
            />
          </label>
          <input
            ref={inputRef}
            type="text"
            placeholder="Ask a question or use @ to mention a file..."
            value={question}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
          />
          <button onClick={() => askQuestion()} disabled={loading} className="send-btn">
            {loading ? "..." : "Send"}
          </button>
          <button 
            onClick={retryLastQuery} 
            disabled={loading || messages.filter(m => m.role === 'user').length === 0} 
            className="retry-btn"
            title="Retry last query"
          >
            ↺
          </button>

          {showAutocomplete && filteredFiles.length > 0 && (
            <ul className="autocomplete-dropdown">
              {filteredFiles.map((file, i) => (
                <li
                  key={file}
                  onClick={() => selectFile(file)}
                  onMouseEnter={() => setAutocompleteIndex(i)}
                  style={{
                    background: i === autocompleteIndex ? '#f1f5f9' : 'transparent',
                  }}
                >
                  <span style={{ marginRight: '8px' }}>📄</span> {file}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </>
  );
};

export default ChatSection;
