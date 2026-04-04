import { useCallback } from 'react';
import { useNodesState, useEdgesState, addEdge } from '@xyflow/react';
import { toPng } from 'html-to-image';

export const useKnowledgeCanvas = (selectedFiles) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const onStickyNoteChange = useCallback((id, text) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === id) {
          return { ...node, data: { ...node.data, text } };
        }
        return node;
      })
    );
  }, [setNodes]);

  const addStickyNote = useCallback(() => {
    const id = `sticky_${Date.now()}`;
    const newNode = {
      id,
      type: 'stickyNote',
      position: { x: 100, y: 100 },
      data: { text: '', onChange: onStickyNoteChange },
    };
    setNodes((nds) => nds.concat(newNode));
  }, [onStickyNoteChange, setNodes]);

  const pinToCanvas = (content, source) => {
    const id = `node_${Date.now()}`;
    const newNode = {
      id,
      type: 'aiAnswer',
      position: { x: Math.random() * 400, y: Math.random() * 400 },
      data: { content, source },
    };
    setNodes((nds) => nds.concat(newNode));
    alert("Pinned to Canvas! Check the Canvas tab.");
  };

  const exportCanvas = useCallback(() => {
    const element = document.querySelector('.react-flow__viewport');
    if (!element) return;
    
    const dateStr = new Date().toISOString().split('T')[0];
    
    let baseName = "knowledge-canvas";
    if (selectedFiles && selectedFiles.length > 0) {
      const firstFile = selectedFiles[0].split('/').pop();
      const nameWithoutExt = firstFile.substring(0, firstFile.lastIndexOf('.')) || firstFile;
      baseName = nameWithoutExt;
    }
    
    const defaultName = `${baseName}[${dateStr}]`;
    const fileName = prompt("💾 Save your Knowledge Canvas as an image (PNG):", defaultName);
    
    if (!fileName) return;
    
    toPng(element, { backgroundColor: '#f1f5f9' })
      .then((dataUrl) => {
        const link = document.createElement('a');
        link.download = fileName.endsWith(".png") ? fileName : `${fileName}.png`;
        link.href = dataUrl;
        link.click();
      })
      .catch((err) => {
        console.error('Export failed:', err);
      });
  }, [selectedFiles]);

  return {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    addStickyNote,
    pinToCanvas,
    exportCanvas
  };
};
