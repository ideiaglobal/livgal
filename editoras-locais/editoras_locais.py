#!/usr/bin/env python3
"""Associa a cada Editora o(s) Local(is) de publicaçom dos seus livros.

Uso: python3 -I editoras_locais.py <livro.csv> <editora.csv> <local.csv> <pasta_saida>

Entradas: exportações CSV do Heurist (UTF-8 com BOM, separador TAB, valores
múltiplos separados por '|').

Saídas:
  editoras-com-local.csv      o ficheiro de editoras com duas colunas novas
                              (Local H-ID, Local nome); só as editoras com um
                              único local ficam preenchidas
  editoras-varios-locais.csv  editoras com mais de um local, para rever

Tipos de evidência, por ordem de confiança:
  1. direta    livro com uma só editora: os locais do livro som da editora
  2. coediçom  livro com várias editoras e um só local: o local vale para todas
  3. ambígua   livro com várias editoras e vários locais: nom se sabe que local
               corresponde a que editora (a ordem das colunas nom é fiável)
Para cada editora usa-se só o nível mais fiável que tiver.
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

SEP = "|"
NIVEIS = ["direta", "coediçom", "ambígua"]


def ler(caminho):
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f, delimiter="\t"))


def campo(valor):
    """Escreve um campo como o Heurist: entre aspas se tiver espaços ou aspas."""
    valor = str(valor)
    if any(c in valor for c in ' "\t'):
        return '"' + valor.replace('"', '""') + '"'
    return valor


def partir(valor):
    return [v for v in valor.split(SEP) if v.strip()]


def main():
    livros, editoras, locais = ler(sys.argv[1]), ler(sys.argv[2]), ler(sys.argv[3])
    saida = Path(sys.argv[4])

    nome_local = {r[0]: r[1] for r in locais[1:]}
    nome_editora = {r[0]: r[1] for r in editoras[1:]}
    cab = livros[0]
    i_livro, i_ed, i_loc = cab.index("Livro H-ID"), cab.index("Editora H-ID"), cab.index("Local de publicação H-ID")

    # evidencia[nível][editora][local] = lista de H-ID de livros
    evidencia = {n: defaultdict(lambda: defaultdict(list)) for n in NIVEIS}
    for r in livros[1:]:
        eds, locs = partir(r[i_ed]), partir(r[i_loc])
        desconhecidos = [x for x in eds if x not in nome_editora] + [x for x in locs if x not in nome_local]
        if desconhecidos:
            raise SystemExit(f"Livro {r[i_livro]}: H-ID sem correspondência {desconhecidos}")
        if not eds or not locs:
            continue
        nivel = "direta" if len(eds) == 1 else ("coediçom" if len(locs) == 1 else "ambígua")
        for e in eds:
            for l in locs:
                evidencia[nivel][e][l].append(r[i_livro])

    # para cada editora: nível usado e locais ordenados por n.º de livros
    resultado = {}
    for e in nome_editora:
        for nivel in NIVEIS:
            if e in evidencia[nivel]:
                locs = evidencia[nivel][e]
                ordem = sorted(locs, key=lambda l: (-len(locs[l]), nome_local[l]))
                resultado[e] = (nivel, ordem, locs)
                break

    def unico(e):
        return e in resultado and resultado[e][0] != "ambígua" and len(resultado[e][1]) == 1

    # 1. ficheiro de editoras com as colunas novas (mesma ordem e formato do original)
    with open(saida / "editoras-com-local.csv", "w", encoding="utf-8-sig", newline="") as f:
        f.write("\t".join(campo(c) for c in editoras[0] + ["Local H-ID", "Local nome"]) + "\n")
        for r in editoras[1:]:
            l = resultado[r[0]][1][0] if unico(r[0]) else ""
            f.write("\t".join(campo(c) for c in r + [l, nome_local.get(l, "")]) + "\n")

    # 2. editoras com vários locais (ou só com evidência ambígua), para rever
    cab2 = ["Editora H-ID", "Full name of organisation", "Local H-ID (todos)", "Local nome (todos)",
            "Local H-ID (mais frequente)", "Local nome (mais frequente)", "N.º de livros por local",
            "Tipo de evidência", "Livros H-ID por local"]
    with open(saida / "editoras-varios-locais.csv", "w", encoding="utf-8-sig", newline="") as f:
        f.write("\t".join(campo(c) for c in cab2) + "\n")
        for r in editoras[1:]:
            e = r[0]
            if e not in resultado or unico(e):
                continue
            nivel, ordem, locs = resultado[e]
            n = [len(locs[l]) for l in ordem]
            empate = len(n) > 1 and n[0] == n[1]
            linha = [
                e, r[1],
                SEP.join(ordem), SEP.join(nome_local[l] for l in ordem),
                "" if empate else ordem[0], "" if empate else nome_local[ordem[0]],
                SEP.join(f"{nome_local[l]}: {len(locs[l])}" for l in ordem),
                nivel,
                SEP.join(f"{nome_local[l]}: {', '.join(locs[l][:15])}{' …' if len(locs[l]) > 15 else ''}" for l in ordem),
            ]
            f.write("\t".join(campo(c) for c in linha) + "\n")

    # resumo
    c = Counter()
    for e in nome_editora:
        if e not in resultado:
            c["sem local"] += 1
        elif unico(e):
            c[f"um local ({resultado[e][0]})"] += 1
        else:
            c[f"vários locais ({resultado[e][0]})"] += 1
    for k, v in sorted(c.items()):
        print(f"{v:4d}  {k}")
    print("sem local:", [nome_editora[e] for e in nome_editora if e not in resultado])


if __name__ == "__main__":
    main()
