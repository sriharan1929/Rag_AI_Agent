import { jsPDF } from "jspdf";

export const downloadConversationPDF = (messages, selectedFiles) => {
  if (!messages || messages.length === 0) {
    alert("No conversation to download.");
    return;
  }

  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 20;
  const maxLineWidth = pageWidth - margin * 2;
  let y = 20;

  // Header
  doc.setFontSize(18);
  doc.setTextColor(99, 102, 241); 
  doc.text("ZIP-RAG AI Chat Conversation", margin, y);
  y += 10;
  
  doc.setFontSize(10);
  doc.setTextColor(100, 116, 139); 
  doc.text(`Generated on: ${new Date().toLocaleString()}`, margin, y);
  y += 15;

  messages.forEach((msg) => {
    const isUser = msg.role === 'user';
    
    // Check for page overflow before starting a new message
    if (y > 270) {
      doc.addPage();
      y = 20;
    }

    // Role Header
    doc.setFontSize(11);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(isUser ? 31 : 99, isUser ? 41 : 102, isUser ? 59 : 241);
    doc.text(isUser ? "YOU" : "AI", margin, y);
    y += 6;

    // Message Content
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(30, 41, 59);

    let content = msg.content || "";
    if (msg.isComparative && msg.responses) {
      content = msg.responses.map(r => `[${r.model}]\n${r.content}`).join("\n\n");
    }
      
    const lines = doc.splitTextToSize(content, maxLineWidth);
    
    lines.forEach(line => {
      if (y > 280) {
        doc.addPage();
        y = 20;
      }
      doc.text(line, margin, y);
      y += 5;
    });

    if (msg.source) {
      if (y > 280) {
        doc.addPage();
        y = 20;
      }
      doc.setFontSize(8);
      doc.setTextColor(148, 163, 184);
      doc.text(`Source: ${msg.source}`, margin, y);
      y += 6;
    }

    y += 10; // Spacing between messages
  });

  // Filename logic
  const dateStr = new Date().toISOString().split('T')[0];
  let baseName = "conversation";
  if (selectedFiles && selectedFiles.length > 0) {
    const firstFile = selectedFiles[0].split('/').pop();
    const nameWithoutExt = firstFile.substring(0, firstFile.lastIndexOf('.')) || firstFile;
    baseName = nameWithoutExt;
  }
  
  const defaultName = `${baseName}[${dateStr}]_chat`;
  const fileName = prompt("💾 Save your AI chat conversation as a PDF:", defaultName);
  if (!fileName) return;

  doc.save(fileName.endsWith(".pdf") ? fileName : `${fileName}.pdf`);
};
