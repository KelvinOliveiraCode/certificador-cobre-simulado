"""certsim - simulador de certificacao de cabo de rede.

Simula o teste de certificacao de um cabo de rede: mapa de fiaacao pino a pino,
comprimento, atenuacao, NEXT, PS-NEXT, resistencia e desvio de propagacao.
A medicao e estatistica e usa semente fixa, entao o resultado e deterministico.

Simulates network cable certification: pin-to-pin wiring map, length,
attenuation, NEXT, PS-NEXT, resistance and propagation skew. Measurement is
statistical with a fixed seed, so results are deterministic.
"""

from .classificador import APROVADO, APROVADO_COM_RESSALVA, REPROVADO, Veredito, classificar
from .medicao import SEMENTE_FIXA, Perfil, medir
from .laudo import gerar_laudo
from .mapa import T568A, T568B, ErroDeMapa, conferir_mapa, detectar_split_pair

__all__ = [
    "APROVADO",
    "APROVADO_COM_RESSALVA",
    "REPROVADO",
    "Veredito",
    "classificar",
    "Perfil",
    "medir",
    "SEMENTE_FIXA",
    "gerar_laudo",
    "T568A",
    "T568B",
    "ErroDeMapa",
    "conferir_mapa",
    "detectar_split_pair",
]

__version__ = "1.0.0"