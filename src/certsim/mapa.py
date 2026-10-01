"""Mapa de fiaacao pino a pino de um cabo de rede.

Pin-to-pin wiring map for a network cable.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Nominacao T568B, a mais comum em campo.
T568B = ("branco/laranja", "laranja", "branco/verde", "azul",
         "azul", "branco/verde", "branco/marrom", "marrom")

#: Nominacao T568A (invertida em relacao a B nos pares 1 e 3).
T568A = ("branco/verde", "verde", "branco/laranja", "azul",
         "azul", "branco/laranja", "branco/marrom", "marrom")


class ErroDeMapa(ValueError):
    """Mapa de fiaacao invalido.

    Invalid wiring map.
    """


@dataclass(frozen=True)
class ResultadoMapa:
    """Resultado da comparacao entre os dois extremos do cabo.

    Result of comparing both cable ends.

    Atributos:
        par_invertido: Pin 1 ligado a pin 8 e 2 a 7 (inversao de par).
        par_duplicado: Dois pinos com a mesma cor de fio.
        cor_desconhecida: Algum pino com cor fora da tabela.
        pinos: Ligacao pino a pino ja resolvida.
    """

    par_invertido: bool = False
    par_duplicado: bool = False
    cor_desconhecida: bool = False
    pinos: tuple[tuple[int, str], ...] = ()

    @property
    def correto(self) -> bool:
        """Se o mapa esta conforme o padrao esperado.

        Whether the map matches the expected standard.
        """
        return not (self.par_invertido or self.par_duplicado or self.cor_desconhecida)

    def como_texto(self) -> str:
        """Saida tabular do mapa.

        Tabular output of the map.
        """
        linhas = ["PIN | COR", "----+---------------"]
        for pino, cor in self.pinos:
            linhas.append(f"{pino:>3} | {cor}")
        linhas.append("")
        if self.par_invertido:
            linhas.append("FALHA: par invertido (1<->8 e 2<->7)")
        if self.par_duplicado:
            linhas.append("FALHA: crimpagem fora dos padroes T568A/T568B")
        if self.cor_desconhecida:
            linhas.append("FALHA: cor fora da tabela")
        if self.correto:
            linhas.append("Mapa conforme o padrao.")
        return "\n".join(linhas)


def conferir_mapa(
    inicio: tuple[str, ...], fim: tuple[str, ...], padrao: tuple[str, ...] = T568B
) -> ResultadoMapa:
    """Confere o mapa pino a pino de um cabo.

    Check the pin-to-pin wiring map of a cable.

    Args:
        inicio: Cores na ponta A, do pino 1 ao 8.
        fim: Cores na ponta B, do pino 1 ao 8.
        padrao: Nominacao de referencia.

    Returns:
        Um :class:`ResultadoMapa` com o veredito.

    Raises:
        ErroDeMapa: Se alguma ponta nao tiver exatamente 8 posicoes.
    """
    if len(inicio) != 8 or len(fim) != 8:
        raise ErroDeMapa(
            f"Cada ponta precisa de 8 pinos, veio {len(inicio)} e {len(fim)} "
            f"/ each end needs 8 pins, got {len(inicio)} and {len(fim)}"
        )

    pinos = tuple((i + 1, inicio[i]) for i in range(8))

    # Inversao de par: o pino 1 do lado A cai no 8 do lado B.
    invertido = inicio[0] == fim[7] and inicio[1] == fim[6]

    # As cores validas sao a uniao dos dois padroes: o verde, por exemplo,
    # so existe em T568A e nao pode ser tratado como cor desconhecida.
    cores_conhecidas = set(T568B) | set(T568A)
    desconhecida = any(cor not in cores_conhecidas for cor in inicio + fim)

    # Fora dos dois padroes = crimpagem nao conformante. Contar cor repetida
    # nao serve: no padrao, branco/laranja aparece nos pinos 1 e 3 (pares
    # diferentes) e o azul solido nos pinos 4 e 5. Um padrao valido repete
    # cor; o que nao pode e um par montado com as cores erradas.
    def _bate(ponta: tuple[str, ...], ref: tuple[str, ...]) -> bool:
        return tuple(ponta) == tuple(ref)

    padrao_confere = (
        (_bate(inicio, T568B) and _bate(fim, T568B))
        or (_bate(inicio, T568A) and _bate(fim, T568A))
    )

    duplicado = padrao_confere is False

    return ResultadoMapa(
        par_invertido=invertido,
        par_duplicado=duplicado,
        cor_desconhecida=desconhecida,
        pinos=pinos,
    )


def detectar_split_pair(
    inicio: tuple[str, ...], padrao: tuple[str, ...] | None = None
) -> bool:
    """Detecta split pair: os dois fios de um par em pinos nao adjacentes.

    Detecta split pair: the two wires of one pair landing on non-adjacent pins.

    Split pair e o defeito que passa no teste de continuidade e reprova em
    NEXT. E o motivo de "o cabo testa certo e ainda da erro" em campo.

    Args:
        inicio: Cores na ponta A, do pino 1 ao 8.
        padrao: Nominacao de referencia. ``None`` deduz pelo conteudo: quem
            tem ``verde`` so pode ser T568A.

    Returns:
        ``True`` se algum par estiver partido.

    Raises:
        ErroDeMapa: Se a ponta nao tiver 8 pinos.
    """
    if len(inicio) != 8:
        raise ErroDeMapa(
            f"Esperado 8 pinos, veio {len(inicio)} / expected 8, got {len(inicio)}"
        )

    if padrao is None:
        padrao = T568A if "verde" in inicio else T568B

    vistos: dict[str, list[int]] = {}
    for idx, cor in enumerate(inicio):
        vistos.setdefault(cor, []).append(idx + 1)

    for i in range(0, 8, 2):
        par = (padrao[i], padrao[i + 1])
        p1 = vistos.get(par[0], [])
        p2 = vistos.get(par[1], [])
        if not p1 or not p2:
            continue
        if abs(p1[0] - p2[0]) != 1:
            return True
    return False


def mapa_padrao(nome: str = "T568B") -> tuple[str, ...]:
    """Devolve a nominacao de um padrao.

    Return a wiring standard.

    Args:
        nome: ``T568B`` ou ``T568A``.

    Returns:
        A tupla de 8 cores.

    Raises:
        ErroDeMapa: Se o padrao nao existir.
    """
    if nome == "T568B":
        return T568B
    if nome == "T568A":
        return T568A
    raise ErroDeMapa(f"Padrao desconhecido / unknown standard: {nome!r}")