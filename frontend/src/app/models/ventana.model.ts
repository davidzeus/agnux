export interface Ventana {
  id: string;
  titulo: string;
  tipo: 'html' | 'musica' | 'video' | 'texto';
  datos?: any;
  htmlDinamico?: string;
  maximizada: boolean;
  x: number;
  y: number;
  zIndex: number;
}
