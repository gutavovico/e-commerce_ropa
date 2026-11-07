import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { WidgetChatbotComponent } from './modules/catalogo/cu19_asistente_chatbot/componentes/widget-chatbot.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, WidgetChatbotComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class App {
  title = 'Fashion Store';
}
