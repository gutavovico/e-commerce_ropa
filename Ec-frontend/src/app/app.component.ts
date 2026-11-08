import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { WidgetChatbotComponent } from './modules/catalogo/cu19_asistente_chatbot/componentes/widget-chatbot.component';
import { TenantService } from './core/tenant/tenant.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, WidgetChatbotComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class App {
  title = 'Fashion Store';
  // P2-CU02: se crea al arrancar para seguir la navegación y limpiar la tienda al salir del portal
  private readonly tenant = inject(TenantService);
}
