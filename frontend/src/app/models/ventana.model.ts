export interface Ventana {
  id: string;
  titulo: string;
  tipo: 'html' | 'musica' | 'video' | 'texto' | 'iframe';
  datos?: any;
  htmlDinamico?: string;
  urlDinamica?: string;
  maximizada: boolean;
  x: number;
  y: number;
  zIndex: number;
  width?: number;
  height?: number;
  replyInput?: string;
  cargandoRespuesta?: boolean;
}
