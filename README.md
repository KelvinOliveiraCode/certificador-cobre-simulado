<div align="center">

<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/tests-84%20passing-brightgreen?style=flat-square" alt="Tests">
  <img src="https://img.shields.io/badge/coverage-96%25-brightgreen?style=flat-square" alt="Coverage">
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/platform-Windows-blue?style=flat-square" alt="Windows">
</p>

# certificador-cobre-simulado

**Simula teste de certificacao de cabo de rede e emite laudo com o limite estourado nomeado.**

</div>

---

## PT-BR

### O que e

CLI que simula o ensaio de certificacao de um cabo de rede: mapa de fiaicao
pino a pino, comprimento, atenuacao, NEXT, PS-NEXT, resistencia e desvio de
propagacao. Aplica os limites da ISO/IEC 11811 e devolve o veredito com o
parametro e a frequencia que estourou. A medicao e estatistica com semente
fixa, entao o resultado e deterministico.

### Por que foi feito

"Continuidade passou" e a frase que mais atrasa uma obra. Um cabo com os oito
fios ligados pode ter o par 1 e o par 3 invertidos, ou um split pair que
continua passando em continuidade e reprovando em NEXT. O tecnico passa o cabo,
o cliente reclama, e alguem volta para crimpar de novo.

O laudo so ajuda se voce sabe **para que lado esta o limite**. Atenuacao e teto:
menor e melhor. NEXT e piso: maior e melhor. Aplicar o sinal de comparacao errado
nos dois reprova cabo bom - e a falha silenciosa, do tipo que so aparece quando o
cliente liga.

### Como rodar

```powershell
# 1. Instalar
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
# instala o pacote local para o python -m <pacote>$nl
# 2. Validar
python -m pytest tests/ -v

# 3. Executar
python -m certsim testar dados/cenarios.yaml
```

Saida real:

```
CABO                   CAT     COMP  SITUACAO
---------------------- ---- -------  ----------------------
cabo-01-cat6-ok        6      45.0m  APROVADO
cabo-02-cat6-ok-longo  6      88.0m  APROVADO
cabo-03-cat6a-ok       6A     90.0m  APROVADO COM RESSALVA
cabo-04-cat6a-curto    6A     12.0m  APROVADO
cabo-05-cat6-padrao-a  6      60.0m  APROVADO
cabo-06-cat6-ressalva  6      84.0m  APROVADO
cabo-07-cat6a-maximo   6A     89.5m  APROVADO COM RESSALVA
cabo-08-par-aberto     6      50.0m  REPROVADO
                                    -> NEXT/100/30.58 dB/41.80 dB
                                    -> NEXT/250/28.97 dB/38.60 dB
                                    -> resistencia/--/81.00 ohm/24.0 ohm
                                    -> fiacao/aberto/--/--
cabo-09-par-em-curto   6      50.0m  REPROVADO
                                    -> fiacao/curto/--/--
cabo-10-par-invertido  6      40.0m  REPROVADO
                                    -> fiacao/invertido/--/--
cabo-11-split-pair     6      55.0m  REPROVADO
                                    -> desvio/--/13.29 ns/5.0 ns
                                    -> fiacao/split/--/--
cabo-12-comprimento-acima 6     105.0m  REPROVADO
                                    -> comprimento/--/105.00 m/90 m

7/12 aprovados
```

Cada linha `->` nomeia o parametro, a frequencia, o valor medido e o limite.
Para reprovar por perda sao 18,20 dB; o codigo diz exatamente quais numeros
ficaram de fora.

Outros comandos:

```powershell
python -m certsim cabos                                     # limites por categoria
python -m certsim testar dados/cenarios.yaml --laudo exemplos/laudo-certificacao.md
python -m certsim testar dados/cenarios.yaml --semente 999   # outra realizacao
```

### O que aprendi

- **Ate hoje eu achava que subir de categoria diminuia a perda.** Nao. Cat6A tem
  limite de 21,0 dB em 100 MHz contra 20,7 dB do Cat6 - **pior** no mesmo ponto.
  Categoria superior nao e cabo mais fino, e cabo mais largo. Escrevi um teste
  que afirmava o contrario e ele falhou; o codigo estava certo e a minha
  premissa, errada. O ganho do Cat6A esta no piso de NEXT e em cobrir 500 MHz.
