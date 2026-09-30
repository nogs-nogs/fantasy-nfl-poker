#!/usr/bin/env python3
"""
Levanta uma rodada da liga de fantasy NFL (Yahoo Daily Fantasy) e gera o bloco
de dados da página de ranking.

O que faz, a partir de um contestId:
  1. baixa o pool oficial do contest (salário + pontuação real de cada jogador)
  2. baixa a classificação da rodada (as 14 inscrições, com pontos e posição)
  3. resolve o TIME PERFEITO — a maior pontuação que cabe no teto salarial
  4. lista os 3 melhores de cada posição
  5. imprime (ou aplica) o bloco JavaScript da semana para o index.html

Só usa a biblioteca padrão do Python 3. Sem pip, sem chave de API, sem login
para os passos 1 a 5 — os dois endpoints usados são públicos.

USO TÍPICO
    python3 fantasy_round.py --contest 15807394 --week 3
    python3 fantasy_round.py --contest 15807394 --week 3 \
        --lineup-file rodada3.txt --patch ../index.html

COMO DESCOBRIR O contestId (único passo que exige login)
    Abra https://sports.yahoo.com/dailyfantasy/league/<LIGA>/<ENTRY> logado,
    clique na linha da rodada na tabela "Performance" e leia a URL:
    .../dailyfantasy/contest/<contestId>/<entryId>
    Os ids NÃO são sequenciais entre rodadas — não tente adivinhar.

COMO PEGAR A ESCALAÇÃO DO CAMPEÃO (opcional, também exige login)
    Abra .../dailyfantasy/contest/<contestId>/<entryId-do-1º-lugar>,
    copie o texto da página inteira para um arquivo e passe em --lineup-file.
    O parser entende o formato da página. Alternativa manual:
    --lineup "QB:Kyler Murray;RB:Bijan Robinson;RB:Jahmyr Gibbs;..."

REGRAS DA MODALIDADE (Yahoo Daily Fantasy NFL)
    Escalação: QB, RB, RB, WR, WR, WR, TE, FLEX (RB/WR/TE), DEF — 9 vagas.
    Teto salarial: 200.
"""

import argparse, json, re, sys, urllib.request, urllib.error

API = "https://dfyql-ro.sports.yahoo.com/v2"
QS = "lang=en-US&region=US&device=desktop"
CAP = 200
SLOTS = ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "DEF"]
# o Yahoo usa siglas próprias para três times; normalizamos para exibição
TEAM_FIX = {"LA": "LAR", "JAC": "JAX"}


