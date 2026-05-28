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
  width?: number;
  height?: number;
  replyInput?: string;
  cargandoRespuesta?: boolean;
}
