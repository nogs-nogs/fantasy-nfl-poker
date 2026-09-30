# Mensagem pronta para a próxima IA

Copie o bloco abaixo, preencha o número da rodada e o `contestId`, e mande.
Nada mais é necessário: o runbook, o script e as armadilhas conhecidas estão
todos no repositório.

---

> Preciso atualizar o ranking da minha liga de fantasy NFL. Está tudo neste
> repositório público:
>
> **https://github.com/nogs-nogs/fantasy-nfl-poker**
>
> Comece lendo `tools/README.md` — é o runbook completo, com as armadilhas que
> já custaram retrabalho. O cálculo inteiro já está resolvido em
> `tools/fantasy_round.py` (Python 3, sem dependências): ele baixa o pool e a
> classificação da rodada por dois endpoints públicos do Yahoo, resolve o time
> perfeito sob o teto salarial, lista os melhores por posição e atualiza a
> página.
>
> Rodada a levantar: **Rodada N**
> contestId: **XXXXXXXX**
> Escalação do campeão: segue em anexo / colada abaixo.
>
> O que eu espero de volta: a página `index.html` atualizada e publicada
> (`git push` — o GitHub Pages republica sozinho). Se você não tiver terminal,
> me devolva o bloco JavaScript da semana que eu colo e publico.
>
> Antes de publicar, confira os dois avisos que o script emite: a escalação do
> campeão precisa somar exatamente o `score` dele e caber em 200 de salário.

---

## O que só você consegue obter (exige login no Yahoo)

Estes dois itens nenhuma IA pega sozinha — a liga é privada.

1. **O `contestId` da rodada.** Abra
   `https://sports.yahoo.com/dailyfantasy/league/154304/8486967`, clique na
   linha da rodada na tabela "Performance", e copie o número do meio da URL:
   `.../dailyfantasy/contest/<contestId>/<entryId>`.

2. **A escalação do campeão.** Abra
   `.../dailyfantasy/contest/<contestId>/<entryId-do-1º>` e copie o texto
   inteiro da página para um arquivo. O parser do script entende o formato
   cru — não precisa limpar nada. (O `entryId` de cada participante sai na
   primeira execução do script.)

   Esse item é opcional: sem ele a rodada entra completa, só sem a aba
   "Melhor escalado".

## Três cenários, conforme a IA

| A IA tem… | Como fica |
|---|---|
| terminal na sua máquina | Manda o link e os dois itens acima. Ela clona, roda o script, dá push. Trabalho seu: zero. |
| internet, mas sem terminal | Mesma mensagem. Ela consulta os dois endpoints do README, devolve o bloco JavaScript, você cola no `index.html` e dá push. |
| nem uma coisa nem outra | Você mesmo roda: `python3 tools/fantasy_round.py --contest <id> --week <n> --lineup-file <arquivo> --patch ../index.html` e depois `git push`. Chame a IA só se algo quebrar. |

## Se o push falhar com 403

A conta ativa do `gh` voltou para a de trabalho. Resolve com:

```bash
gh auth switch --user nogs-nogs
```
