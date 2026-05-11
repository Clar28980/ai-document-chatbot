# Changelog

All notable changes to the AI Document Chatbot project.

## [2.0.0] - 2024-05-06

### Added
- Multi-document support - upload and manage multiple documents
- Persistent storage - documents saved to disk using pickle
- Document management API endpoints:
  - `GET /documents` - List all uploaded documents
  - `POST /documents/{id}/load` - Switch to a document
  - `DELETE /documents/{id}` - Delete a document
  - `GET /current-document` - Get active document info
- Chat export functionality - export chat history to text file
- Clear chat feature
- File type validation in UI (accepts only PDF/TXT)
- Visual document list in sidebar with icons and timestamps
- Active document indicator (blue highlight)
- Document delete confirmation dialogs
- Better error handling with detailed messages
- Loading spinners during upload
- Chat message timestamps
- User and AI avatars in chat
- Environment configuration support (.env file)
- PowerShell startup script for Windows
- Setup verification test script
- Comprehensive documentation (README, SETUP, CONTRIBUTING)
- MIT License

### Changed
- Completely redesigned UI with better UX
- Backend version bumped to 2.0.0
- Improved error messages throughout
- Chat input disabled when no document loaded
- Better empty states for both chat and document list
- API now returns document metadata on upload

### Fixed
- Temp files now properly cleaned up
- File input resets after successful upload
- Error handling for backend connection issues

## [1.0.0] - 2024-05-06

### Added
- Initial release
- FastAPI backend with LangChain integration
- FAISS vector database for document embeddings
- Claude integration through the Anthropic API
- PDF and TXT file upload support
- Angular 18 frontend
- Tailwind CSS styling
- Real-time chat interface
- Document processing with chunking
- CORS support for frontend communication
- Basic error handling
- Requirements files
- README with setup instructions

### Features
- Upload PDF/TXT documents
- Ask questions about uploaded documents
- View chat history
- Loading indicators
- Responsive design

---

## Assignment Requirements Met

✅ Loads content from PDF/TXT files  
✅ Embeds and stores in local vector database (FAISS)  
✅ Uses LangChain to orchestrate the full pipeline  
✅ Uses Claude through the Anthropic API with `ANTHROPIC_API_KEY`  
✅ Angular UI for user interaction  
✅ Answers user questions about the document  
✅ **Bonus**: Multi-document support, persistent storage, chat export  
✅ **Bonus**: Document management (list, switch, delete)  
✅ **Bonus**: Enhanced UI with timestamps, avatars, empty states  
