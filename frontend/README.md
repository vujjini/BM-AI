# Building Manager Assistant - Frontend

A modern, intuitive React.js frontend for the Building Manager RAG Chatbot system. This application provides a user-friendly interface for uploading building management documents and chatting with an AI assistant powered by your document data.

## Features

### 🔄 File Upload System
- **Single File Upload**: Upload individual PDF or Excel files
- **Multiple Files Upload**: Upload multiple files at once
- **ZIP Folder Upload**: Upload and process ZIP archives containing multiple documents
- **Drag & Drop Interface**: Intuitive drag-and-drop functionality
- **Real-time Progress**: Visual feedback during file processing
- **Detailed Results**: View processing statistics and file-by-file results

### 💬 AI Chat Interface
- **Natural Language Queries**: Ask questions in plain English
- **Source Attribution**: See which documents the AI used to answer your questions
- **Real-time Responses**: Fast, streaming-like chat experience
- **Message History**: Keep track of your conversation
- **Example Prompts**: Helpful suggestions to get started

### 🎨 Modern UI/UX
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Real-time Status**: Backend connection monitoring
- **Toast Notifications**: Success and error feedback
- **Professional Styling**: Clean, modern interface with smooth animations
- **Accessibility**: Built with accessibility best practices

## Technology Stack

- **React 18** with TypeScript
- **Axios** for API communication
- **React Dropzone** for file uploads
- **Lucide React** for icons
- **CSS3** with modern styling and animations

## Getting Started

### Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

### Backend Integration

The frontend is configured to work with the FastAPI backend running on `http://localhost:8000`. Make sure your backend is running before using the frontend.

**Backend Endpoints Used:**
- `POST /api/upload` - Single file upload
- `POST /api/upload_folder` - Multiple files upload
- `POST /api/upload_zip_folder` - ZIP file upload
- `POST /api/chat` - Chat with AI assistant
- `GET /api/health` - Health check

## Usage Guide

### 1. Upload Documents

1. **Choose Upload Mode**:
   - **Single File**: Upload one PDF or Excel file
   - **Multiple Files**: Upload several files at once
   - **ZIP Folder**: Upload a ZIP archive

2. **Upload Files**:
   - Drag and drop files onto the upload area, or
   - Click to browse and select files

3. **View Results**:
   - See processing statistics
   - Review file-by-file results
   - Check for any processing errors

### 2. Chat with Your Documents

1. **Ask Questions**: Type natural language questions about your uploaded documents
2. **Review Answers**: Get AI-powered responses with source attribution
3. **Follow Up**: Continue the conversation with follow-up questions

**Example Questions:**
- "What are the maintenance schedules?"
- "Show me the budget breakdown"
- "What safety protocols are mentioned?"
- "Summarize the key findings"

## File Support

**Supported Formats:**
- PDF files (`.pdf`)
- Excel files (`.xlsx`, `.xls`)
- ZIP archives containing PDF/Excel files (`.zip`)

**File Size Limits:**
- Individual files: As configured in backend
- ZIP archives: As configured in backend

## Development

### Available Scripts

- `npm start` - Start development server
- `npm test` - Run tests
- `npm run build` - Build for production
- `npm run eject` - Eject from Create React App (irreversible)

### Project Structure

```
src/
├── components/          # React components
│   ├── FileUpload.tsx   # File upload component
│   ├── ChatInterface.tsx # Chat interface component
│   └── Notification.tsx  # Toast notification component
├── services/            # API services
│   └── api.ts          # Backend API integration
├── App.tsx             # Main application component
├── App.css             # Global styles
└── index.tsx           # Application entry point
```

### Customization

**API Configuration:**
Update the API base URL in `src/services/api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:8000/api';
```

**Styling:**
Modify CSS files in the `src/components/` directory to customize the appearance.

## Troubleshooting

### Common Issues

1. **Backend Connection Failed**
   - Ensure the backend is running on `http://localhost:8000`
   - Check CORS configuration in the backend
   - Verify network connectivity

2. **File Upload Errors**
   - Check file format (PDF, Excel, ZIP only)
   - Verify file size limits
   - Ensure backend has proper file handling

3. **Chat Not Working**
   - Upload documents first
   - Check backend logs for processing errors
   - Verify vector store is properly configured

### Development Issues

1. **Dependencies**
   ```bash
   npm install  # Reinstall dependencies
   ```

2. **Clear Cache**
   ```bash
   npm start -- --reset-cache
   ```

## Contributing

When contributing to this project:

1. Follow TypeScript best practices
2. Maintain consistent styling
3. Add proper error handling
4. Update documentation as needed
5. Test on multiple browsers and devices

## License

This project is part of the Building Manager RAG Chatbot system.
