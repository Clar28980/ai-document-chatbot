import { ChangeDetectorRef, Component, ElementRef, NgZone, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';

type ChatMessage = {
  sender: 'user' | 'bot' | 'system';
  text: string;
};

type HistoryItem = {
  question: string;
  answer: string;
};

@Component({
  selector: 'app-root',
  imports: [FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  @ViewChild('conversationArea') conversationArea!: ElementRef<HTMLElement>;

  private apiUrl = 'http://127.0.0.1:8000';
  private historyStorageKey = 'clarence_ai_history';

  selectedFile: File | null = null;
  question = '';
  isUploading = false;
  isAsking = false;
  activeDocument = 'No document uploaded yet';

  history: HistoryItem[] = [];
  messages: ChatMessage[] = [];

  constructor(
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {
    this.loadHistory();
  }

  get hasConversation(): boolean {
    return this.messages.length > 0 || this.isAsking;
  }

  private loadHistory() {
    const savedHistory = localStorage.getItem(this.historyStorageKey);

    if (savedHistory) {
      try {
        const parsedHistory = JSON.parse(savedHistory);

        this.history = parsedHistory.map((item: any) => {
          if (typeof item === 'string') {
            return {
              question: item,
              answer: 'No saved answer for this old history item.'
            };
          }

          return {
            question: item.question || '',
            answer: item.answer || 'No saved answer.'
          };
        });
      } catch {
        this.history = [];
      }
    }
  }

  private saveHistory() {
    localStorage.setItem(this.historyStorageKey, JSON.stringify(this.history));
  }

  private addToHistory(question: string, answer: string) {
    this.history = this.history.filter(item => item.question !== question);

    this.history.unshift({
      question,
      answer
    });

    this.saveHistory();
  }

  private updateScreen() {
    this.zone.run(() => {
      this.cdr.detectChanges();
      this.scrollToBottom();
    });
  }

  private scrollToBottom() {
    setTimeout(() => {
      const element = this.conversationArea?.nativeElement;

      if (element) {
        element.scrollTop = element.scrollHeight;
      }
    }, 50);

    setTimeout(() => {
      const element = this.conversationArea?.nativeElement;

      if (element) {
        element.scrollTop = element.scrollHeight;
      }
    }, 250);
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;

    if (input.files && input.files.length > 0) {
      this.selectedFile = input.files[0];
      this.activeDocument = this.selectedFile.name;
      this.updateScreen();
    }
  }

  async uploadDocument() {
    if (!this.selectedFile) {
      this.messages.push({
        sender: 'system',
        text: 'Please choose a PDF or TXT file first.'
      });

      this.updateScreen();
      return;
    }

    this.isUploading = true;

    this.messages.push({
      sender: 'system',
      text: `Uploading and processing ${this.selectedFile.name}...`
    });

    const loadingMessageIndex = this.messages.length - 1;

    this.updateScreen();

    const formData = new FormData();
    formData.append('file', this.selectedFile);

    try {
      const response = await fetch(`${this.apiUrl}/upload`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      this.zone.run(() => {
        if (!response.ok || data.success === false) {
          this.messages[loadingMessageIndex] = {
            sender: 'system',
            text: data.message || 'Upload failed.'
          };
        } else {
          this.messages[loadingMessageIndex] = {
            sender: 'system',
            text: data.message || `${this.selectedFile?.name} uploaded and processed successfully.`
          };
        }

        this.isUploading = false;
        this.updateScreen();
      });
    } catch {
      this.zone.run(() => {
        this.messages[loadingMessageIndex] = {
          sender: 'system',
          text: 'Upload failed. Make sure FastAPI backend is running on http://127.0.0.1:8000.'
        };

        this.isUploading = false;
        this.updateScreen();
      });
    }
  }

  async askQuestion() {
    const cleanQuestion = this.question.trim();

    if (!cleanQuestion || this.isAsking) {
      return;
    }

    // 1. Display user message immediately
    this.messages.push({
      sender: 'user',
      text: cleanQuestion
    });

    // 2. Add temporary bot loading message immediately
    this.messages.push({
      sender: 'bot',
      text: 'Clarence is thinking...'
    });

    const loadingMessageIndex = this.messages.length - 1;

    // 3. Clear input immediately
    this.question = '';

    // 4. Disable send while waiting
    this.isAsking = true;

    // 5. Update UI immediately before backend request
    this.updateScreen();

    const formData = new FormData();
    formData.append('question', cleanQuestion);

    try {
      const response = await fetch(`${this.apiUrl}/ask`, {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      const botAnswer =
        data.answer ||
        data.response ||
        data.message ||
        'I could not find an answer.';

      this.zone.run(() => {
        // 6. Replace loading message with real backend answer
        this.messages[loadingMessageIndex] = {
          sender: 'bot',
          text: botAnswer
        };

        this.addToHistory(cleanQuestion, botAnswer);
        this.isAsking = false;
        this.updateScreen();
      });
    } catch {
      this.zone.run(() => {
        const errorMessage =
          'Something went wrong. Check that the backend is running on http://127.0.0.1:8000.';

        // 7. Replace loading message with error message
        this.messages[loadingMessageIndex] = {
          sender: 'system',
          text: errorMessage
        };

        this.addToHistory(cleanQuestion, errorMessage);
        this.isAsking = false;
        this.updateScreen();
      });
    }
  }

  useHistoryQuestion(item: HistoryItem) {
    this.messages = [
      {
        sender: 'user',
        text: item.question
      },
      {
        sender: 'bot',
        text: item.answer
      }
    ];

    this.question = '';
    this.isAsking = false;
    this.updateScreen();
  }

  clearChat() {
    this.messages = [];
    this.question = '';
    this.isAsking = false;
    this.updateScreen();
  }

  clearHistory() {
    this.history = [];
    localStorage.removeItem(this.historyStorageKey);
    this.updateScreen();
  }

  startPrompt(prompt: string) {
    this.question = prompt;
    this.updateScreen();
  }

  triggerFileInput(fileInput: HTMLInputElement) {
    fileInput.click();
  }
}