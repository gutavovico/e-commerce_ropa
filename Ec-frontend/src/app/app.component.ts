import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { HealthService, HealthResponse } from './health.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class App implements OnInit {
  private readonly healthService = inject(HealthService);

  readonly title = signal('E-Commerce Architecture');
  readonly healthData = signal<HealthResponse | null>(null);
  readonly isLoading = signal<boolean>(true);
  readonly errorMessage = signal<string | null>(null);
  readonly lastChecked = signal<string>('');

  ngOnInit(): void {
    this.checkBackendHealth();
  }

  checkBackendHealth(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.healthService.getHealth().subscribe({
      next: (response) => {
        this.healthData.set(response);
        this.isLoading.set(false);
        this.lastChecked.set(new Date().toLocaleTimeString());
      },
      error: (err) => {
        console.error('Error al conectar con el backend:', err);
        this.healthData.set(null);
        this.isLoading.set(false);
        this.errorMessage.set(
          err.message || 'No se pudo contactar el backend. Verifica que FastAPI esté ejecutándose en el puerto 8000.'
        );
        this.lastChecked.set(new Date().toLocaleTimeString());
      }
    });
  }
}
