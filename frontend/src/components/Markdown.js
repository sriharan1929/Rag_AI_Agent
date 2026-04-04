import React from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

const Markdown = ({ children }) => {
  if (!children) return null;

  return (
    <div className="markdown-content">
      <ReactMarkdown 
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          h1: ({node, ...props}) => <h3 style={{ marginTop: '15px', color: '#2d3748' }} {...props} />,
          h2: ({node, ...props}) => <h4 style={{ marginTop: '15px', color: '#2d3748' }} {...props} />,
          h3: ({node, ...props}) => <h5 style={{ marginTop: '15px', color: '#2d3748' }} {...props} />,
          ul: ({node, ...props}) => <ul style={{ marginLeft: '20px', padding: 0 }} {...props} />,
          pre: ({node, ...props}) => (
            <pre 
              className="md-code-block" 
              style={{ background: '#1e1e2e', color: '#cdd6f4', padding: '15px', borderRadius: '5px', overflowX: 'auto', position: 'relative' }} 
              {...props} 
            />
          ),
          code({node, inline, className, children, ...props}) {
            if (inline) {
              return (
                <code 
                  style={{ background: '#edf2f7', color: '#c7254e', padding: '2px 4px', borderRadius: '3px' }} 
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className={className} {...props}>
                {children}
              </code>
            );
          }
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
};

export default Markdown;