- **Reprovar por folga, e nao so por estouro, tinha um efeito colateral.** Na
  primeira versao, qualquer parametro dentro de 90% do limite caia em
  `REPROVADO` por causa de um `any()` mal escrito. O resultado era reprovar
  cabo de 90 m que estava dentro da norma. Agora folga pequena vira
  `APROVADO COM RESSALVA`, que ainda aprova porque a obra precisa terminar.
- **"Cor repetida" nao detecta crimpagem errada.** T568B tem `branco/laranja`
  nos pinos 1 e 3 (pares diferentes) e `azul` solido nos pinos 4 e 5. Contar
  repeticao acusava padrao valido. A regra que funciona e comparar a ponta
  inteira com os dois padroes: nao bate com nenhum, nao e conformante.
- **Contar por ponta, nao pelas duas juntas.** Juntar as duas pontas antes de
  contar fez todo cabo com pontas iguais parecer duplicado - que e o caso
  normal. O bug aparecia como "nenhum cabo aprova", e o primeiro impulso seria
  culpar o limite, nao a contagem.
- **Split pair nao aparece nos numeros eletricos de forma confiavel.** Ele passa
  em continuidade e so aparece no NEXT. Por isso o mapa de fiaacao e uma checagem
  separada, e nao uma consequencia da medicao.

### Limitacoes

- **Nao mede nada.** Nao existe sensor nem amostra real. Todo numero sai de uma
  distribuicao normal com semente fixa. Serve para aplicar as regras e ensinar
  a ler o laudo, nao para substituir bancada.
- **NEXT e PS-NEXT sao sinteticos.** A medicao simula o acoplamento a partir do
  perfil, nao de geometria de par, que e o que define o ICR de verdade.
- **Nao modela temperatura, curvatura, grampeamento nem emenda.** Folga pequena
  em ambiente quente e um caso real que a ferramenta nao enxerga.
- **Nao emite laudo no formato proprietario de nenhum equipamento.** O formato
  e legivel por pessoa, nao importavel por software de tercero.
- **O laudo nao tem valor de aceite.** Um cabo que reprova aqui pode passar no
  equipamento do fabricante, e o inverso tambem vale. Para decisao de obra, meca.

### Licenca

MIT. Ver [LICENSE](LICENSE).

---

## EN

### What it is

A CLI that simulates a network cable certification test: pin-to-pin wiring map,
length, attenuation, NEXT, PS-NEXT, resistance and propagation skew. It applies
the ISO/IEC 11811 limits and returns a verdict naming the parameter and
frequency that was exceeded. Measurement is statistical with a fixed seed, so
the result is deterministic.

### Why it was built

"Continuity passed" is the phrase that most delays a job. A cable with all eight
wires connected can have pair 1 and pair 3 inverted, or a split pair that keeps
passing continuity and fails NEXT. The technician installs it, the client calls,
and someone goes back to re-crimp.

A report only helps if you know **which side of the limit it sits on**. Attenuation
is a ceiling: lower is better. NEXT is a floor: higher is better. Applying the
same comparison to both rejects a good cable - the silent failure, the kind that
only surfaces when the client calls.

### How to run

```powershell
# 1. Install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
# instala o pacote local para o python -m <pacote>$nl
# 2. Validate
python -m pytest tests/ -v

# 3. Run
python -m certsim testar dados/cenarios.yaml
```

Real output:

