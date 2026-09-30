# Como levantar uma rodada

> Vai pedir isso para uma IA? A mensagem pronta está em
> [PROMPT-INICIAL.md](PROMPT-INICIAL.md).

Runbook para atualizar o ranking depois que uma rodada termina. Escrito para
ser seguido por qualquer pessoa — ou por qualquer assistente de IA com acesso a
um terminal. Não depende de nenhum serviço além do próprio Yahoo.

**Requisitos:** Python 3 (só biblioteca padrão) e internet. Nada para instalar.

---

## Contexto em um parágrafo

Liga de fantasy NFL no Yahoo Daily Fantasy, 14 amigos, 18 rodadas. Cada rodada é
um contest independente: você monta 9 jogadores (QB, RB, RB, WR, WR, WR, TE,
FLEX, DEF) com um teto de **200 de salário**. A página
`index.html` mostra, por rodada, a classificação, a escalação campeã, o **time
perfeito** (a maior pontuação que caberia no teto) e os 3 melhores de cada
posição. O script faz todo esse cálculo.

---

## Passo 1 — descobrir o `contestId` da rodada  (exige login)

1. Abra, logado no Yahoo, a página da liga:
   `https://sports.yahoo.com/dailyfantasy/league/154304/8486967`
2. Na tabela **Performance**, clique na linha da rodada desejada.
   Ela não é um link HTML, é uma `div` com handler — se estiver automatizando,
   clique por coordenada.
3. A URL vira `.../dailyfantasy/contest/<contestId>/<entryId>`. O primeiro
   número é o que você quer.

⚠ Os ids **não são sequenciais** entre rodadas. Já observados:
R1 `15760298`, R2 `15789052`, R3 `15807394`. Não tente adivinhar o próximo.

## Passo 2 — copiar a escalação do campeão  (opcional, exige login)

O Yahoo não expõe escalações por API pública; só a página logada mostra.

1. Rode o script sem `--lineup-file` uma vez para ver quem venceu.
2. Volte à página da liga, clique na rodada, e no ranking do contest clique no
   nome do campeão — ou monte a URL direto:
   `.../dailyfantasy/contest/<contestId>/<entryId-do-campeão>`
   (o `entryId` de cada um aparece na saída do script).
3. Copie o **texto inteiro da página** para um arquivo, por exemplo `r4.txt`.
   Não precisa limpar nada: o parser procura as linhas `12.3% Rostered <Nome>`
   e o bloco de posições logo abaixo.

Sem esse passo o script ainda funciona — a aba "Melhor escalado" é que não
aparece naquela rodada.

## Passo 3 — rodar

```bash
cd tools

# só para ver a rodada
python3 fantasy_round.py --contest 15807394 --week 3

# completo, já atualizando a página
python3 fantasy_round.py --contest 15807394 --week 3 \
    --lineup-file r3.txt --patch ../index.html
```

Outras opções: `--label "Semana 3"` (rótulo exibido), `--json saida.json`
(dados crus), `--lineup "QB:Nome;RB:Nome;..."` (escalação na mão).

Rodar duas vezes a mesma semana é seguro: o bloco é substituído, não duplicado.

## Passo 4 — publicar

```bash
cd ..
git add -A && git commit -m "Semana 3" && git push
```

O GitHub Pages republica sozinho em cerca de um minuto, no mesmo endereço:
https://nogs-nogs.github.io/fantasy-nfl-poker/

⚠ Se o push der `403`, a conta ativa do `gh` é a errada:
`gh auth switch --user nogs-nogs`.

---

## O que o script calcula

**Time perfeito.** Um problema de mochila: maximizar pontos com salário ≤ 200,
respeitando as vagas. Resolvido por programação dinâmica por posição sobre o
salário, testando as três hipóteses de FLEX (RB, WR ou TE). É exato, não é
heurística. Não confunda com "os mais pontuadores": o QB mais pontuador
frequentemente fica de fora porque custa caro demais.

**Melhores por posição.** Os 3 maiores de cada posição dentro do pool daquele
contest. Empate é desempatado pelo salário mais barato.

**Classificação.** Vem pronta do Yahoo, com `rank` e `score` por inscrição.

## De onde vêm os dados

Dois endpoints públicos, sem autenticação:

| endpoint | o que traz |
|---|---|
| `dfyql-ro.sports.yahoo.com/v2/contestPlayers?contestId=<id>` | pool do contest: nome, posição, time, **salário** e **pontuação real** |
| `dfyql-ro.sports.yahoo.com/v2/contestEntries?contestId=<id>` | as 14 inscrições: apelido, `rank`, `score`, `entryId` |

## Armadilhas já pagas (não repita)

- **Nunca use `fantasyPointsHistory[0]` como pontuação da rodada.** Esse campo é
  o último jogo que o *atleta* disputou, não a rodada. Quem não jogou carrega um
  placar antigo, e o otimizador escala um fantasma barato. Já aconteceu: um QB
  reserva com projeção de 1,04 apareceu com 28,86 e entrou no time perfeito.
  O campo `points` do `contestPlayers` é o correto.
- **Não reconstrua a pontuação a partir de boxscore de terceiros.** Foi tentado
  com o ESPN e erra em detalhes que só o Yahoo tem: conversão de 2 pontos,
  bloqueio de chute na defesa. Use o `points` oficial.
- **Não case jogadores só por sobrenome.** Kyle Allen herdou os pontos do Josh
  Allen assim. O script casa por nome completo e só recorre ao sobrenome quando
  o resultado é único.
- **Siglas de time.** O Yahoo usa `LA` (Rams) e `JAC` (Jaguars); o script
  normaliza para `LAR` e `JAX` na exibição.

## Conferências automáticas

O script avisa no `stderr` quando algo não fecha:

- a escalação do campeão tem que somar exatamente o `score` dele;
- e não pode passar de 200 de salário.

Se um desses avisos aparecer, provavelmente você copiou a página do jogador
errado. Vale conferir à mão antes de publicar.

## Premiação (para conferir os valores da página)

Semanal, 14 × R$ 30 = R$ 420 → 1º R$ 170, 2º R$ 110, 3º R$ 80, 4º e 5º R$ 30.
Geral, 14 × R$ 150 = R$ 2.100 → 1º R$ 1.000, 2º R$ 550, 3º R$ 250, 4º e 5º R$ 150.
A classificação geral é a **soma dos pontos** de todas as rodadas — confirmado
contra a "Overall Standings" do próprio Yahoo.
