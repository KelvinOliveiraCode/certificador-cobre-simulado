"""Testes do mapa de fiaacao e da simulacao de medicao.

Tests for the wiring map and the measurement simulation.
"""

from __future__ import annotations

import pytest

from certsim.medicao import (
    LIMITE_CANAL_M,
    LIMITES_ATENUACAO,
    LIMITES_NEXT,
    SEMENTE_FIXA,
    Perfil,
    frequencias_da,
    medir,
)
from certsim.mapa import (
    T568A,
    T568B,
    ErroDeMapa,
    conferir_mapa,
    detectar_split_pair,
    mapa_padrao,
)


class TestPadroes:
    """Os dois padroes de crimpagem."""

    def test_t568b_tem_oito_pinos(self) -> None:
        assert len(T568B) == 8

    def test_t568a_tem_oito_pinos(self) -> None:
        assert len(T568A) == 8

    def test_padroes_diferem_nos_pinos_1_2_e_3(self) -> None:
        # T568A e T568B diferem no par 1 (pinos 1/2) e no par 3 (pinos 3/6).
        assert T568A[0] != T568B[0]
        assert T568A[1] != T568B[1]
        assert T568A[2] != T568B[2]
        assert T568A[5] != T568B[5]

    def test_padroes_iguais_no_par_azul(self) -> None:
        # Pinos 4 e 5 sao o par azul solido, igual nos dois padroes.
        assert T568A[3] == T568B[3]
        assert T568A[4] == T568B[4]

    def test_padrao_verde_so_existe_em_t568a(self) -> None:
        assert "verde" in T568A
        assert "verde" not in T568B

    def test_mapa_padrao_devolve_tupla(self) -> None:
        assert mapa_padrao("T568B") == T568B

    def test_mapa_padrao_desconhecido_levanta_erro(self) -> None:
        with pytest.raises(ErroDeMapa, match="Padrao desconhecido"):
            mapa_padrao("T999")


class TestConferenciaDeMapa:
    """Conferencia pino a pino."""

    def test_mapa_correto_passa(self) -> None:
        r = conferir_mapa(T568B, T568B)
        assert r.correto is True

    def test_mapa_correto_lista_oito_pinos(self) -> None:
        assert len(conferir_mapa(T568B, T568B).pinos) == 8

    def test_mapa_zerado_no_padrao_b_e_igual_ao_a(self) -> None:
        # Conectado A em A e B em B: cada ponta esta em si, sem inversao.
        assert conferir_mapa(T568A, T568A).correto is True

    def test_ponta_curta_levanta_erro(self) -> None:
        with pytest.raises(ErroDeMapa, match="8 pinos"):
            conferir_mapa(T568B[:4], T568B)

    def test_cor_desconhecida_detectada(self) -> None:
        ruim = ("rosa",) + T568B[1:]
        assert conferir_mapa(ruim, ruim).cor_desconhecida is True

    def test_crimpagem_fora_do_padrao_detectada(self) -> None:
        # Branco/laranja e branco/marrom no mesmo par: nao existe em padrao.
        ruim = ("branco/laranja", "branco/marrom") + T568B[2:]
        assert conferir_mapa(ruim, ruim).par_duplicado is True

    def test_mapa_reprova_texto_mostra_falha(self) -> None:
        ruim = ("branco/laranja", "branco/marrom") + T568B[2:]
        texto = conferir_mapa(ruim, ruim).como_texto()
        assert "crimpagem fora" in texto.lower()


class TestSplitPair:
    """Split pair: passa no continuidade, reprova em NEXT."""

    def test_padrao_nao_tem_split(self) -> None:
        assert detectar_split_pair(T568B) is False

    def test_split_detectado(self) -> None:
        # Branco/laranja no pino 1, parceiro no pino 4 (nao adjacente).
        ruim = ("branco/laranja", "laranja", "branco/verde", "branco/laranja") + T568B[4:]
        assert detectar_split_pair(ruim) is True

    def test_pinos_incompletos_levanta_erro(self) -> None:
        with pytest.raises(ErroDeMapa):
            detectar_split_pair(T568B[:4])

    def test_t568a_tambem_nao_tem_split(self) -> None:
        assert detectar_split_pair(T568A) is False