```
CABO                   CAT     COMP  SITUACAO
---------------------- ---- -------  ----------------------
cabo-01-cat6-ok        6      45.0m  APROVADO
cabo-02-cat6-ok-longo  6      88.0m  APROVADO
cabo-03-cat6a-ok       6A     90.0m  APROVADO COM RESSALVA
cabo-04-cat6a-curto    6A     12.0m  APROVADO
cabo-05-cat6-padrao-a  6      60.0m  APROVADO
cabo-06-cat6-ressalva  6      84.0m  APROVADO
cabo-07-cat6a-maximo   6A     89.5m  APROVADO COM RESSALVA
cabo-08-par-aberto     6      50.0m  REPROVADO
                                    -> NEXT/100/30.58 dB/41.80 dB
                                    -> NEXT/250/28.97 dB/38.60 dB
                                    -> resistencia/--/81.00 ohm/24.0 ohm
                                    -> fiacao/aberto/--/--
cabo-09-par-em-curto   6      50.0m  REPROVADO
                                    -> fiacao/curto/--/--
cabo-10-par-invertido  6      40.0m  REPROVADO
                                    -> fiacao/invertido/--/--
cabo-11-split-pair     6      55.0m  REPROVADO
                                    -> desvio/--/13.29 ns/5.0 ns
                                    -> fiacao/split/--/--
cabo-12-comprimento-acima 6     105.0m  REPROVADO
                                    -> comprimento/--/105.00 m/90 m

7/12 aprovados
```

Each `->` line names the parameter, the frequency, the measured value and the
limit. To fail on loss by 18.20 dB, the code names exactly which numbers were
outside.

Other commands:

```powershell
python -m certsim cables                                     # limits per category
python -m certsim test data/cenarios.yaml --report examples/laudo-certificacao.md
python -m certsim test data/cenarios.yaml --seed 999         # another draw
```

### What I learned

- **Until now I thought a higher category meant less loss.** It does not. Cat6A
  has a 21.0 dB limit at 100 MHz against Cat6's 20.7 dB - **worse** at the same
  point. A higher category is not a thinner cable, it is a wider one. I wrote a
  test asserting the opposite and it failed; the code was right and my premise
  was wrong. Cat6A's gain is in the NEXT floor and in covering 500 MHz.
- **Failing on thin margin, not just on breach, had a side effect.** The first
  version dropped anything within 90% of the limit into `REPROVADO` because of a
  misplaced `any()`. The result was rejecting a 90 m cable that was inside spec.
  Now thin margin becomes `APROVADO COM RESSALVA`, which still passes because
  the job has to get done.
- **"Repeated colour" does not detect a bad crimp.** T568B has
  `branco/laranja` on pins 1 and 3 (different pairs) and solid `azul` on pins 4
  and 5. Counting repetition flagged a valid standard. The rule that works is
  comparing the whole end against both standards: match neither, it is not
  conformant.
- **Count per end, not across both.** Joining the two ends before counting made
  every cable with equal ends look duplicated - which is the normal case. The
  bug showed up as "no cable passes", and the first instinct would be to blame
  the limit, not the count.
- **Split pair does not show up reliably in the electrical numbers.** It passes
  continuity and only appears in NEXT. That is why the wiring map is a separate
  check and not a consequence of the measurement.

### Limitations

- **It measures nothing.** There is no sensor and no real sample. Every number
  comes from a normal distribution with a fixed seed. It serves to apply the
  rules and teach report reading, not to replace a bench.
- **NEXT and PS-NEXT are synthetic.** Coupling is simulated from the profile, not
  from pair geometry, which is what actually determines the ICR.
- **No temperature, bend, staple or splice model.** Thin margin in a warm room is
  a real case the tool cannot see.
- **No proprietary equipment output format.** The format is readable by a person,
  not importable by third-party software.
- **The report carries no certificate value.** A cable that fails here may pass
  on the manufacturer's unit, and the reverse also holds. For a real job, measure.

### License

MIT. See [LICENSE](LICENSE).

---

## Estrutura / Structure

```
src/certsim/
  mapa.py          fiacao pino a pino, split pair
  medicao.py       simulacao estatistica com semente fixa
  classificador.py veredito e limites estourados
  laudo.py         saida em Markdown
  cli.py           interface de linha de comando
dados/cenarios.yaml   12 cabos: 7 bons, 5 com falhas distintas
docs/                 o que e certificacao, como ler o laudo
exemplos/             saidas reais
tests/                84 testes
```

## Licenca / License

MIT &mdash; [LICENSE](LICENSE)

---

<div align="center">
  <sub>Por <a href="https://github.com/KelvinOliveiraCode">Kelvin Oliveira</a> &middot;
  <a href="https://kelvinoliveiracode.github.io/portfolio/">portfolio</a></sub>
</div>
