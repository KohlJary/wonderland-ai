import React from 'react'
import ReactMarkdown from 'react-markdown'

interface NotePreviewProps {
  markdown: string
}

export default function NotePreview({ markdown }: NotePreviewProps) {
  return (
    <div>
      <ReactMarkdown
        components={{
          img: ({ node, ...props }) => (
            <img style={{ maxWidth: '100%' }} {...props} />
          ),
          code: ({ node, inline, ...props }) =>
            inline ? (
              <code style={{
                backgroundColor: '#f4f4f4',
                padding: '2px 6px',
                borderRadius: '3px',
                fontFamily: "'Courier New', monospace",
                fontSize: '0.9em',
              }} {...props} />
            ) : (
              <code style={{
                backgroundColor: '#f4f4f4',
                padding: '2px 6px',
                borderRadius: '3px',
                fontFamily: "'Courier New', monospace",
              }} {...props} />
            ),
          pre: ({ node, ...props }) => (
            <pre style={{
              backgroundColor: '#f5f5f5',
              border: '1px solid #ddd',
              borderRadius: '4px',
              padding: '12px',
              overflowX: 'auto',
              margin: '1em 0',
            }} {...props} />
          ),
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  )
}
