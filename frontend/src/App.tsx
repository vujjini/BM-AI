import React, { useState, useEffect } from 'react';
import { Building, Wifi, WifiOff } from 'lucide-react';
import { FileUpload } from './components/FileUpload';
import { ChatInterface } from './components/ChatInterface';
import { Notification } from './components/Notification';
import { apiService } from './services/api';
import './App.css';

interface NotificationState {
  type: 'success' | 'error';
  message: string;
  id: string;
}

function App() {
  const [notifications, setNotifications] = useState<NotificationState[]>([]);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean | null>(null);

  useEffect(() => {
    checkBackendConnection();
    const interval = setInterval(checkBackendConnection, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const checkBackendConnection = async () => {
    try {
      await apiService.healthCheck();
      setIsBackendConnected(true);
    } catch (error) {
      setIsBackendConnected(false);
    }
  };

  const addNotification = (type: 'success' | 'error', message: string) => {
    const id = Date.now().toString();
    setNotifications(prev => [...prev, { type, message, id }]);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const handleUploadSuccess = (message: string) => {
    addNotification('success', message);
  };

  const handleUploadError = (error: string) => {
    addNotification('error', `Upload failed: ${error}`);
  };

  const handleChatError = (error: string) => {
    addNotification('error', `Chat error: ${error}`);
  };

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <Building size={32} />
            <div>
              <h1>Building Manager Assistant</h1>
              <p>AI-powered document analysis and chat</p>
            </div>
          </div>
          <div className="connection-status">
            {isBackendConnected === null ? (
              <div className="status-indicator checking">
                <Wifi size={16} />
                <span>Checking...</span>
              </div>
            ) : isBackendConnected ? (
              <div className="status-indicator connected">
                <Wifi size={16} />
                <span>Connected</span>
              </div>
            ) : (
              <div className="status-indicator disconnected">
                <WifiOff size={16} />
                <span>Disconnected</span>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="container">
          <div className="upload-section">
            <h2>Upload Documents</h2>
            <p>Upload PDF or Excel files to analyze building management data</p>
            <FileUpload
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          </div>

          <div className="chat-section">
            <h2>Ask Questions</h2>
            <p>Chat with your documents using natural language</p>
            <ChatInterface onError={handleChatError} />
          </div>
        </div>
      </main>

      {/* Notifications */}
      <div className="notifications-container">
        {notifications.map(notification => (
          <Notification
            key={notification.id}
            type={notification.type}
            message={notification.message}
            onClose={() => removeNotification(notification.id)}
          />
        ))}
      </div>
    </div>
  );
}

export default App;
