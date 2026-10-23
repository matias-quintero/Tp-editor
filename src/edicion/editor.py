"""El editor: estado del texto y operaciones primitivas (Receiver del Command)."""

from __future__ import annotations

from dataclasses import dataclass

from src.alineacion.alineadores import Alineador
from src.edicion.cursor import Cursor
from src.layout.maquetador import Maquetacion, Maquetador
from src.visitantes.contadores import ContadorPaginas, ContadorPalabras


@dataclass(frozen=True)
class Estadisticas:
    palabras: int
    paginas: int


class Editor:
    """Receiver del patrón Command.

    Responsabilidad: ser la única fuente de verdad del documento (el texto
    plano y el cursor) y ofrecer las operaciones primitivas que usan los
    comandos: insertar, borrar y cambiar la alineación. También expone la
    maquetación actual y las estadísticas.

    Ítem de cambio que esconde: cómo se guarda el texto (hoy un ``str``) y
    cuándo se vuelve a maquetar (de forma perezosa, solo si hubo cambios y
    alguien pide la maquetación). Los comandos y la vista no saben nada de eso.
    """

    def __init__(self, maquetador: Maquetador, texto: str = "") -> None:
        self._maquetador = maquetador
        self._texto = texto
        self._cursor = Cursor()
        self._maquetacion: Maquetacion | None = None
        self._estadisticas: Estadisticas | None = None

    # --- consultas -------------------------------------------------------

    @property
    def texto(self) -> str:
        return self._texto

    @property
    def cursor(self) -> Cursor:
        return self._cursor

    @property
    def alineador(self) -> Alineador:
        return self._maquetador.alineador

    @property
    def ancho(self) -> int:
        return self._maquetador.ancho

    @property
    def lineas_por_pagina(self) -> int:
        return self._maquetador.lineas_por_pagina

    @property
    def maquetacion(self) -> Maquetacion:
        if self._maquetacion is None:
            self._maquetacion = self._maquetador.maquetar(self._texto)
        return self._maquetacion

    def estadisticas(self) -> Estadisticas:
        if self._estadisticas is None:
            documento = self.maquetacion.documento
            self._estadisticas = Estadisticas(
                palabras=ContadorPalabras.contar(documento),
                paginas=ContadorPaginas.contar(documento),
            )
        return self._estadisticas

    # --- operaciones primitivas (las usan los comandos) ------------------

    def insertar(self, posicion: int, texto: str) -> None:
        """Inserta ``texto`` en ``posicion`` y deja el cursor detrás."""
        posicion = self._validar(posicion)
        self._texto = self._texto[:posicion] + texto + self._texto[posicion:]
        self._invalidar()
        self._cursor.ir_a(posicion + len(texto), len(self._texto))

    def borrar(self, posicion: int, cantidad: int) -> str:
        """Borra ``cantidad`` caracteres desde ``posicion``; devuelve lo borrado."""
        posicion = self._validar(posicion)
        fin = min(len(self._texto), posicion + max(0, cantidad))
        borrado = self._texto[posicion:fin]
        self._texto = self._texto[:posicion] + self._texto[fin:]
        self._invalidar()
        self._cursor.ir_a(posicion, len(self._texto))
        return borrado

    def cambiar_alineador(self, alineador: Alineador) -> Alineador:
        """Cambia la estrategia de alineación; devuelve la anterior."""
        anterior = self._maquetador.alineador
        self._maquetador.alineador = alineador
        self._invalidar()
        return anterior

    # --- movimiento del cursor (no modifica el documento) ----------------

    def mover_cursor_a(self, posicion: int) -> None:
        self._cursor.ir_a(posicion, len(self._texto))

    def mover_izquierda(self) -> None:
        self._cursor.izquierda(len(self._texto))

    def mover_derecha(self) -> None:
        self._cursor.derecha(len(self._texto))

    def mover_arriba(self, lineas: int = 1) -> None:
        self._cursor.vertical(self.maquetacion, -lineas)

    def mover_abajo(self, lineas: int = 1) -> None:
        self._cursor.vertical(self.maquetacion, lineas)

    def mover_inicio_linea(self) -> None:
        self._cursor.inicio_linea(self.maquetacion)

    def mover_fin_linea(self) -> None:
        self._cursor.fin_linea(self.maquetacion)

    # --- internos --------------------------------------------------------

    def _validar(self, posicion: int) -> int:
        if not 0 <= posicion <= len(self._texto):
            raise IndexError(f"Posición fuera del texto: {posicion}")
        return posicion

    def _invalidar(self) -> None:
        self._maquetacion = None
        self._estadisticas = None