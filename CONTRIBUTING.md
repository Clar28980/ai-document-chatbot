# Contributing to AI Document Chatbot

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/ai-document-chatbot.git
   cd ai-document-chatbot
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   # OR: source venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

## Running in Development Mode

**Backend:**
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
ng serve
```

## Code Style

### Python (Backend)
- Follow PEP 8
- Use type hints where possible
- Add docstrings for functions
- Run `black` for formatting (if available)

### TypeScript (Frontend)
- Follow Angular style guide
- Use strict TypeScript mode
- Follow existing code patterns
- Use meaningful variable names

## Testing

Before submitting changes:
1. Test file upload with PDF and TXT files
2. Test asking questions about uploaded documents
3. Test document switching functionality
4. Verify error messages display correctly

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Test thoroughly
4. Commit with clear messages
5. Push to your fork
6. Create a Pull Request

## Reporting Issues

When reporting bugs, please include:
- Operating system and version
- Python and Node.js versions
- Steps to reproduce
- Expected vs actual behavior
- Error messages (if any)

## Feature Requests

We welcome feature requests! Please describe:
- The feature you'd like to see
- Why it would be useful
- Any implementation ideas you have

## Questions?

Feel free to open an issue for any questions about contributing.
