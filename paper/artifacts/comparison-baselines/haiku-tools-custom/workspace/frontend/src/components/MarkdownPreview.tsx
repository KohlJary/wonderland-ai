import ReactMarkdown from 'react-markdown';
import RemarkGfm from 'remark-gfm';
import './MarkdownPreview.css';

interface MarkdownPreviewProps {
  markdown: string;
}

export default function MarkdownPreview({ markdown }: MarkdownPreviewProps) {
  return (
    <div className="markdown-preview">
      {markdown ? (
        <ReactMarkdown remarkPlugins={[RemarkGfm]}>
          {markdown}
        </ReactMarkdown>
      ) : (
        <p className="empty-preview">Preview will appear here...</p>
      )}
    </div>
  );
}
