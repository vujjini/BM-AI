import React, { useState, useRef, useEffect } from 'react';
import { Send, MessageCircle, Bot, User, FileText, Loader } from 'lucide-react';
import { apiService, ChatResponse, Source } from '../services/api';
import { PDFViewer } from './PDFViewer';
import './ChatInterface.css';

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  sources?: Source[];
  timestamp: Date;
}

interface ChatInterfaceProps {
  onError: (error: string) => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ onError }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPDF, setSelectedPDF] = useState<{ filename: string; pdfPath: string | null } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await apiService.chat(userMessage.content);
      console.log('Chat response:', response);
      console.log('Sources:', response.sources);
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: response.answer,
        sources: response.sources || [],
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error: any) {
      console.error('Chat error:', error);
      console.error('Error response:', error.response);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to get response';
      onError(errorMessage);
      
      const errorBotMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: 'Sorry, I encountered an error while processing your question. Please try again.',
        timestamp: new Date(),
      };
      
      setMessages(prev => [...prev, errorBotMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const renderMessage = (message: Message) => {
    try {
      return (
        <div key={message.id} className={`message ${message.type}`}>
          <div className="message-avatar">
            {message.type === 'user' ? <User size={20} /> : <Bot size={20} />}
          </div>
          <div className="message-content">
            <div className="message-text">
              {message.content}
            </div>
            {message.sources && message.sources.length > 0 && (
              <div className="message-sources">
                <h4>Sources:</h4>
                <ul>
                  {message.sources
                    .filter((source): source is Source => {
                      return source !== null && 
                             source !== undefined && 
                             typeof source === 'object' &&
                             'filename' in source;
                    })
                    .map((source, index) => {
                      const filename = typeof source.filename === 'string' ? source.filename : 'Unknown';
                      const handleClick = () => {
                        console.log('Source clicked:', source);
                        console.log('Has pdf_path:', source.pdf_path);
                        if (source.pdf_path) {
                          console.log('Opening PDF:', filename, source.pdf_path);
                          setSelectedPDF({ filename: filename, pdfPath: source.pdf_path });
                        } else {
                          console.log('No pdf_path available for:', filename);
                        }
                      };
                      
                      return (
                        <li 
                          key={index}
                          className={source.pdf_path ? 'clickable-source' : ''}
                          onClick={handleClick}
                          style={{ cursor: source.pdf_path ? 'pointer' : 'default' }}
                        >
                          <FileText size={14} />
                          <span>{filename}</span>
                          {!source.pdf_path && <span style={{ fontSize: '11px', color: '#888', marginLeft: '8px' }}>(no preview)</span>}
                        </li>
                      );
                    })}
                </ul>
              </div>
            )}
            <div className="message-timestamp">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        </div>
      );
    } catch (error) {
      console.error('Error rendering message:', error, message);
      return (
        <div key={message.id} className={`message ${message.type}`}>
          <div className="message-content">
            <div className="message-text">
              Error displaying message
            </div>
          </div>
        </div>
      );
    }
  };

  return (
    <>
      {selectedPDF && (
        <PDFViewer
          filename={selectedPDF.filename}
          pdfPath={selectedPDF.pdfPath}
          onClose={() => setSelectedPDF(null)}
        />
      )}
      <div className="chat-interface">
      <div className="chat-header">
        <MessageCircle size={24} />
        <h2>Building Manager Assistant</h2>
        <p>Ask questions about your uploaded documents</p>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <Bot size={48} />
            <h3>Welcome to Building Manager Assistant</h3>
            <p>Upload some documents first, then ask me questions about building management, maintenance, or any content from your files.</p>
            <div className="example-questions">
              <h4>Example questions:</h4>
              <ul>
                <li>"What are the maintenance schedules?"</li>
                <li>"Show me the budget breakdown"</li>
                <li>"What safety protocols are mentioned?"</li>
                <li>"Summarize the key findings"</li>
              </ul>
            </div>
          </div>
        )}
        
        {messages.map(renderMessage)}
        
        {isLoading && (
          <div className="message bot loading">
            <div className="message-avatar">
              <Bot size={20} />
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <Loader className="spinner" size={16} />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="input-container">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask a question about your documents..."
            disabled={isLoading}
            className="chat-input"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="send-button"
          >
            <Send size={20} />
          </button>
        </div>
      </form>
    </div>
    </>
  );
};
