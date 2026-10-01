# O que e certificacao de cabo

Certificacao e o teste que prova que o par de fios faz o que a categoria promete,
em todas as frequencias que a categoria cobre. Nao e "o cabo esta ligado": e "o
cabo tem dentro da performance". Um cabo que acende o LED e reprova NEXT a 250 MHz
funciona na pratica a 100 m e falha a 90.

## Os tres testes, em ordem de importancia

### 1. Continuidade e mapa de fiaacao (o mais basico)

Cada pino de um lado tem que ligar ao pino certo do outro. E o teste que revela:

- **Par aberto** - um dos 8 fios nao tem contato
- **Par em curto** - dois fios do mesmo par se tocando
- **Par invertido** - pinos 1 e 2 trocados entre si
- **Crimpagem fora do padrao** - cores que nao formam par nenhum

Um cabo com todos os 8 pinos ligados pode estar com o par 1 e o par 3
invertidos. Continua "funcionando" numa ponta, e falha do outro lado do switch.

### 2. Split pair - o defeito que engana

Nos pinos 1 e 2 do T568B vai branco/laranja e laranja. Sao o **mesmo par**: as
duas pernas da mesma dupla trancada.

Se a crimpagem nao respectar os pares e colocar um fio no pino 1 e o parceiro no
pino 4, os dois ainda tem continuidade: o teste 1 passa. Mas sao agora dois
fios soltos dentro da mesma tranca, cada um vizinho de um par diferente. O
acoplamento sobe, o NEXT desaba, e o cabo reprova em 100 MHz numa bancada.

**E por isso que "o teste de continuidade passou" nao significa nada isolado.** O
cabo so e aceito com o mapa E os parametros eletricos.

### 3. Parametros eletricos

| Parametro | O que mede | Direcao |
|---|---|---|
| Atenuacao (insertion loss) | Quanto o sinal perde no caminho | teto, menor e melhor |
| NEXT | Vazamento de um par para o vizinho | piso, maior e melhor |
| PS-NEXT | NEXT depois de passar pelo ruido do vizinho | piso, maior e melhor |
| Resistencia | Continuidade real do condutor | teto |
| Delay skew | Diferenca de propagacao entre os pares | teto |

Atenuacao e NEXT sao medidos **em varias frequencias**, nao so em 100 MHz. NEXT
cai com a frequencia: um par que isola bem a 100 MHz vaza mais a 250 MHz. Por
isso um cabo so pode ser aprovado se passa em **todas** as frequencias da sua
categoria.

## Por que o limite cai com a frequencia

Atenuacao cresce com o comprimento de onda. Em 100 MHz o sinal e lento o bastante
para "pendurar" no condutor. Em 500 MHz, nao. E por isso que a norma define
20,7 dB em 100 MHz e 26,6 dB em 250 MHz para o **mesmo** cabo.

O erro classico e comparar o cabo inteiro contra o limite de 100 MHz e concluir
que "sobrou folga". Sobrou para 100 MHz. Em 250 MHz a conta fecha diferente.

## O que este repositorio faz e nao faz

**Faz:** aplica os limites da ISO/IEC 11801 a uma medicao simulada por padrao
estatistico com semente fixa, e emite o laudo com o limite estourado nomeado.

**Nao faz:** medir. Nao existe sensor, nem aquisicao, nem amostra real. Todo
numero aqui sai de uma distribuicao normal com desvio pequeno, escolhida de
propósito: um simulador que adiciona 3 dB de ruido esconderia justamente o
defeito que o laudo deveria apontar.

O valor do repositorio esta em duas coisas:

1. **Aplicar as regras sem errar o lado do limite.** NEXT e piso, atenuacao e
   teto. Confundir as duas direcoes faz o laudo reprovar cabo bom - e falha
   silenciosa, do tipo que so aparece quando o cliente reclama.
2. **Ensinar a ler o laudo**, inclusive a recusar um laudo incompleto.

## Semente fixa: por que

A medicao usa `random.Random(f"{semente}-{nome}")`. Com semente fixa, a mesma
entrada devolve sempre os mesmos numeros. Isso e o que permite:

- **teste de regressao** - se o laudo mudar, mudou o codigo, nao o dado
- **exemplo reproduzivel** - o README pode colar a saida real sem mentir
- **auditoria** - da para conferir cada numero a conta

O ruido existe e e pequeno (0,3 dB na atenuacao, 0,4 dB no NEXT) porque um
certificador real tem dispersao parecida. Com ruido grande, a falha plantada se
misturaria com a variacao normal e o teste deixaria de provar.

## Limite de 90 m

Nao existe categoria que salve um cabo de 105 m. Acima de 90 m de cabo no canal,
o sinal ja saiu do que a norma cobre, e o `certsim` reprova **antes** de calcular
perda - porque o resultado seria enganoso. Um numero que reprova por 3 dB de
atenuacao sugere "trocar o cabo". A verdade e "isso nao existe": tem que usar
repetidor, fibra ou outro caminho.