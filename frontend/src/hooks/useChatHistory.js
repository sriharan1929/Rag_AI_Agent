import { useState, useCallback, useEffect } from "react";
import axios from "axios";

export const useChatHistory = ({
  API_URL,
  setMessages,
  setCurrentView,
  setStreamingAnswer,
  setStreamingAnswers,
  setTopic,
  setIsRelevant,
  removeImage
}) => {
  const [historyList, setHistoryList] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/history/list/`);
      setHistoryList(res.data || []);
    } catch (error) {
      console.error("Error fetching history:", error);
    }
  }, [API_URL]);

  const saveConversation = async (msgs) => {
    if (!msgs || msgs.length === 0) return;
    try {
      const res = await axios.post(`${API_URL}/history/save/`, { 
        messages: msgs,
        filename: currentConversationId
      });
      if (res.data.filename && !currentConversationId) {
        setCurrentConversationId(res.data.filename);
      }
      fetchHistory();
    } catch (error) {
      console.error("Error saving conversation:", error);
    }
  };

  const loadConversation = async (filename) => {
    try {
      const res = await axios.get(`${API_URL}/history/load/${filename}/`);
      setMessages(res.data.messages || []);
      setCurrentConversationId(filename);
      setCurrentView("chat");
    } catch (error) {
      console.error("Error loading conversation:", error);
      alert("Failed to load conversation.");
    }
  };

  const newChat = () => {
    setMessages([]);
    setStreamingAnswer("");
    setStreamingAnswers({});
    setCurrentConversationId(null);
    setTopic("");
    setIsRelevant(true);
    if (removeImage) removeImage();
  };

  const deleteHistory = async (filename) => {
    if (!window.confirm("Are you sure you want to delete this conversation?")) return;
    try {
      await axios.delete(`${API_URL}/history/delete/${filename}/`);
      if (currentConversationId === filename) {
        newChat();
      }
      fetchHistory();
    } catch (error) {
      console.error("Error deleting history:", error);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return {
    historyList,
    currentConversationId,
    fetchHistory,
    saveConversation,
    loadConversation,
    deleteHistory,
    newChat
  };
};
