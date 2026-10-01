"""Simulacao de medicao por padrao estatistico, com semente fixa.

Deterministic measurement simulation with a fixed seed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

#: Semente fixa. A mesma semente sempre produz a mesma medicao.
SEMENTE_FIXA = 20260901

#: Limites de atenuacao do canal por categoria e frequencia (dB).
LIMITES_ATENUACAO = {
    "5e": {100: 20.0},
    "6": {100: 20.7, 250: 26.6},
    "6A": {100: 21.0, 250: 26.0, 500: 32.0},
}

#: Pisos de NEXT (dB). NEXT nao se soma a perda: e limite do par.
LIMITES_NEXT = {
    "5e": {100: 32.4},
    "6": {100: 41.8, 250: 38.6},
    "6A": {100: 44.4, 250: 41.4, 500: 39.1},
}

#: Pisos de PS-NEXT (dB).
LIMITES_PS_NEXT = {
    "5e": {100: 27.4},
    "6": {100: 39.1, 250: 36.1},
    "6A": {100: 42.4, 250: 39.4, 500: 37.2},
}

#: Limite de resistencia de par (ohm). Acima disso, o par esta aberto.
LIMITE_RESISTENCIA_OHM = 24.0

#: Limite de desvio de propagacao entre pares (ns).
LIMITE_DESVIO_NS = 5.0

#: Comprimento maximo de cabo no canal (m).
LIMITE_CANAL_M = 90.0


@dataclass
class Perfil:
    """Perfil de medicao de um cabo.

    Measurement profile of a cable.

    Atributos:
        nome: Identificador do perfil.
        categoria: ``5e``, ``6`` ou ``6A``.
        comprimento_m: Comprimento do cabo em metros.
        perda_extra_db: Perda adicional plantada por mecanismo.
        crosstalk_db: Acoplamento entre pares em dB (menor e melhor).
        resistencia_ohm: Resistencia do par.
        desvio_ps_ns: Desvio de propagacao entre pares, em ns.
        defeito: ``aberto``, ``curto``, ``invertido``, ``split`` ou ``None``.
        pinos: Cores do lado A, para o mapa pino a pino.
    """

    nome: str
    categoria: str = "6"
    comprimento_m: float = 90.0
    perda_extra_db: float = 0.0
    crosstalk_db: float = 55.0
    resistencia_ohm: float = 21.0
    desvio_ps_ns: float = 4.0
    defeito: str | None = None
    pinos: tuple[str, ...] = field(default=())


def frequencias_da(categoria: str) -> tuple[int, ...]:
    """Frequencias avaliadas para uma categoria.

    Evaluation frequencies for a category.

    Args:
        categoria: ``5e``, ``6`` ou ``6A``.

    Returns:
        As frequencias em MHz, ordenadas.

    Raises:
        ValueError: Se a categoria nao existir.
    """
    if categoria not in LIMITES_ATENUACAO:
        raise ValueError(f"Categoria desconhecida / unknown category: {categoria!r}")
    return tuple(sorted(LIMITES_ATENUACAO[categoria]))


def medir(perfil: Perfil, semente: int = SEMENTE_FIXA) -> dict:
    """Simula a medicao de um cabo.

    Simulate the measurement of a cable.

    O ruido e drawn de uma distribuicao normal com semente fixa, entao a mesma
    chamada com o mesmo perfil devolve exatamente os mesmos numeros. O ruido e
    pequenos de proposito: um certificador real tem dispersao de talvez 0,3 dB,
    e um simulador que adiciona 3 dB de ruido esconde justamente o defeito que
    o laudo deveria apontar.

    Args:
        perfil: O perfil do cabo.
        semente: Semente do gerador.

    Returns:
        Um ``dict`` com ``atenuacao``, ``next``, ``ps_next``,
        ``resistencia`` e ``desvio``.
    """
    rng = random.Random(f"{semente}-{perfil.nome}")

    atenuacao: dict[int, float] = {}
    next_db: dict[int, float] = {}
    ps_next_db: dict[int, float] = {}

    for freq in frequencias_da(perfil.categoria):
        base = LIMITES_ATENUACAO[perfil.categoria][freq]
        # Escala linear com o comprimento, mais o ruido e a perda plantada.
        perda = base * (perfil.comprimento_m / 100.0)
        perda += perfil.perda_extra_db
        perda += rng.gauss(0.0, 0.3)

        piso_next = LIMITES_NEXT[perfil.categoria][freq]
        piso_ps = LIMITES_PS_NEXT[perfil.categoria][freq]

        # Acoplamento piora com o comprimento. Valor medido = piso + folga.
        folga_next = max(0.5, perfil.crosstalk_db - (perfil.crosstalk_db - piso_next) * 0.6)
        medido_next = piso_next + folga_next + rng.gauss(0.0, 0.4)

        medido_ps = piso_ps + (medido_next - piso_next) * 0.85 + rng.gauss(0.0, 0.4)

        atenuacao[freq] = round(perda, 2)
        next_db[freq] = round(medido_next, 2)
        ps_next_db[freq] = round(medido_ps, 2)

    # Par aberto: a resistencia sobe e o NEXT desaba.
    resistencia = perfil.resistencia_ohm
    if perfil.defeito == "aberto":
        resistencia = round(resistencia + 60.0, 2)
        for freq in atenuacao:
            next_db[freq] = round(next_db[freq] * 0.35, 2)
    elif perfil.defeito == "curto":
        resistencia = round(resistencia * 0.08, 2)

    desvio = perfil.desvio_ps_ns + abs(rng.gauss(0.0, 0.3))
    if perfil.defeito == "split":
        desvio = round(desvio + 9.0, 2)

    return {
        "atenuacao": atenuacao,
        "next": next_db,
        "ps_next": ps_next_db,
        "resistencia": round(resistencia, 2),
        "desvio": round(desvio, 2),
    }