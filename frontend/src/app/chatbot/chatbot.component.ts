import { Component, ElementRef, ViewChild, AfterViewChecked, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../api.service';
import { CandidateProfile } from '../models';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  candidates?: CandidateProfile[];  // bot messages can carry candidate cards
}

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css']
})
export class ChatbotComponent implements AfterViewChecked {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;
  @Output() candidateSelected = new EventEmitter<CandidateProfile>();

  messages: ChatMessage[] = [
    {
      role: 'assistant',
      content: "👋 Hi! I'm **SearchBot**, your AI recruitment assistant.\n\nI use the same AI ranking engine as the Intelligent Search. Just ask me naturally:\n\n• *\"Find me a Python developer with 2 years experience\"*\n• *\"Who are the best React candidates?\"*\n• *\"Show me full stack developers\"*",
      timestamp: new Date()
    }
  ];

  inputText = '';
  isThinking = false;
  private shouldScroll = false;

  constructor(private api: ApiService) {}

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  private scrollToBottom(): void {
    try {
      const el = this.messagesContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    } catch (_) {}
  }

  sendMessage(): void {
    const text = this.inputText.trim();
    if (!text || this.isThinking) return;

    this.messages.push({ role: 'user', content: text, timestamp: new Date() });
    this.inputText = '';
    this.isThinking = true;
    this.shouldScroll = true;

    // Build conversation history (text only — no candidate arrays)
    const history = this.messages.map(m => ({ role: m.role, content: m.content }));

    this.api.sendChatMessage(history).subscribe({
      next: (res) => {
        this.messages.push({
          role: 'assistant',
          content: res.reply,
          candidates: res.candidates || [],
          timestamp: new Date()
        });
        this.isThinking = false;
        this.shouldScroll = true;
      },
      error: () => {
        this.messages.push({
          role: 'assistant',
          content: '⚠️ Sorry, I could not reach the AI server. Please make sure the backend is running and try again.',
          timestamp: new Date()
        });
        this.isThinking = false;
        this.shouldScroll = true;
      }
    });
  }

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  clearChat(): void {
    this.messages = [this.messages[0]];
  }

  openCandidate(candidate: CandidateProfile): void {
    this.candidateSelected.emit(candidate);
  }

  formatContent(content: string): string {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  }

  getInitial(name: string): string {
    return name ? name.charAt(0).toUpperCase() : '?';
  }
}
