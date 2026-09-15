# NFL and Poker 2026

Ranking semana a semana da liga de fantasy NFL (Yahoo Daily Fantasy, liga 154304).

Página única, sem dependências: todo o conteúdo está em `index.html`.

## Premiação

| Semanal (14 × R$ 30 = R$ 420) | | Geral (14 × R$ 150 = R$ 2.100) | |
|---|---|---|---|
| 1º | R$ 170 (lucro R$ 140) | 1º | R$ 1.000 |
| 2º | R$ 110 (lucro R$ 80)  | 2º | R$ 550 |
| 3º | R$ 80 (lucro R$ 50)   | 3º | R$ 250 |
| 4º | R$ 30 (freeroll)      | 4º | R$ 150 |
| 5º | R$ 30 (freeroll)      | 5º | R$ 150 |

A classificação geral soma os pontos de todas as semanas.

## Como adicionar uma semana

No bloco `WEEKS` dentro de `index.html`, copie um objeto de semana e preencha:

```js
{ n:2, label:"Semana 2", results:[ ["Time", 123.45], ... ],
  lineups:{ best:{ owner:"...", slots:[{slot:"QB", name:"...", team:"...", sal:0, pts:0}, ...] },
            optimal:{ slots:[...] } },
  tops:{ QB:[{name,team,sal,pts}, ...], RB:[...], WR:[...], TE:[...], DEF:[...] } }
```

Posição, prêmio, lucro, caixa e a aba Geral são calculados sozinhos. Os blocos
`lineups` e `tops` são opcionais — sem eles, as abas correspondentes não aparecem.

## De onde vêm os dados

- Classificação e pontuação: tela de Standings do Yahoo.
- Salário e pontuação de cada jogador: API pública do Yahoo DFS
  (`dfyql-ro.sports.yahoo.com/v2/seriesPlayers?seriesId=...`), onde
  `fantasyPointsHistory[0]` traz os pontos da rodada encerrada.
- Melhor time possível: maior pontuação que cabe no teto salarial de 200,
  resolvido como um problema de mochila sobre o pool da rodada.
