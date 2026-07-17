import { Component, ElementRef, ViewChild, AfterViewChecked, Output, EventEmitter, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/api.service';
import { CandidateProfile } from '../../core/models';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  candidates?: CandidateProfile[];
}

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css']
})
export class ChatbotComponent implements AfterViewChecked, OnChanges {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;
  @Output() candidateSelected = new EventEmitter<CandidateProfile>();

  @Input() sessionId: string | null = null;
  @Input() userEmail: string = '';
  @Output() sessionCreated = new EventEmitter<string>();

  messages: ChatMessage[] = [];
  inputText = '';
  isThinking = false;
  private shouldScroll = false;

  constructor(private api: ApiService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['sessionId']) {
      const newSessionId = changes['sessionId'].currentValue;
      if (newSessionId) {
        this.loadSession(newSessionId);
      } else {
        this.messages = [];
      }
    }
  }

  loadSession(sessionId: string): void {
    this.isThinking = true;
    this.api.getChatSession(sessionId).subscribe({
      next: (session) => {
        this.messages = (session.messages || []).map((m: any) => ({
          role: m.role,
          content: m.content,
          candidates: m.candidates,
          timestamp: m.timestamp ? new Date(m.timestamp) : new Date()
        }));
        this.isThinking = false;
        this.shouldScroll = true;
      },
      error: (err) => {
        console.error('Failed to load session:', err);
        this.isThinking = false;
      }
    });
  }

  selectSuggestion(prompt: string): void {
    this.inputText = prompt;
    this.sendMessage();
  }

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

    this.api.sendChatMessage(this.sessionId, this.userEmail, text).subscribe({
      next: (res) => {
        const wasNewSession = !this.sessionId;
        this.sessionId = res.session_id;

        this.messages.push({
          role: 'assistant',
          content: res.reply,
          candidates: res.candidates || [],
          timestamp: new Date()
        });

        this.isThinking = false;
        this.shouldScroll = true;

        if (wasNewSession) {
          this.sessionCreated.emit(res.session_id);
        }
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
    this.messages = [];
    this.sessionId = null;
    this.sessionCreated.emit('');
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

  downloadResume(candidate: CandidateProfile): void {
    if (candidate && candidate.id) {
      this.api.downloadResumePdf(candidate.id);
    }
  }

  getInitial(name: string): string {
    return name ? name.charAt(0).toUpperCase() : '?';
  }
}
