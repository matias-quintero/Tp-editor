"""Dibujo del editor en la consola (vista reducida + estadísticas)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from src.edicion.editor import Editor

FILAS_FIJAS = 7  # título, 2 bordes, estado, 2 de ayuda, mensaje

AYUDA = (
    " Flechas/Inicio/Fin/RePág/AvPág: mover   Backspace/Supr: borrar   Ctrl+Z: deshacer",
    " Ctrl+L izq  Ctrl+N centro  Ctrl+R der  Ctrl+T justif.   Ctrl+O exportar  Ctrl+S salir",
)


@dataclass(frozen=True)
class Cuadro:
    """Una "foto" de la pantalla lista para escribir (filas y cursor, base 0)."""

    filas: list[str]
    cursor_fila: int
    cursor_columna: int


class Pantalla:
    """Responsabilidad: mostrar una ventana (vista reducida) del documento
    alrededor del cursor, con separadores de página, y una barra de estado
    con las estadísticas y la alineación.

    Ítem de cambio que esconde: el diseño visual de la consola y el
    desplazamiento (scroll) de la ventana. ``componer`` no escribe nada, así
    que se puede testear sin terminal.
    """

    def __init__(self, escribir: Callable[[str], None]) -> None:
        self._escribir = escribir
        self._desplazamiento = 0

    def componer(self, editor: Editor, mensaje: str, columnas: int, filas: int) -> Cuadro:
        maquetacion = editor.maquetacion
        ancho = editor.ancho
        por_pagina = editor.lineas_por_pagina
        interior = ancho + 1  # +1 para que el cursor quepa al final de una línea llena
        alto = max(1, filas - FILAS_FIJAS)

        # Cada página ocupa `por_pagina` filas y, desde la 2da, un separador antes.
        def fila_de_linea(indice: int) -> int:
            return indice + indice // por_pagina

        total_lineas = len(maquetacion.lineas)
        total_filas = fila_de_linea(total_lineas - 1) + 1
        indice_cursor, columna_cursor = editor.cursor.ubicacion(maquetacion)
        fila_cursor = fila_de_linea(indice_cursor)

        self._desplazamiento = min(self._desplazamiento, max(0, total_filas - alto))
        if fila_cursor < self._desplazamiento:
            self._desplazamiento = fila_cursor
        elif fila_cursor >= self._desplazamiento + alto:
            self._desplazamiento = fila_cursor - alto + 1

        cuerpo: list[str] = []
        for fila in range(self._desplazamiento, self._desplazamiento + alto):
            bloque, resto = divmod(fila, por_pagina + 1)
            indice = bloque * por_pagina + resto
            if fila >= total_filas:
                cuerpo.append("|" + " " * interior + "|")
            elif resto == por_pagina:
                cuerpo.append("+" + f" Página {bloque + 2} ".center(interior, "-") + "+")
            else:
                texto = maquetacion.lineas[indice].linea.renderizar()
                cuerpo.append("|" + texto.ljust(interior) + "|")

        estadisticas = editor.estadisticas()
        linea_cursor = maquetacion.lineas[indice_cursor]
        estado = (
            f" Palabras: {estadisticas.palabras} | Páginas: {estadisticas.paginas}"
            f" | Alineación: {editor.alineador.nombre}"
            f" | Pág {linea_cursor.pagina} Lín {indice_cursor % por_pagina + 1}"
            f" Col {columna_cursor + 1}"
        )
        titulo = f" Editor de texto - ancho {ancho}, {por_pagina} líneas por página"
        borde = "+" + "-" * interior + "+"
        todas = [titulo, borde, *cuerpo, borde, estado, *AYUDA, " " + mensaje]
        todas = [fila[:columnas] for fila in todas]
        return Cuadro(
            filas=todas,
            cursor_fila=2 + fila_cursor - self._desplazamiento,
            cursor_columna=1 + columna_cursor,
        )

    def dibujar(self, editor: Editor, mensaje: str, columnas: int, filas: int) -> None:
        cuadro = self.componer(editor, mensaje, columnas, filas)
        partes = ["\x1b[?25l"]  # ocultar cursor mientras se dibuja (evita parpadeo)
        for numero, fila in enumerate(cuadro.filas, start=1):
            partes.append(f"\x1b[{numero};1H{fila}\x1b[K")
        partes.append("\x1b[J")
        partes.append(f"\x1b[{cuadro.cursor_fila + 1};{cuadro.cursor_columna + 1}H\x1b[?25h")
        self._escribir("".join(partes))