import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { animate, style, transition, trigger } from '@angular/animations';

@Component({
  selector: 'app-past-searches-log',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './past-searches-log.component.html',
  styleUrl: './past-searches-log.component.css',
  animations: [
    trigger('slideIn', [
      transition(':enter', [
        style({ transform: 'translateX(-20px)', opacity: 0 }),
        animate('400ms ease-out', style({ transform: 'translateX(0)', opacity: 1 }))
      ])
    ])
  ]
})
export class PastSearchesLogComponent {
  @Input() chatSessions: any[] = [];
  @Input() isLoadingHistory = false;

  @Output() refreshHistory = new EventEmitter<void>();
  @Output() viewSession = new EventEmitter<any>();
  @Output() deleteSession = new EventEmitter<string>();
  @Output() clearAll = new EventEmitter<void>();
  @Output() navigateToChatbot = new EventEmitter<void>();
}
