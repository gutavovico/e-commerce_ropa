import {
  Component,
  ElementRef,
  ViewChild,
  effect,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ChatbotService } from '../servicios/chatbot.service';

@Component({
  selector: 'app-widget-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './widget-chatbot.component.html',
  styleUrls: ['./widget-chatbot.component.scss'],
})
export class WidgetChatbotComponent {
  readonly chatbotService = inject(ChatbotService);
  private readonly router = inject(Router);

  @ViewChild('scrollContainer') private scrollContainer?: ElementRef<HTMLDivElement>;

  readonly nuevoMensaje = signal<string>('');

  constructor() {
    // Scroll automático al llegar mensajes nuevos
    effect(() => {
      // Registrar dependencia reactiva sobre mensajes
      this.chatbotService.mensajes();
      setTimeout(() => this.scrollAlFondo(), 100);
    });
  }

  scrollAlFondo(): void {
    if (this.scrollContainer?.nativeElement) {
      this.scrollContainer.nativeElement.scrollTop =
        this.scrollContainer.nativeElement.scrollHeight;
    }
  }

  enviar(): void {
    const texto = this.nuevoMensaje().trim();
    if (!texto) {
      return;
    }
    this.chatbotService.enviarMensaje(texto);
    this.nuevoMensaje.set('');
  }

  seleccionarSugerencia(sugerencia: string): void {
    this.chatbotService.enviarMensaje(sugerencia);
  }

  irAProducto(idProducto: number): void {
    this.router.navigate(['/productos', idProducto]);
  }
}