class TestLimites:
    """As tabelas de limite."""

    def test_cada_categoria_tem_next_para_toda_frequencia(self) -> None:
        for cat, tabela in LIMITES_ATENUACAO.items():
            for freq in tabela:
                assert freq in LIMITES_NEXT[cat]

    def test_categoria_desconhecida_levanta_valueerror(self) -> None:
        with pytest.raises(ValueError, match="Categoria desconhecida"):
            frequencias_da("8")

    def test_frequencias_de_6a_inclui_500(self) -> None:
        assert 500 in frequencias_da("6A")

    def test_limite_canal_e_90m(self) -> None:
        assert LIMITE_CANAL_M == 90.0


class TestMedicaoDeterminismo:
    """Mesmo perfil e mesma semente, mesmos numeros."""

    def test_dois_chamados_identicos(self) -> None:
        p = Perfil("x", "6", 50.0)
        assert medir(p) == medir(p)

    def test_semente_diferente_muda_o_resultado(self) -> None:
        p = Perfil("x", "6", 50.0)
        assert medir(p, semente=1) != medir(p, semente=2)

    def test_nome_diferente_muda_o_resultado(self) -> None:
        a = medir(Perfil("a", "6", 50.0))
        b = medir(Perfil("b", "6", 50.0))
        assert a["atenuacao"] != b["atenuacao"]

    def test_semente_fixa_e_um_inteiro_estavel(self) -> None:
        assert isinstance(SEMENTE_FIXA, int)


class TestMedicaoFisica:
    """A medicao obedece a fisica do modelo."""

    def test_cabo_mais_curto_perde_menos(self) -> None:
        curto = medir(Perfil("x", "6", 10.0))["atenuacao"][100]
        longo = medir(Perfil("x", "6", 90.0))["atenuacao"][100]
        assert curto < longo

    def test_perda_plantada_aumenta_a_medida(self) -> None:
        base = medir(Perfil("x", "6", 50.0))["atenuacao"][100]
        com_extra = medir(Perfil("x", "6", 50.0, perda_extra_db=4.0))["atenuacao"][100]
        assert com_extra > base

    def test_par_aberto_derruba_next(self) -> None:
        bom = medir(Perfil("x", "6", 50.0))["next"][100]
        aberto = medir(Perfil("x", "6", 50.0, defeito="aberto"))["next"][100]
        assert aberto < bom

    def test_par_aberto_sobe_resistencia(self) -> None:
        assert medir(Perfil("x", "6", 50.0, defeito="aberto"))["resistencia"] > 24.0

    def test_par_em_curto_derruba_resistencia(self) -> None:
        assert medir(Perfil("x", "6", 50.0, defeito="curto"))["resistencia"] < 5.0

    def test_split_aumenta_desvio(self) -> None:
        base = medir(Perfil("x", "6", 50.0))["desvio"]
        split = medir(Perfil("x", "6", 50.0, defeito="split"))["desvio"]
        assert split > base

    def test_categoria_maior_sobe_o_teto_nas_frequencias_altas(self) -> None:
        # Cat6A tem limite PIOR que Cat6 em 100 MHz (21,0 contra 20,7 dB):
        # ele nao e mais fino, e mais largo. O ganho dele aparece em 250/500.
        limite_6 = LIMITES_ATENUACAO["6"][100]
        limite_6a = LIMITES_ATENUACAO["6A"][100]
        assert limite_6a > limite_6
        # E o piso de NEXT sobe, o que e o beneficio real da categoria.
        assert LIMITES_NEXT["6A"][100] > LIMITES_NEXT["6"][100]

    def test_so_cat6a_suporta_500mhz(self) -> None:
        assert 500 in LIMITES_ATENUACAO["6A"]
        assert 500 not in LIMITES_ATENUACAO["6"]
        assert 500 not in LIMITES_ATENUACAO["5e"]

    def test_medicao_tem_todas_as_frequencias_da_categoria(self) -> None:
        m = medir(Perfil("x", "6A", 50.0))
        assert set(m["atenuacao"]) == {100, 250, 500}
        assert set(m["next"]) == {100, 250, 500}
        assert set(m["ps_next"]) == {100, 250, 500}

    def test_valores_arredondados(self) -> None:
        m = medir(Perfil("x", "6", 50.0))
        assert round(m["resistencia"], 2) == m["resistencia"]