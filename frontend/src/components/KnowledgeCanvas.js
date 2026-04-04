import React, { useCallback, useMemo } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import Markdown from './Markdown';

// --- Custom Node: AI Answer ---
const AIAnswerNode = ({ data }) => {
  return (
    <div className="node-ai-answer shadow-md">
      {/* Top Handle: both source and target overlaying */}
      <Handle type="target" position={Position.Top} id="t-t" />
      <Handle type="source" position={Position.Top} id="t-s" />
      
      <div className="node-header">
        <span>🤖 AI Answer</span>
        {data.source && <span style={{ opacity: 0.6, fontSize: '0.65rem' }}>{data.source}</span>}
      </div>
      <div className="node-content">
        <Markdown>{data.content}</Markdown>
      </div>
      
      {/* Bottom Handle: both source and target overlaying */}
      <Handle type="target" position={Position.Bottom} id="b-t" />
      <Handle type="source" position={Position.Bottom} id="b-s" />
    </div>
  );
};

// --- Custom Node: Sticky Note ---
const StickyNoteNode = ({ data, id }) => {
  const onChange = (evt) => {
    data.onChange(id, evt.target.value);
  };

  return (
    <div className="node-sticky">
      {/* Top Handle: both source and target overlaying */}
      <Handle type="target" position={Position.Top} id="st-t" />
      <Handle type="source" position={Position.Top} id="st-s" />
      
      <textarea 
        className="nodrag" 
        value={data.text} 
        onChange={onChange} 
        placeholder="Type a note..."
      />
      
      {/* Bottom Handle: both source and target overlaying */}
      <Handle type="target" position={Position.Bottom} id="sb-t" />
      <Handle type="source" position={Position.Bottom} id="sb-s" />
    </div>
  );
};

// --- Node Types Definition ---
const nodeTypes = {
  aiAnswer: AIAnswerNode,
  stickyNote: StickyNoteNode,
};

const KnowledgeCanvas = ({ 
  nodes, 
  edges, 
  onNodesChange, 
  onEdgesChange, 
  onConnect,
  addStickyNote,
  exportCanvas,
}) => {
  return (
    <div className="canvas-container" style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#cbd5e1" variant="dots" gap={20} size={1} />
        <Controls />
        <MiniMap zoomable pannable />
        
        <Panel position="top-center">
          <div className="canvas-toolbar">
            <button onClick={addStickyNote}>
              <span>📝</span> Add Note
            </button>
            <div className="divider" />
            <button onClick={exportCanvas}>
              <span>🖼️</span> Export Image
            </button>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
};

export default KnowledgeCanvas;
