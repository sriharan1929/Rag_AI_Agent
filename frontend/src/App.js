import axios from "axios";
import { useState, useRef, useEffect, useMemo } from "react";
import "./App.css";

import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import ChatSection from "./components/ChatSection";
import KnowledgeCanvas from "./components/KnowledgeCanvas";

import { useKnowledgeCanvas } from "./hooks/useKnowledgeCanvas";
import { useChatHistory } from "./hooks/useChatHistory";
import { downloadConversationPDF } from "./utils/pdfExport";
import { API_URL } from "./config";

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [structure, setStructure] = useState({});
  const [summaries, setSummaries] = useState({});
  const [question, setQuestion] = useState("");
  const [topic, setTopic] = useState("");
  const [results, setResults] = useState([]);
  const [generalAnswer, setGeneralAnswer] = useState("");
  const [isRelevant, setIsRelevant] = useState(true);
  const [loading, setLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [lastLogs, setLastLogs] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [streamingAnswer, setStreamingAnswer] = useState("");
  const [currentView, setCurrentView] = useState("chat"); 
  const [queryMode, setQueryMode] = useState("advanced"); 
  const [webSearch, setWebSearch] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [selectedModels, setSelectedModels] = useState(["mistral", "llama3"]);
  const [streamingAnswers, setStreamingAnswers] = useState({}); 
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [availableModels, setAvailableModels] = useState([]);

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addStickyNote,
    pinToCanvas,
    exportCanvas
  } = useKnowledgeCanvas(selectedFiles);

  const {
    historyList,
    currentConversationId,
    fetchHistory,
    saveConversation,
    loadConversation,
    deleteHistory,
    newChat
  } = useChatHistory({
    API_URL,
    setMessages,
    setCurrentView,
    setStreamingAnswer,
    setStreamingAnswers,
    setTopic,
    setIsRelevant,
    removeImage
  });

  const retryLastQuery = () => {
    if (messages.length === 0) return;
    const userMsgs = messages.filter(m => m.role === "user");
    if (userMsgs.length === 0) return;
    const lastUserMsg = userMsgs[userMsgs.length - 1];
    const lastUserIdx = messages.lastIndexOf(lastUserMsg);
    const newMessages = messages.slice(0, lastUserIdx);
    setMessages(newMessages);
    setQuestion(lastUserMsg.content || "");
    if (lastUserMsg.image) {
      setImagePreview(lastUserMsg.image);
    }
    setTimeout(() => askQuestion(), 10);
  };

  useEffect(() => {
    fetchFiles();
    fetchAvailableModels();
  }, []); // fetchHistory is handled inside useChatHistory's useEffect now

  const fetchAvailableModels = async () => {
    try {
      const res = await axios.get(`${API_URL}/models/list/`);
      if (res.data && res.data.models) {
        setAvailableModels(res.data.models);
        // If the current selected models are not in the list, pick the first two available
        if (res.data.models.length >= 2) {
          setSelectedModels([res.data.models[0], res.data.models[1]]);
        }
      }
    } catch (error) {
      console.error("Error fetching available models:", error);
    }
  };

  const fetchFiles = async () => {
    try {
      const res = await axios.get(`${API_URL}/list_files/`);
      setStructure(res.data.structure || {});
      setSummaries(res.data.summaries || {});
    } catch (error) {
      console.error("Error fetching initial files:", error);
    }
  };

  const handleDelete = async (path) => {
    if (!window.confirm(`Are you sure you want to delete "${path}"? This will also re-index the remaining files.`)) {
      return;
    }
    try {
      setIsUploading(true);
      setLastLogs([`[SYSTEM] Initiating deletion for: ${path}...`]);
      
      const response = await fetch(`${API_URL}/delete/?path=${encodeURIComponent(path)}`, { method: 'DELETE' });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Delete Failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); 

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.event === "log") {
              setLastLogs(prev => [...prev, data.message]);
            } else if (data.event === "metadata") {
              setStructure(data.structure || {});
              setSummaries(data.summaries || {});
              setSelectedFiles(prev => prev.filter(f => !f.startsWith(path)));
            } else if (data.event === "error") {
              console.error("Backend delete error:", data.detail);
              alert(data.detail);
            }
          } catch (e) {}
        }
      }

      if (buffer.trim()) {
        try {
          const data = JSON.parse(buffer);
          if (data.event === "metadata") {
            setStructure(data.structure || {});
            setSummaries(data.summaries || {});
            setSelectedFiles(prev => prev.filter(f => !f.startsWith(path)));
          }
        } catch (e) {}
      }

    } catch (error) {
      console.error("Delete failed", error);
      alert(error.message || "Delete failed");
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = (filePath) => {
    setSelectedFiles(prev => 
      prev.includes(filePath) ? prev.filter(f => f !== filePath) : [...prev, filePath]
    );
  };

  // --- @ Mentions Autocomplete State ---
  const [showAutocomplete, setShowAutocomplete] = useState(false);
  const [autocompleteQuery, setAutocompleteQuery] = useState("");
  const [autocompleteIndex, setAutocompleteIndex] = useState(0);
  const inputRef = useRef(null);

  const allFiles = useMemo(() => {
    const getFiles = (obj, path = "") => {
      let files = [];
      if (!obj) return files;
      for (const [key, value] of Object.entries(obj)) {
        const fullPath = path + key;
        if (value === null) {
          files.push(fullPath);
        } else {
          files = files.concat(getFiles(value, fullPath + "/"));
        }
      }
      return files;
    };
    return getFiles(structure);
  }, [structure]);
  
  const filteredFiles = allFiles.filter(f => f.toLowerCase().includes(autocompleteQuery));

  const handleInputChange = (e) => {
    const val = e.target.value;
    setQuestion(val);
    const cursor = e.target.selectionStart;
    const textBeforeCursor = val.slice(0, cursor);
    const match = textBeforeCursor.match(/@([a-zA-Z0-9_.-]*)$/);
    if (match) {
      setShowAutocomplete(true);
      setAutocompleteQuery(match[1].toLowerCase());
      setAutocompleteIndex(0);
    } else {
      setShowAutocomplete(false);
    }
  };

  const selectFile = (fileName) => {
    if (!inputRef.current) return;
    const cursor = inputRef.current.selectionStart;
    const textBefore = question.slice(0, cursor);
    const textAfter = question.slice(cursor);
    const newTextBefore = textBefore.replace(/@([a-zA-Z0-9_.-]*)$/, "");
    setQuestion(newTextBefore + textAfter);
    setShowAutocomplete(false);
    setSelectedFiles(prev => prev.includes(fileName) ? prev : [...prev, fileName]);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  const handleKeyDown = (e) => {
    if (showAutocomplete && filteredFiles.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setAutocompleteIndex((prev) => (prev + 1) % filteredFiles.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setAutocompleteIndex((prev) => (prev - 1 + filteredFiles.length) % filteredFiles.length);
        return;
      }
      if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        selectFile(filteredFiles[autocompleteIndex]);
        return;
      }
      if (e.key === "Escape") {
        setShowAutocomplete(false);
        return;
      }
    }
    if (e.key === "Enter") {
      askQuestion();
    }
  };

  const uploadFiles = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      setIsUploading(true);
      setLastLogs([]);
      setStructure({});
      setSummaries({});
      setTopic("");
      setResults([]);
      setGeneralAnswer("");
      setIsRelevant(true);

      const response = await fetch(`${API_URL}/upload/`, { method: 'POST', body: formData });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Upload Failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); 

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.event === "log") {
              setLastLogs(prev => [...prev, data.message]);
            } else if (data.event === "metadata") {
              setStructure(data.structure || {});
              if (data.newly_uploaded) {
                setSelectedFiles(prev => {
                  const next = [...prev];
                  data.newly_uploaded.forEach(file => {
                    if (!next.includes(file)) next.push(file);
                  });
                  return next;
                });
              }
            } else if (data.event === "done") {
              setSummaries(data.summaries || {});
              setLastLogs(data.logs || []);
            }
          } catch (e) {}
        }
      }
      alert("Files Uploaded and Indexed Successfully!");
    } catch (error) {
      console.error(error);
      alert(`Error: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const askQuestion = async (forcedQuestion = null, forcedImage = null) => {
    const activeQuestion = (typeof forcedQuestion === 'string') ? forcedQuestion : question;
    const activeImagePreview = (typeof forcedImage === 'string') ? forcedImage : imagePreview;

    if (!activeQuestion.trim() && !activeImagePreview) {
      alert("Please enter a question or upload an image.");
      return;
    }

    let base64Image = null;
    if (activeImagePreview) {
      base64Image = activeImagePreview.split(',')[1];
    }

    const userMsg = { role: "user", content: activeQuestion, image: activeImagePreview };
    setMessages(prev => [...prev, userMsg]);
    
    setLoading(true);
    setStreamingAnswer("");
    setStreamingAnswers({});
    setQuestion("");
    removeImage();

    let accumulated = "";
    let accumulatedMulti = {};
    let metaInfo = { isRelevant: true, topic: "", source: "", images: [], web_results: [] };

    try {
      const response = await fetch(`${API_URL}/ask_stream/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: activeQuestion,
          selected_files: selectedFiles, // Use array directly and correct key name
          mode: queryMode,
          web_search: webSearch,
          models: compareMode ? selectedModels.join(",") : null,
          images: base64Image ? [base64Image] : [] // Ensure it's an array, not null
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Request failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); 

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith("data: ")) continue;

          let data;
          try {
            data = JSON.parse(trimmed.slice(6));
          } catch (e) {
            continue;
          }

          if (data.event === "meta") {
            metaInfo = {
              isRelevant: data.isRelevant,
              topic: data.topic || "",
              source: data.source || "",
              images: data.images || [],
              web_results: data.web_results || []
            };
            setTopic(metaInfo.topic);
            setIsRelevant(metaInfo.isRelevant);
          } 
          else if (data.event === "token") {
            if (data.model) {
              accumulatedMulti[data.model] = (accumulatedMulti[data.model] || "") + data.text;
              setStreamingAnswers({ ...accumulatedMulti });
            } else {
              accumulated += data.text;
              setStreamingAnswer(accumulated);
            }
          }
          else if (data.event === "done") {
            setLoading(false);
            if (compareMode && Object.keys(accumulatedMulti).length > 0) {
              const aiMsg = { 
                role: "assistant", 
                isComparative: true,
                responses: Object.entries(accumulatedMulti).map(([model, content]) => ({
                  model,
                  content,
                  topic: metaInfo.topic,
                  source: metaInfo.source,
                  isRelevant: metaInfo.isRelevant,
                })),
                images: metaInfo.images,
                web_results: metaInfo.web_results
              };
              setMessages(prev => {
                const next = [...prev, aiMsg];
                saveConversation(next);
                return next;
              });
            } else {
              const aiMsg = { 
                role: "assistant", 
                content: accumulated, 
                topic: metaInfo.topic, 
                source: metaInfo.source,
                isRelevant: metaInfo.isRelevant,
                images: metaInfo.images,
                web_results: metaInfo.web_results
              };
              setMessages(prev => {
                const next = [...prev, aiMsg];
                saveConversation(next);
                return next;
              });
            }
            setStreamingAnswer("");
            setStreamingAnswers({});
          }
          else if (data.event === "error") {
            setLoading(false);
            setStreamingAnswer("");
            setStreamingAnswers({});
            alert(`Error: ${data.message || "An error occurred during streaming"}`);
          }
        }
      }
    } catch (error) {
      console.error("Fetch/SSE Error:", error);
      setLoading(false);
      setStreamingAnswer("");
      alert(`Error: ${error.message}`);
    }
  };

  const downloadConversation = () => {
    if (messages.length === 0) {
      alert("No conversation to download.");
      return;
    }
    const dateStr = new Date().toISOString().split('T')[0];
    let baseName = "conversation";
    if (selectedFiles && selectedFiles.length > 0) {
      const firstFile = selectedFiles[0].split('/').pop();
      const nameWithoutExt = firstFile.substring(0, firstFile.lastIndexOf('.')) || firstFile;
      baseName = nameWithoutExt;
      if (selectedFiles.length > 1) {
        baseName += `_and_${selectedFiles.length - 1}_others`;
      }
    }
    const defaultName = `${baseName}[${dateStr}]_chat`;
    const fileName = prompt("💾 Save your AI chat conversation as a text file:", defaultName);
    if (!fileName) return; 
    
    let text = "ZIP-RAG AI Chat Conversation\n============================\n\n";
    messages.forEach((msg) => {
      const role = msg.role === 'user' ? 'YOU' : 'AI';
      text += `[${role}]:\n${msg.content}\n`;
      if (msg.source) text += `(Source: ${msg.source})\n`;
      text += "\n----------------------------\n\n";
    });
    
    const element = document.createElement("a");
    const file = new Blob([text], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = fileName.endsWith(".txt") ? fileName : `${fileName}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="app-container">
      <Header 
        currentView={currentView}
        setCurrentView={setCurrentView}
        messages={messages}
        downloadConversation={downloadConversation}
        downloadConversationPDF={() => downloadConversationPDF(messages, selectedFiles)}
        nodesCount={nodes.length}
        webSearch={webSearch}
        setWebSearch={setWebSearch}
        newChat={newChat}
        queryMode={queryMode}
        setQueryMode={setQueryMode}
        hasImage={!!imagePreview}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
      />

      <div className="app-body">
        <Sidebar 
          isOpen={sidebarOpen}
          historyList={historyList}
          currentConversationId={currentConversationId}
          loadConversation={loadConversation}
          deleteHistory={deleteHistory}
          uploadFiles={uploadFiles}
          isUploading={isUploading}
          lastLogs={lastLogs}
          structure={structure}
          selectedFiles={selectedFiles}
          setSelectedFiles={setSelectedFiles}
          handleFileSelect={handleFileSelect}
          handleDelete={handleDelete}
          summaries={summaries}
        />

        <main className="main-content">
          {currentView === 'chat' ? (
            <ChatSection 
              inputRef={inputRef}
              question={question}
              handleInputChange={handleInputChange}
              handleKeyDown={handleKeyDown}
              askQuestion={askQuestion}
              showAutocomplete={showAutocomplete}
              filteredFiles={filteredFiles}
              autocompleteIndex={autocompleteIndex}
              setAutocompleteIndex={setAutocompleteIndex}
              selectFile={selectFile}
              loading={loading}
              messages={messages}
              streamingAnswer={streamingAnswer}
              streamingAnswers={streamingAnswers}
              compareMode={compareMode}
              setCompareMode={setCompareMode}
              selectedModels={selectedModels}
              setSelectedModels={setSelectedModels}
              availableModels={availableModels}
              pinToCanvas={pinToCanvas}
              selectedFiles={selectedFiles}
              setSelectedFiles={setSelectedFiles}
              downloadConversation={downloadConversation}
              downloadConversationPDF={() => downloadConversationPDF(messages, selectedFiles)}
              handleImageChange={handleImageChange}
              imagePreview={imagePreview}
              removeImage={removeImage}
              retryLastQuery={retryLastQuery}
            />
          ) : (
            <KnowledgeCanvas 
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              addStickyNote={addStickyNote}
              exportCanvas={exportCanvas}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;