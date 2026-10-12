#!/usr/bin/env python3
"""
Gera uma página HTML interativa (redes.html) com as duas redes de relações:

  Rede 1  prologuistas -> autores/as de livros individuais
  Rede 2  autores/as de livros individuais -- editoras (pelo nome normalizado)

Uso:
    python3 redes_html.py Export_livpoesia.json [pasta_saida]

A página não depende de nada externo: os dados e a disposição dos nós vão
dentro do ficheiro, que se abre diretamente no navegador. A disposição é
calculada aqui (algoritmo de Fruchterman-Reingold, com numpy) e fica fixa; os
filtros da página só escondem ou mostram ligações.

As regras de construção das redes são as de redes.py (livro individual = uma
pessoa em Autoria; papel de prologuista lido no registo de relação ou nos
campos MARC). A diferença é que aqui as editoras se agrupam pelo campo «Nome
normalizado».
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))  # necessário com python -I
from redes import (F_ANO, F_AUTORIA, F_ED_NOME, F_ED_NORMALIZADO, F_EDITORA, F_ETIQUETA, F_GENERO,  # noqa: E402
                   F_LINGUA_FONTE, F_MARC, F_MORTE, F_NASC, F_NATUREZA, F_NOME_COMPLETO, F_TITULO,
                   F_TRADUCAO, F_VARIANTES, FUNCOES_PROLOGO, R_FUNCAO, R_LIVRO, R_PESSOA, papel_marc,
                   rotulos, sem_acentos, valores)


def disposicao(n, arestas, atracao=1.0, iteracoes=500, semente=7):
    """Disposição por forças, ao estilo do ForceAtlas 2. arestas: lista de (i, j, peso).

    Repulsão proporcional ao grau dos nós (afasta os nós muito ligados uns dos
    outros), atração linear nas ligações e gravidade forte, para que os
    componentes soltos não fujam para longe. Com «atracao» menor, as ligações
    ficam mais compridas (útil em redes de pares soltos). Devolve coordenadas n x 2.
    """
    rng = np.random.default_rng(semente)
    pos = rng.uniform(-1, 1, (n, 2)).astype(np.float32) * np.sqrt(n) * 10
    if n < 2:
        return pos
    ai = np.array([a[0] for a in arestas], dtype=int)
    aj = np.array([a[1] for a in arestas], dtype=int)
    aw = np.log1p(np.array([a[2] for a in arestas], dtype=np.float32))
    massa = np.ones(n, dtype=np.float32)
    np.add.at(massa, ai, 1)
    np.add.at(massa, aj, 1)
    mm = np.outer(massa, massa)
    for it in range(iteracoes):
        dx = pos[:, 0][:, None] - pos[:, 0][None, :]
        dy = pos[:, 1][:, None] - pos[:, 1][None, :]
        fator = 10.0 * mm / (dx * dx + dy * dy + 0.01)               # repulsão ~ massas / distância
        forca = np.stack([(dx * fator).sum(1), (dy * fator).sum(1)], axis=1)
        d = (pos[ai] - pos[aj]) * aw[:, None] * atracao              # atração linear
        np.add.at(forca, ai, -d)
        np.add.at(forca, aj, d)
        raio = np.sqrt((pos ** 2).sum(1, keepdims=True)) + 1e-6
        forca -= pos / raio * massa[:, None] * 2.0                   # gravidade forte
        passo = 6.0 * (1 - it / iteracoes) ** 1.5 + 0.05
        norma = np.sqrt((forca ** 2).sum(1, keepdims=True)) + 1e-6
        pos += forca / norma * np.minimum(norma / massa[:, None] * 0.5, passo)
    pos -= pos.mean(0)
    # escala pelo percentil 98, para que uns poucos nós afastados não encolham o resto
    limite = np.percentile(np.abs(pos), 98)
    return np.clip(pos / limite, -1.15, 1.15) * 900


def construir(caminho):
    with open(caminho, encoding="utf-8") as f:
        recs = json.load(f)["heurist"]["records"]
    por_id = {r["rec_ID"]: r for r in recs}

    etiquetas, livros, marc = [], {}, {}
    for r in recs:
        if r["rec_RecTypeName"] != "Livro":
            continue
        tags = []
        for t in sorted(str(v) for v in valores(r, F_ETIQUETA)):
            if t not in etiquetas:
                etiquetas.append(t)
            tags.append(etiquetas.index(t))
        eds = []
        for v in valores(r, F_EDITORA):
            e = por_id[v["id"]]
            eds.append(str((valores(e, F_ED_NORMALIZADO) or valores(e, F_ED_NOME) or [e["rec_Title"]])[0]))
        livros[r["rec_ID"]] = {
            "autores": [v["id"] for v in valores(r, F_AUTORIA)], "editoras": sorted(set(eds)),
            "dados": [r["rec_ID"], str((valores(r, F_TITULO) or [""])[0]), (valores(r, F_ANO) or [0])[0],
                      1 if (rotulos(r, F_TRADUCAO) or [""])[0] == "sim" else 0, tags,
                      (rotulos(r, F_NATUREZA) or [""])[0], (rotulos(r, F_LINGUA_FONTE) or [""])[0]],
        }
        marc[r["rec_ID"]] = sem_acentos(" || ".join(str(v) for dty in F_MARC for v in valores(r, dty)))
    individuais = [lid for lid, l in livros.items() if len(l["autores"]) == 1]

    def no_pessoa(pid):
        r = por_id[pid]
        return {"id": "P" + pid, "n": str((valores(r, F_NOME_COMPLETO) or [r["rec_Title"]])[0]), "t": "p",
                "g": (rotulos(r, F_GENERO) or [""])[0], "a": str((valores(r, F_NASC) or [""])[0])[:4],
                "m": str((valores(r, F_MORTE) or [""])[0])[:4]}

    # índice de livros partilhado pelas duas redes
    ordem = sorted(individuais, key=int)
    indice_livro = {lid: i for i, lid in enumerate(ordem)}

    # Rede 1: (prologuista, autor/a, livro)
    prologos = set()
    for r in recs:
        if r["rec_RecTypeName"] != "Record relationship":
            continue
        d = {x["dty_ID"]: x for x in r["details"]}
        if R_PESSOA not in d or R_LIVRO not in d:
            continue
        pid, lid = d[R_PESSOA]["value"]["id"], d[R_LIVRO]["value"]["id"]
        if lid not in indice_livro or pid not in por_id or pid in livros[lid]["autores"]:
            continue
        funcao = d.get(R_FUNCAO, {}).get("termLabel") or "nd"
        if funcao == "nd":
            nomes = [str(v) for v in valores(por_id[pid], F_NOME_COMPLETO) + valores(por_id[pid], F_VARIANTES)]
            funcao = papel_marc(nomes, marc[lid])[0]
        if funcao in FUNCOES_PROLOGO or funcao == "prologuista":
            prologos.add((pid, livros[lid]["autores"][0], lid))

    def montar(triplos, nos_de, atracao):
        """triplos: (origem, destino, livro) com chaves de nó; devolve nós com posição e linhas."""
        chaves = sorted({x for o, d, _ in triplos for x in (o, d)})
        idx = {c: i for i, c in enumerate(chaves)}
        pesos = defaultdict(int)
        for o, d, _ in triplos:
            pesos[(idx[o], idx[d])] += 1
        pos = disposicao(len(chaves), [(i, j, w) for (i, j), w in pesos.items()], atracao)
        nos = []
        for c in chaves:
            no = nos_de(c)
            no["x"], no["y"] = round(float(pos[idx[c]][0]), 1), round(float(pos[idx[c]][1]), 1)
            nos.append(no)
        linhas = sorted([idx[o], idx[d], indice_livro[l]] for o, d, l in triplos)
        return {"nos": nos, "linhas": linhas}

    rede1 = montar([("P" + p, "P" + a, l) for p, a, l in prologos], lambda c: no_pessoa(c[1:]), 0.2)
    triplos2 = [("P" + livros[l]["autores"][0], "E" + e, l) for l in ordem for e in livros[l]["editoras"]]
    rede2 = montar(triplos2, lambda c: no_pessoa(c[1:]) if c[0] == "P" else {"id": c, "n": c[1:], "t": "e"}, 1.0)
    return {"etiquetas": etiquetas, "livros": [livros[l]["dados"] for l in ordem], "rede1": rede1, "rede2": rede2}


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    saida = Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    dados = construir(sys.argv[1])
    modelo = (Path(__file__).resolve().parent / "redes_modelo.html").read_text(encoding="utf-8")
    json_dados = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (saida / "redes.html").write_text(modelo.replace("/*DADOS*/null", json_dados), encoding="utf-8")
    for nome in ("rede1", "rede2"):
        r = dados[nome]
        print(f"{nome}: {len(r['nos'])} nós, {len({(a, b) for a, b, _ in r['linhas']})} ligações, "
              f"{len(r['linhas'])} linhas por livro")
    print("editoras (nome normalizado):", sum(1 for n in dados["rede2"]["nos"] if n["t"] == "e"))


if __name__ == "__main__":
    main()
