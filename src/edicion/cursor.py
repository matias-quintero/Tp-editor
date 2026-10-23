"""Cursor del editor."""

from __future__ import annotations

from src.layout.maquetador import Maquetacion


class Cursor:
    """Posición de edición dentro del texto.

    Responsabilidad: guardar la posición actual (un offset entre 0 y el
    largo del texto) y calcular los movimientos: izquierda/derecha por
    carácter, arriba/abajo por línea visual, inicio/fin de línea y saltos
    de página.

    Ítem de cambio que esconde: cómo se traduce un movimiento visual (por
    ejemplo "una línea arriba") a un offset del texto. Recuerda la columna
    deseada para que, al subir y bajar por líneas cortas, el cursor vuelva
    a la columna original (como en cualquier editor).
    """

    def __init__(self, posicion: int = 0) -> None:
        self._posicion = posicion
        self._columna_deseada: int | None = None

    @property
    def posicion(self) -> int:
        return self._posicion

    def ir_a(self, posicion: int, largo_texto: int) -> None:
        self._posicion = max(0, min(posicion, largo_texto))
        self._columna_deseada = None

    def izquierda(self, largo_texto: int) -> None:
        self.ir_a(self._posicion - 1, largo_texto)

    def derecha(self, largo_texto: int) -> None:
        self.ir_a(self._posicion + 1, largo_texto)

    def vertical(self, maquetacion: Maquetacion, delta: int) -> None:
        """Mueve ``delta`` líneas visuales (negativo = hacia arriba)."""
        indice = maquetacion.indice_linea(self._posicion)
        actual = maquetacion.lineas[indice]
        columna = self._columna_deseada
        if columna is None:
            columna = actual.columna(self._posicion)
        destino = indice + delta
        if destino < 0:
            self._posicion = maquetacion.lineas[0].inicio
        elif destino >= len(maquetacion.lineas):
            self._posicion = maquetacion.lineas[-1].fin
        else:
            self._posicion = maquetacion.lineas[destino].posicion_mas_cercana(columna)
        self._columna_deseada = columna

    def inicio_linea(self, maquetacion: Maquetacion) -> None:
        linea = maquetacion.lineas[maquetacion.indice_linea(self._posicion)]
        self._posicion = linea.inicio
        self._columna_deseada = None

    def fin_linea(self, maquetacion: Maquetacion) -> None:
        linea = maquetacion.lineas[maquetacion.indice_linea(self._posicion)]
        self._posicion = linea.fin
        self._columna_deseada = None

    def ubicacion(self, maquetacion: Maquetacion) -> tuple[int, int]:
        """(índice de línea visual, columna) donde se dibuja el cursor."""
        indice = maquetacion.indice_linea(self._posicion)
        return indice, maquetacion.lineas[indice].columna(self._posicion)