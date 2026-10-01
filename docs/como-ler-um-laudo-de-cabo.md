# Como ler um laudo de cabo

O laudo de certificacao tem uma coluna que voce olha e uma que voce precisa
ler. Este documento e sobre a segunda.

## As colunas que importam

| Coluna | O que e | Como ler |
|---|---|---|
| Length | Comprimento medido | Compare com 90 m. Acima disso, reprova por limite fisico |
| Wire Map | Mapa pino a pino | Precisa bater com T568A ou T568B |
| Split | Detectado ou nao | Qualquer "sim" reprova, mesmo com continuidade ok |
| Insertion Loss | Perda por frequencia | **Teto**: menor e melhor |
| NEXT | Acoplamento entre pares | **Piso**: maior e melhor |
| PS-NEXT | NEXT apos ruido do vizinho | **Piso**: maior e melhor |
| Resistance | Continuidade do par | Teto |
| Skew | Diferenca entre pares | Teto |

## Regra 1 - confira o lado de cada limite

Este e o ponto que mais gera conclusao errada.

```
Atenuacao   medido  18,20 dB   limite  20,70 dB   -> ok (18,20 < 20,70)
NEXT        medido  44,10 dB   limite  41,80 dB   -> ok (44,10 > 41,80)
```

Atenuacao e **menor** que o limite. NEXT e **maior** que o limite. O sinal de
comparacao inverte entre os dois.

Se voce aplicar `<=` nos dois, todo cabo com NEXT bom reprova. E se aplicar `>=`
nos dois, todo cabo com atenuacao boa reprova. Nos dois casos, o laudo esta
"criterioso" demais e ninguem sabe dizer por que.

## Regra 2 - confereca todas as frequencias

Um laudo com NEXT otimo a 100 MHz e ruim a 250 MHz **reprova**. Nao e
"reprovou parcialmente". Aprovacao em um laudo de cabo e tudo-ou-nada.

Quando for comparar dois cabos, faca a comparacao na frequencia mais alta que
ambos cobrem. E a frequacao mais alta que decide se o cabo serve a 100 m.

## Regra 3 - "Ressalva" nao e aprovacao

`APROVADO COM RESSALVA` significa que a folga ficou menor que 10% do limite. O
cabo passa, mas nao com margem para o ambiente.

Folga pequena e sensivel a:

- temperatura (cabo quente perde mais)
- curvatura e grampeamento
- emenda mal feita

Um cabo aprovado com 0,4 dB de folga numa bancada a 23 °C pode reprovar dentro
de um rack a 35 °C. **Ressalva nao e aprovacao para descobrir que nao era.**

## Regra 4 - 90 m nao e suggestao

Acima de 90 m de cabo no canal nao existe categoria que salve. O laudo vai dizer
comprimento maior que 90 m e reprovar.

Quando isso acontecer, as saidas sao tres, todas com custo:

1. **Fibra optica.** A unica solucao que cresce.
2. **Repetidor/poe.** Divide o caminho em dois trechos dentro da norma.
3. **Trocar a topologia** para o cabo nao passar por 90 m.

Nao existe "Cat7A resolve". A norma nao cobre esse comprimento para nenhuma
categoria de cobre.

## Regra 5 - split pair reprova sempre

Se o laudo marcar split, o cabo vai embora, sem discussao. Split pode passar
continuidade e reprovar em NEXT, ou o inverso. Nao existe "split acceptable".

Causa quase sempre e crimpagem com o cabo fora do esquadro na hora de puxar o
conector, ou conector de codigo de cor parecido (branco/verde com
branco/laranja sob luz amarela).

## O que fazer quando reprova

| O que estourou | Causa provavel | Acao |
|---|---|---|
| Atenuacao | Cabo de categoria errada, ou comprimento excessivo | Trocar o cabo, revisar caminho |
| NEXT | Categoria errada para a frequencia, ou cabo de baixa qualidade | Trocar por Cat6/Cat6A |
| PS-NEXT | Segue o NEXT; se NEXT ok e PS nao, cabo blindado mal aterrado | Revisar aterramento |
| Resistencia | Conector mal crimpado ou oxidado | Recrimpar |
| Skew | Pares de lotes diferentes no mesmo cabo | Trocar o cabo |
| Split | Crimpagem | Recrimpar com ferramenta certa |
| Comprimento > 90 m | Projeto | Fibra, repetidor ou mudanca de topologia |

**Nao conserta cabo reprovado.** Trocar. Recrimpar um cabo que reprovou em NEXT
normalmente nao resolve, porque a causa e o cabo, nao a ferramenta.

## Checklist antes de assinar

- [ ] Wire map bate com T568A ou T568B?
- [ ] Split: nao?
- [ ] Todas as frequencias da categoria presentes no laudo?
- [ ] NEXT e PS-NEXT acima do piso em **todas** elas?
- [ ] Comprimento ate 90 m?
- [ ] Ressalva? Se sim, minha decisao e consciente.
- [ ] Data do teste de hoje?
- [ ] Equipamento e movel? (modelo diferente, limite diferente)

Se qualquer resposta for nao, o cabo nao esta pronto, por mais que o
equipamento tenha dado "pass".