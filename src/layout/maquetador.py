"""Maquetado (reflow): del texto plano al árbol Composite paginado."""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field

from src.alineacion.alineadores import Alineador
from src.layout.partidor import partir_parrafo
from src.modelo.elementos import Documento, Linea, Pagina, Palabra, Parrafo


@dataclass(frozen=True)
class LineaUbicada:
    """Una línea junto con su ubicación absoluta en el texto y en las páginas.

    Responsabilidad: responder, para una línea, qué rango de posiciones del
    cursor le pertenece y en qué columna se ve cada una.

    Ítem de cambio que esconde: la conversión entre offsets relativos al
    párrafo (los que guarda ``Linea``) y offsets absolutos del texto.
    """

    linea: Linea
    inicio: int  # primera posición del cursor que cae en esta línea
    fin: int  # última posición del cursor que cae en esta línea (inclusive)
    pagina: int
    inicio_parrafo: int

    def columna(self, posicion: int) -> int:
        return self.linea.columna_de(posicion - self.inicio_parrafo)

    def posicion_mas_cercana(self, columna: int) -> int:
        """Posición de esta línea cuya columna está más cerca de ``columna``."""
        mejor = self.inicio
        mejor_distancia = abs(self.columna(self.inicio) - columna)
        for posicion in range(self.inicio + 1, self.fin + 1):
            distancia = abs(self.columna(posicion) - columna)
            if distancia < mejor_distancia:
                mejor, mejor_distancia = posicion, distancia
        return mejor


@dataclass(frozen=True)
class Maquetacion:
    """Resultado de maquetar: el árbol y un índice plano de líneas.

    Responsabilidad: ofrecer el documento (para visitantes y exportadores) y
    la lista de líneas en orden (para el cursor y la vista) sin que estos
    tengan que recorrer el árbol.

    Ítem de cambio que esconde: cómo se busca la línea de una posición
    (búsqueda binaria sobre los inicios de línea).
    """

    documento: Documento
    lineas: tuple[LineaUbicada, ...]
    _inicios: list[int] = field(repr=False, compare=False)

    def indice_linea(self, posicion: int) -> int:
        return max(0, bisect_right(self._inicios, posicion) - 1)


class Maquetador:
    """Context del patrón Strategy y constructor del Composite.

    Responsabilidad: convertir el texto en un ``Documento`` dividido en
    páginas, párrafos, líneas y palabras, con un ancho fijo de caracteres y
    una cantidad fija de líneas por página, delegando la alineación en la
    estrategia ``Alineador`` actual.

    Ítem de cambio que esconde: el algoritmo de maquetado (corte de líneas,
    corte de páginas y la cache de líneas ya calculadas). Nadie más sabe
    cuándo una palabra pasa de línea o un párrafo de página.
    """

    _LIMITE_CACHE = 20000

    def __init__(self, ancho: int, lineas_por_pagina: int, alineador: Alineador) -> None:
        if ancho < 1:
            raise ValueError("El ancho debe ser al menos 1")
        if lineas_por_pagina < 1:
            raise ValueError("Debe haber al menos una línea por página")
        self.ancho = ancho
        self.lineas_por_pagina = lineas_por_pagina
        self._alineador = alineador
        self._cache: dict[str, tuple[Linea, ...]] = {}

    @property
    def alineador(self) -> Alineador:
        return self._alineador

    @alineador.setter
    def alineador(self, alineador: Alineador) -> None:
        self._alineador = alineador
        self._cache.clear()  # las columnas dependen de la alineación

    def maquetar(self, texto: str) -> Maquetacion:
        documento = Documento(self.ancho, self._alineador.nombre)
        ubicadas: list[LineaUbicada] = []
        pagina: Pagina | None = None
        lineas_en_pagina = 0
        inicio_parrafo = 0
        for texto_parrafo in texto.split("\n"):
            lineas = self._lineas_de(texto_parrafo)
            fragmento: Parrafo | None = None
            for k, linea in enumerate(lineas):
                if pagina is None or lineas_en_pagina == self.lineas_por_pagina:
                    pagina = Pagina(len(documento.hijos()) + 1)
                    documento.agregar(pagina)
                    lineas_en_pagina = 0
                    fragmento = None
                if fragmento is None:
                    fragmento = Parrafo(inicio_parrafo, es_continuacion=k > 0)
                    pagina.agregar(fragmento)
                fragmento.agregar(linea)
                lineas_en_pagina += 1
                es_ultima = k == len(lineas) - 1
                fin_relativo = len(texto_parrafo) if es_ultima else lineas[k + 1].inicio - 1
                ubicadas.append(
                    LineaUbicada(
                        linea=linea,
                        inicio=inicio_parrafo + linea.inicio,
                        fin=inicio_parrafo + fin_relativo,
                        pagina=pagina.numero,
                        inicio_parrafo=inicio_parrafo,
                    )
                )
            inicio_parrafo += len(texto_parrafo) + 1
        return Maquetacion(documento, tuple(ubicadas), [u.inicio for u in ubicadas])

    def _lineas_de(self, texto_parrafo: str) -> tuple[Linea, ...]:
        """Líneas de un párrafo; se cachean porque al teclear casi todos los
        párrafos quedan iguales (las líneas no guardan offsets absolutos, así
        que siguen siendo válidas aunque el párrafo se desplace)."""
        en_cache = self._cache.get(texto_parrafo)
        if en_cache is not None:
            return en_cache
        if len(self._cache) >= self._LIMITE_CACHE:
            self._cache.clear()
        partidas = partir_parrafo(texto_parrafo, self.ancho)
        lineas: list[Linea] = []
        columna_vacia = self._alineador.columna_vacia(self.ancho)
        for k, partida in enumerate(partidas):
            palabras = [
                Palabra(texto_parrafo[f.inicio : f.fin], f.inicio, f.es_continuacion)
                for f in partida.fragmentos
            ]
            columnas = self._alineador.columnas(
                [len(p) for p in palabras], self.ancho, es_ultima=k == len(partidas) - 1
            )
            lineas.append(Linea(palabras, columnas, self.ancho, partida.inicio, columna_vacia))
        resultado = tuple(lineas)
        self._cache[texto_parrafo] = resultado
        return resultado