def fetch(path):
    url = f"{API}/{path}{'&' if '?' in path else '?'}{QS}"
    req = urllib.request.Request(url, headers={"User-Agent": "fantasy-round/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"ERRO {e.code} ao chamar {url}\n"
                 f"Se for 404, confira o contestId.")


def get_pool(contest_id):
    """Jogadores do contest: nome, posição, time, salário e pontuação REAL."""
    data = fetch(f"contestPlayers?contestId={contest_id}")
    out = []
    for p in data["players"]["result"]:
        team = (p.get("team") or {}).get("abbr")
        out.append({
            "name": f"{p['firstName']} {p['lastName']}",
            "pos": p.get("primaryPosition"),
            "team": TEAM_FIX.get(team, team),
            "sal": p["salary"],
            "pts": round(p.get("points") or 0.0, 2),
        })
    if not out:
        sys.exit("Pool vazio — contest inexistente ou ainda não liberado.")
    return out


def get_standings(contest_id):
    """Classificação da rodada. 'score' é o total do time; 'rank' já vem pronto."""
    data = fetch(f"contestEntries?contestId={contest_id}")
    rows = [{"team": e["user"]["nickname"], "pts": round(e["score"], 2),
             "rank": e["rank"], "entryId": e["id"]}
            for e in data["entries"]["result"]]
    return sorted(rows, key=lambda r: r["rank"])


def best_lineup(pool):
    """
    Time perfeito: maximiza pontos com salário <= CAP, respeitando as vagas.
    Programação dinâmica por posição sobre o salário (mochila 0/1), depois
    combina as posições. O FLEX é tratado como uma vaga extra de RB, WR ou TE —
    testamos as três hipóteses e ficamos com a melhor.
    """
    NEG = float("-inf")
    by = {k: [p for p in pool if p["pos"] == k] for k in ("QB", "RB", "WR", "TE", "DEF")}

    def group(players, maxk):
        # f[k][s] = (melhor pontuação com k jogadores custando s, escalação)
        f = [[(NEG, ())] * (CAP + 1) for _ in range(maxk + 1)]
        f[0][0] = (0.0, ())
        for pl in players:
            s0, p0 = pl["sal"], pl["pts"]
            if s0 > CAP:
                continue
            for k in range(maxk - 1, -1, -1):
                for s in range(CAP - s0, -1, -1):
                    v, lst = f[k][s]
                    if v == NEG:
                        continue
                    if v + p0 > f[k + 1][s + s0][0]:
                        f[k + 1][s + s0] = (v + p0, lst + (pl,))
        return f

    dp = {k: group(v, 4 if k in ("RB", "WR", "TE") else 1) for k, v in by.items()}
    best = (NEG, (), None)
    for flex in ("RB", "WR", "TE"):
        need = {"RB": 2, "WR": 3, "TE": 1}
        need[flex] += 1
        cur = [(NEG, ())] * (CAP + 1)
        cur[0] = (0.0, ())
        for pos, k in [("QB", 1), ("DEF", 1), ("RB", need["RB"]),
                       ("WR", need["WR"]), ("TE", need["TE"])]:
            nxt = [(NEG, ())] * (CAP + 1)
            g = dp[pos][k]
            for s1 in range(CAP + 1):
                v1, l1 = cur[s1]
                if v1 == NEG:
                    continue
                for s2 in range(CAP - s1 + 1):
                    v2, l2 = g[s2]
                    if v2 == NEG:
                        continue
                    if v1 + v2 > nxt[s1 + s2][0]:
                        nxt[s1 + s2] = (v1 + v2, l1 + l2)
            cur = nxt
        top = max(cur, key=lambda x: x[0])
        if top[0] > best[0]:
            best = (top[0], top[1], flex)
    pts, players, flex = best
    if not players:
        sys.exit("Não foi possível montar um time dentro do teto.")
    return assign_slots(list(players), flex), round(pts, 2)


def assign_slots(players, flex_pos):
    """Distribui os 9 jogadores nas vagas, mandando o pior do grupo para o FLEX."""
    out, by = [], {}
    for p in players:
        by.setdefault(p["pos"], []).append(p)
    for k in by:
        by[k].sort(key=lambda p: -p["pts"])
    flex_player = by[flex_pos].pop()          # o de menor pontuação vira FLEX
    for slot in ["QB", "RB", "RB", "WR", "WR", "WR", "TE"]:
        out.append(dict(by[slot].pop(0), slot=slot))
    out.append(dict(flex_player, slot="FLEX"))
    out.append(dict(by["DEF"].pop(0), slot="DEF"))
    return out


def tops(pool, n=3):
    """Melhores de cada posição. Empate é desempatado pelo salário mais barato."""
    res = {}
    for pos in ("QB", "RB", "WR", "TE", "DEF"):
        grp = [p for p in pool if p["pos"] == pos]
        grp.sort(key=lambda p: (-p["pts"], p["sal"]))
        res[pos] = grp[:n]
    return res


def parse_lineup_text(text, pool):
    """
    Lê a escalação a partir do texto copiado da página do contest.
    A página lista os jogadores como '14.3% Rostered <Nome>' na ordem das vagas,
    e logo depois um bloco 'Pos' com QB, RB, RB, WR... na mesma ordem.
    """
    names = re.findall(r"^[\d.]+%\s+Rostered\s+(.+?)\s*$", text, re.M)
    slots = re.findall(r"^(QB|RB|WR|TE|FLEX|DEF)\s*$", text, re.M)
    if not names:
        sys.exit("Não achei jogadores no texto (esperava linhas '% Rostered Nome').")
    if len(slots) >= len(names):
        slots = slots[:len(names)]
    else:
        slots = SLOTS[:len(names)]
    return match_players(list(zip(slots, names)), pool)


def parse_lineup_arg(arg, pool):
    pairs = []
    for part in arg.split(";"):
        part = part.strip()
        if not part:
            continue
        slot, _, name = part.partition(":")
        pairs.append((slot.strip().upper(), name.strip()))
    return match_players(pairs, pool)


def match_players(pairs, pool):
    index = {p["name"].lower(): p for p in pool}
    out = []
    for slot, name in pairs:
        p = index.get(name.lower())
        if p is None:                      # tenta por sobrenome, exigindo unicidade
            last = name.lower().split()[-1]
            cands = [q for q in pool if q["name"].lower().split()[-1] == last]
            if len(cands) != 1:
                sys.exit(f"Jogador ambíguo ou inexistente no pool: {name!r}")
            p = cands[0]
        out.append(dict(p, slot=slot))
    return out


def js_block(week, label, standings, best, optimal, top3):
    """Monta o objeto JavaScript da semana, no formato do index.html."""
    def slots(rows):
        return "\n".join(
            f'      {{slot:"{r["slot"]}", name:"{r["name"]}", team:"{r["team"]}", '
            f'sal:{r["sal"]}, pts:{r["pts"]:.2f}}}{"," if i < len(rows)-1 else ""}'
            for i, r in enumerate(rows))

    def plist(rows, pad):
        return (",\n" + " " * pad).join(
            f'{{name:"{r["name"]}", team:"{r["team"]}", sal:{r["sal"]}, pts:{r["pts"]:.2f}}}'
            for r in rows)

    res = "\n".join(f'    ["{r["team"]}", {r["pts"]:.2f}]{"," if i < len(standings)-1 else ""}'
                    for i, r in enumerate(standings))
    parts = [f'  {{ n:{week}, label:"{label}", results:[', res, "  ], lineups:{"]
    if best:
        parts += [f'    best:{{ owner:"{best[0]}", slots:[', slots(best[1]), "    ]},"]
    parts += ["    optimal:{ slots:[", slots(optimal), "    ]}", "  }, tops:{"]
    parts += [f"    {pos}:[ " + plist(top3[pos], 9) + " ]" + ("," if pos != "DEF" else "")
              for pos in ("QB", "RB", "WR", "TE", "DEF")]
    parts.append("  }}")
    return "\n".join(parts)


def patch_html(path, week, block):
    """Insere (ou substitui) o objeto da semana dentro do array WEEKS."""
    src = open(path, encoding="utf-8").read()
    start = src.index("const WEEKS = [")
    end = src.index("\n];", start)
    body = src[start:end]
    marker = f"{{ n:{week},"
    if marker in body:                      # já existe: troca o objeto inteiro
        i = body.index(marker)
        i = body.rindex("\n", 0, i)
        depth, j = 0, body.index(marker)
        while True:                         # anda até fechar as chaves
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        new_body = body[:i] + "\n" + block + body[j + 1:]
        action = "substituída"
    else:
        new_body = body + ",\n" + block
        action = "adicionada"
    open(path, "w", encoding="utf-8").write(src[:start] + new_body + src[end:])
    return action


def main():
    ap = argparse.ArgumentParser(
        description="Levanta uma rodada do fantasy e gera o bloco da página.")
    ap.add_argument("--contest", required=True, help="contestId da rodada")
    ap.add_argument("--week", type=int, required=True, help="número da rodada")
    ap.add_argument("--label", help='rótulo (padrão: "Semana <n>")')
    ap.add_argument("--lineup-file", help="texto da página do campeão")
    ap.add_argument("--lineup", help='"QB:Nome;RB:Nome;..." como alternativa')
    ap.add_argument("--patch", help="caminho do index.html para atualizar")
    ap.add_argument("--json", help="salva o resultado bruto em JSON")
    a = ap.parse_args()
    label = a.label or f"Semana {a.week}"

    pool = get_pool(a.contest)
    standings = get_standings(a.contest)
    optimal, opt_pts = best_lineup(pool)
    top3 = tops(pool)

    best = None
    if a.lineup_file or a.lineup:
        text = open(a.lineup_file, encoding="utf-8").read() if a.lineup_file else None
        rows = parse_lineup_text(text, pool) if text else parse_lineup_arg(a.lineup, pool)
        best = (standings[0]["team"], rows)
        soma = round(sum(r["pts"] for r in rows), 2)
        sal = sum(r["sal"] for r in rows)
        if abs(soma - standings[0]["pts"]) > 0.01:
            print(f"  ATENÇÃO: a escalação soma {soma}, mas o campeão pontuou "
                  f"{standings[0]['pts']}. Confira se é o time certo.", file=sys.stderr)
        if sal > CAP:
            print(f"  ATENÇÃO: escalação custa {sal}, acima do teto {CAP}.", file=sys.stderr)

    print(f"== {label} — {len(standings)} times, pool de {len(pool)} jogadores ==\n")
    print("CLASSIFICAÇÃO")
    for r in standings:
        print(f"  {r['rank']:2} {r['team']:22} {r['pts']:7.2f}")
    if best:
        print(f"\nMELHOR ESCALADO — {best[0]} "
              f"({sum(r['sal'] for r in best[1])} de salário)")
        for r in best[1]:
            print(f"  {r['slot']:4} {r['name']:24} {r['team']:4} "
                  f"sal={r['sal']:3} pts={r['pts']:6.2f}")
    print(f"\nTIME PERFEITO — {opt_pts} pts, "
          f"{sum(r['sal'] for r in optimal)} de salário")
    for r in optimal:
        print(f"  {r['slot']:4} {r['name']:24} {r['team']:4} "
              f"sal={r['sal']:3} pts={r['pts']:6.2f}")
    print("\nMELHORES POR POSIÇÃO")
    for pos in ("QB", "RB", "WR", "TE", "DEF"):
        for i, r in enumerate(top3[pos], 1):
            print(f"  {pos:4} {i}º {r['name']:24} {r['team']:4} "
                  f"sal={r['sal']:3} pts={r['pts']:6.2f}")

    block = js_block(a.week, label, standings, best, optimal, top3)
    if a.json:
        json.dump({"week": a.week, "label": label, "standings": standings,
                   "best": best[1] if best else None, "optimal": optimal,
                   "optimalPoints": opt_pts, "tops": top3},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\nJSON salvo em {a.json}")
    if a.patch:
        print(f"\nSemana {a.week} {patch_html(a.patch, a.week, block)} em {a.patch}")
    else:
        print("\n--- bloco para colar em WEEKS no index.html ---")
        print(block)


if __name__ == "__main__":
    main()
