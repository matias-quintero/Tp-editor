"""Bucle principal de la consola: traduce teclas en comandos."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.alineacion.alineadores import (
    Alineador,
    AlineadorCentrado,
    AlineadorDerecha,
    AlineadorIzquierda,
    AlineadorJustificado,
)
from src.comandos.alineacion import ComandoCambiarAlineacion
from src.comandos.edicion import ComandoBorrar, ComandoInsertar
from src.comandos.historial import HistorialComandos
from src.edicion.editor import Editor
from src.vista.pantalla import Pantalla
from src.vista.teclado import LectorTeclas, Tecla, TipoTecla
from src.vista.terminal import Terminal
from src.visitantes.exportadores import ExportadorTextoPlano

_ALINEACIONES: dict[TipoTecla, Callable[[], Alineador]] = {
    TipoTecla.ALINEAR_IZQUIERDA: AlineadorIzquierda,
    TipoTecla.ALINEAR_DERECHA: AlineadorDerecha,
    TipoTecla.ALINEAR_CENTRADO: AlineadorCentrado,
    TipoTecla.ALINEAR_JUSTIFICADO: AlineadorJustificado,
}


class ControladorConsola:
    """Client del patrón Command.

    Responsabilidad: leer teclas, decidir qué hacer con cada una (crear y
    ejecutar un comando, mover el cursor, deshacer, exportar) y pedir a la
    pantalla que se redibuje.

    Ítem de cambio que esconde: el mapeo de teclas a acciones. Cambiar un
    atajo o agregar uno nuevo se hace solo acá.
    """

    def __init__(
        self,
        editor: Editor,
        historial: HistorialComandos,
        pantalla: Pantalla,
        lector: LectorTeclas,
        ruta_exportacion: Path,
    ) -> None:
        self._editor = editor
        self._historial = historial
        self._pantalla = pantalla
        self._lector = lector
        self._ruta_exportacion = ruta_exportacion
        self.mensaje = ""

    def ejecutar(self, terminal: Terminal) -> None:
        while True:
            columnas, filas = terminal.tamanio()
            self._pantalla.dibujar(self._editor, self.mensaje, columnas, filas)
            try:
                tecla = self._lector.leer()
            except KeyboardInterrupt:
                break
            if not self.procesar(tecla):
                break

    def procesar(self, tecla: Tecla) -> bool:
        """Aplica la tecla. Devuelve ``False`` si hay que salir."""
        self.mensaje = ""
        editor = self._editor
        tipo = tecla.tipo
        if tipo is TipoTecla.SALIR:
            return False
        if tipo is TipoTecla.CARACTER:
            self._historial.ejecutar(ComandoInsertar(editor, tecla.caracter))
        elif tipo is TipoTecla.ENTER:
            self._historial.ejecutar(ComandoInsertar(editor, "\n"))
        elif tipo is TipoTecla.BORRAR_ATRAS:
            self._historial.ejecutar(ComandoBorrar(editor, hacia_atras=True))
        elif tipo is TipoTecla.BORRAR_ADELANTE:
            self._historial.ejecutar(ComandoBorrar(editor, hacia_atras=False))
        elif tipo in _ALINEACIONES:
            alineador = _ALINEACIONES[tipo]()
            if self._historial.ejecutar(ComandoCambiarAlineacion(editor, alineador)):
                self.mensaje = f"Alineación: {alineador.nombre}"
        elif tipo is TipoTecla.DESHACER:
            if not self._historial.deshacer():
                self.mensaje = "No hay nada para deshacer"
        elif tipo is TipoTecla.IZQUIERDA:
            editor.mover_izquierda()
        elif tipo is TipoTecla.DERECHA:
            editor.mover_derecha()
        elif tipo is TipoTecla.ARRIBA:
            editor.mover_arriba()
        elif tipo is TipoTecla.ABAJO:
            editor.mover_abajo()
        elif tipo is TipoTecla.PAGINA_ARRIBA:
            editor.mover_arriba(editor.lineas_por_pagina)
        elif tipo is TipoTecla.PAGINA_ABAJO:
            editor.mover_abajo(editor.lineas_por_pagina)
        elif tipo is TipoTecla.INICIO:
            editor.mover_inicio_linea()
        elif tipo is TipoTecla.FIN:
            editor.mover_fin_linea()
        elif tipo is TipoTecla.EXPORTAR:
            self._exportar()
        return True

    def _exportar(self) -> None:
        contenido = ExportadorTextoPlano().exportar(self._editor.maquetacion.documento)
        try:
            self._ruta_exportacion.write_text(contenido, encoding="utf-8")
            self.mensaje = f"Exportado a {self._ruta_exportacion}"
        except OSError as error:
            self.mensaje = f"No se pudo exportar: {error}"