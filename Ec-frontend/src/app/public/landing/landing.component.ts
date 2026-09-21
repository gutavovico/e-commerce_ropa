import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule, ViewportScroller } from '@angular/common';
import { Router, RouterLink } from '@angular/router';

export interface PrendaDemo {
  id: string;
  categoria: string;
  nombre: string;
  tejido: string;
  holguraHombros: string;
  porcentajeHombros: number;
  caidaCadera: string;
  porcentajeCadera: number;
  ajusteOptimo: string;
  descripcionVisual: string;
  tensionFijacion: string;
  imagenPreview: string;
}

export interface SucursalFlagship {
  id: string;
  categoria: string;
  nombre: string;
  direccion: string;
  horario: string;
  serviciosEspeciales: string;
  estado: string;
  esPrincipal: boolean;
}

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LandingPageComponent {
  private readonly scroller = inject(ViewportScroller);
  private readonly router = inject(Router);

  // Prenda seleccionada en el vestidor 3D
  protected readonly prendasDemo: PrendaDemo[] = [
    {
      id: 'sastreria',
      categoria: 'SASTRERÍA',
      nombre: 'Blazer Lana Camel',
      tejido: 'Lana Super 150s',
      holguraHombros: 'Holgura exacta (0.5 cm)',
      porcentajeHombros: 94,
      caidaCadera: 'Caída fluida natural',
      porcentajeCadera: 98,
      ajusteOptimo: '98.4%',
      descripcionVisual: 'Conformidad de busto: exacto · Pliegue según torsión',
      tensionFijacion: '0.12 N/mm',
      imagenPreview: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?q=80&w=800&auto=format&fit=crop',
    },
    {
      id: 'noche',
      categoria: 'NOCHE',
      nombre: 'Vestido Plisado',
      tejido: 'Seda de Morera',
      holguraHombros: 'Drapeado dinámico (0.2 cm)',
      porcentajeHombros: 97,
      caidaCadera: 'Caída ondulada simétrica',
      porcentajeCadera: 99,
      ajusteOptimo: '99.1%',
      descripcionVisual: 'Ajuste de escote: micrométrico · Caída ingrávida de seda',
      tensionFijacion: '0.08 N/mm',
      imagenPreview: 'https://images.unsplash.com/photo-1539109136881-3be0616acf4b?q=80&w=800&auto=format&fit=crop',
    },
    {
      id: 'atelier',
      categoria: 'ATELIER',
      nombre: 'Pantalón Palazzo',
      tejido: 'Cashmere Puro',
      holguraHombros: 'Cintura ceñida anatómica',
      porcentajeHombros: 96,
      caidaCadera: 'Vuelo recto de alta densidad',
      porcentajeCadera: 95,
      ajusteOptimo: '97.8%',
      descripcionVisual: 'Longitud de pernera: milimétrica · Línea vertical perfecta',
      tensionFijacion: '0.15 N/mm',
      imagenPreview: 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?q=80&w=800&auto=format&fit=crop',
    },
  ];

  protected readonly prendaSeleccionadaId = signal<string>('sastreria');
  protected readonly modo3DActivo = signal<string>('360');

  protected readonly prendaActiva = computed(() => {
    const id = this.prendaSeleccionadaId();
    return this.prendasDemo.find((p) => p.id === id) ?? this.prendasDemo[0];
  });

  // Sucursales Flagship
  protected readonly sucursales: SucursalFlagship[] = [
    {
      id: 'madrid',
      categoria: 'FLAGSHIP PRINCIPAL',
      nombre: 'Madrid · Serrano',
      direccion: 'Calle de Serrano 48, Salamanca',
      horario: 'Lun - Sáb: 10:00 - 20:30',
      serviciosEspeciales: 'Vestidor 3D Háptico · Sastrería Bespoke · Salón Privado VIP',
      estado: 'ABIERTO',
      esPrincipal: true,
    },
    {
      id: 'paris',
      categoria: 'HAUTE COUTURE',
      nombre: 'París · Saint-Honoré',
      direccion: '22 Rue du Faubourg Saint-Honoré',
      horario: 'Mar - Sáb: 10:30 - 19:30',
      serviciosEspeciales: 'Atelier de Alta Costura de Lyon · Archivo y Cursos Históricos',
      estado: 'ABIERTO',
      esPrincipal: false,
    },
    {
      id: 'milan',
      categoria: 'SASTRERÍA A MEDIDA',
      nombre: 'Milán · Montenapoleone',
      direccion: 'Via Montenapoleone 8b, Quadrilatero',
      horario: 'Lun - Sáb: 10:00 - 19:30',
      serviciosEspeciales: 'Selección Biella Lanificio · Confección 2D/3D Express',
      estado: 'ABIERTO',
      esPrincipal: false,
    },
    {
      id: 'barcelona',
      categoria: 'ATELIER MEDITERRÁNEO',
      nombre: 'Barcelona · Gràcia',
      direccion: 'Passeig de Gràcia 74, Eixample',
      horario: 'Lun - Sáb: 10:30 - 20:00',
      serviciosEspeciales: 'Consulado de Calzado a Medida · Terrazas Experienciales',
      estado: 'ABIERTO',
      esPrincipal: false,
    },
  ];

  // Desplazamiento suave a sección por ancla
  public scrollToSection(sectionId: string): void {
    const element = document.getElementById(sectionId);
    if (element && typeof element.scrollIntoView === 'function') {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      this.scroller.scrollToAnchor(sectionId);
    }
  }

  // Selección de prenda en el probador virtual
  protected seleccionarPrenda(id: string): void {
    this.prendaSeleccionadaId.set(id);
  }

  // Cambio de modo de visualización 3D
  protected cambiarModo3D(modo: string): void {
    this.modo3DActivo.set(modo);
  }

  // Acción para agendar cita o navegar a login
  protected agendarCita(sucursal: SucursalFlagship): void {
    this.router.navigate(['/login'], {
      queryParams: { origen: 'cita', sucursal: sucursal.nombre },
    });
  }
}
