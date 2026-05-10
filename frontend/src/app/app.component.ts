import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { environment } from '../environments/environment';

interface DocumentInfo {
  id: string;
  filename: string;
  uploaded_at: string;
  chunks: number;
}

interface ChatMessage {
  role: string;
  text: string;
  timestamp?: string;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, HttpClientModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  http = inject(HttpClient);
  
  selectedFile: File | null = null;
  uploadMessage = '';
  uploadProgress = false;
  
  question = '';
  chatHistory: ChatMessage[] = [];
  isLoading = false;
  
  documents: DocumentInfo[] = [];
  currentDocument: DocumentInfo | null = null;
  showDocumentList = false;

  ngOnInit() {
    this.loadDocuments();
    this.loadCurrentDocument();
  }

  // Load all documents
  loadDocuments() {
    this.http.get<DocumentInfo[]>(`${environment.apiUrl}/documents`).subscribe({
      next: (docs) => this.documents = docs,
      error: (err) => console.error('Error loading documents:', err)
    });
  }

  // Load currently active document
  loadCurrentDocument() {
    this.http.get<DocumentInfo | {message: string}>(`${environment.apiUrl}/current-document`).subscribe({
      next: (doc: any) => {
        if (doc.id) {
          this.currentDocument = doc;
        }
      },
      error: (err) => console.error('Error loading current document:', err)
    });
  }

  // Switch to a different document
  switchDocument(docId: string) {
    this.http.post(`${environment.apiUrl}/documents/${docId}/load`, {}).subscribe({
      next: (res: any) => {
        this.currentDocument = res.document;
        this.uploadMessage = `Loaded: ${res.document.filename}`;
        this.chatHistory = []; // Clear chat when switching documents
      },
      error: (err) => {
        this.uploadMessage = 'Error loading document';
        console.error(err);
      }
    });
  }

  // Delete a document
  deleteDocument(docId: string, event: Event) {
    event.stopPropagation();
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    this.http.delete(`${environment.apiUrl}/documents/${docId}`).subscribe({
      next: () => {
        this.documents = this.documents.filter(d => d.id !== docId);
        if (this.currentDocument?.id === docId) {
          this.currentDocument = null;
          this.chatHistory = [];
        }
        this.uploadMessage = 'Document deleted';
      },
      error: (err) => {
        this.uploadMessage = 'Error deleting document';
        console.error(err);
      }
    });
  }

  // Kapag pumili ng file sa sidebar
  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
    this.uploadMessage = this.selectedFile ? `Selected: ${this.selectedFile.name}` : '';
  }

  // Kapag kinlick ang Upload button
  uploadDocument() {
    if (!this.selectedFile) return;
    
    const formData = new FormData();
    formData.append('file', this.selectedFile);
    
    this.uploadProgress = true;
    this.uploadMessage = 'Uploading and processing...';
    
    this.http.post<any>(`${environment.apiUrl}/upload`, formData).subscribe({
      next: (res) => {
        this.uploadMessage = res.message;
        this.currentDocument = res.document;
        this.documents.unshift(res.document);
        this.selectedFile = null;
        this.uploadProgress = false;
        // Reset file input
        const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
      },
      error: (err) => {
        this.uploadMessage = err.error?.detail || 'Error uploading file';
        this.uploadProgress = false;
      }
    });
  }

  // Clear chat history
  clearChat() {
    if (this.chatHistory.length === 0) return;
    if (confirm('Clear all chat messages?')) {
      this.chatHistory = [];
    }
  }

  // Export chat to text file
  exportChat() {
    if (this.chatHistory.length === 0) return;
    
    const content = this.chatHistory.map(msg => 
      `[${msg.role.toUpperCase()}] ${msg.text}`
    ).join('\n\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_export_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }

  // Kapag nag-send ng tanong sa chatbot
  askQuestion() {
    if (!this.question.trim()) return;
    if (!this.currentDocument) {
      this.uploadMessage = 'Please upload a document first!';
      return;
    }
    
    // Ilagay ang tanong ng user sa chat history
    this.chatHistory.push({ 
      role: 'user', 
      text: this.question,
      timestamp: new Date().toISOString()
    });
    const currentQuestion = this.question;
    this.question = ''; 
    this.isLoading = true;
    
    // Ipadala sa Python backend
    this.http.post<any>(`${environment.apiUrl}/ask`, { question: currentQuestion }).subscribe({
      next: (res) => {
        this.chatHistory.push({ 
          role: 'ai', 
          text: res.answer,
          timestamp: new Date().toISOString()
        });
        this.isLoading = false;
        this.uploadMessage = ''; // Clear any error messages
      },
      error: (err) => {
        const errorMsg = err.error?.detail || 'Sorry, cannot connect to AI. Please check if the backend is running.';
        this.chatHistory.push({ 
          role: 'ai', 
          text: errorMsg,
          timestamp: new Date().toISOString()
        });
        this.isLoading = false;
      }
    });
  }

  // Get file icon based on extension
  getFileIcon(filename: string): string {
    return filename.toLowerCase().endsWith('.pdf') ? '📄' : '📝';
  }

  // Format date
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleString();
  }
}