#!/usr/bin/env python3
"""
Constrói duas redes de relações a partir da exportação JSON do Heurist
(livpoesia), usando as associações diretas de autoria dos livros e os registos
de relação (relationships):

  Rede 1  prologuistas -> autores/as de livros individuais
  Rede 2  autores/as de livros individuais -- editoras (pelo nome normalizado)

Uso:
    python3 -I redes.py Export_livpoesia.json [pasta_saida]

«Livro individual» = livro com exatamente uma pessoa no campo Autoria.
Na rede 2, as editoras agrupam-se pelo campo «Nome normalizado», de modo que
as variantes do mesmo selo contam como um só nó.

Para cada rede escrevem-se quatro ficheiros:
  *_nos.csv                nós (Id, Label e atributos), para Gephi ou folha de cálculo
  *_arestas.csv            arestas agregadas (Source, Target, Weight)
  *_arestas-por-livro.csv  uma linha por livro, com ano, etiquetas, tradução,
                           editora, etc., para filtrar antes de agregar
  *.gexf                   a rede completa num só ficheiro (abre em Gephi)

Papel de prologuista
  Vem do campo «Função» do registo de relação quando está preenchido. Como a
  maioria das relações tem a função «nd» (não definida), o script tenta lê-la
  nos campos MARC do livro: o código de função a seguir ao nome («Alvarez
  Cáccamo, Xosé María, 1950- , pr.») ou a menção de responsabilidade
  («prólogo, Xosé María Álvarez Cáccamo»). A coluna «Origem do papel» indica
  de onde veio.
"""
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import quoteattr

# dty_ID dos campos usados
F_AUTORIA, F_EDITORA, F_TITULO, F_ANO, F_ETIQUETA = 930, 950, 944, 952, 1009
F_TRADUCAO, F_LINGUA_FONTE, F_NATUREZA, F_MARC = 994, 995, 999, (946, 977)
F_NOME_COMPLETO, F_VARIANTES, F_GENERO, F_NASC, F_MORTE = 990, 991, 20, 1028, 1027
F_ED_NOME, F_ED_NORMALIZADO, F_ED_INICIO, F_ED_FIM = 1, 1038, 10, 11
R_PESSOA, R_FUNCAO, R_LIVRO = 5, 6, 7

FUNCOES_PROLOGO = {"prologuista", "introduçom"}

# códigos e designações de função nos campos MARC -> papel
CODIGOS = {
    "pr": "prologuista", "prol": "prologuista", "prologuista": "prologuista", "aui": "prologuista",
    "win": "prologuista", "introd": "prologuista", "aft": "epiloguista", "epil": "epiloguista",
    "il": "ilustrador/a", "ill": "ilustrador/a", "ilustrador": "ilustrador/a",
    "trad": "tradutor/a", "trl": "tradutor/a", "traductor": "tradutor/a", "tradutor": "tradutor/a",
    "ed. lit": "editor/a", "ed": "editor/a", "edt": "editor/a", "editor literario": "editor/a",
    "editor": "editor/a", "fot": "fotógrafo/a", "pht": "fotógrafo/a", "fotografo": "fotógrafo/a",
    "comp": "compilador/a", "com": "compilador/a", "compilador": "compilador/a", "sel": "compilador/a",
    "dir": "diretor/a", "director": "diretor/a", "pbd": "diretor/a",
    "coord": "coordenador/a", "coordinador": "coordenador/a",
    "col": "colaborador/a", "ctb": "colaborador/a", "aut": "autor/a", "autor": "autor/a",
}
RE_CODIGO = "(" + "|".join(sorted((re.escape(k) for k in CODIGOS), key=len, reverse=True)) + r")(?![a-z])"
RE_DATAS = r"(?:[\s,(]*\(?\s*(?:ca\.\s*)?\d{3,4}\??\s*-\s*(?:\d{3,4})?\??\s*\)?)?"
RE_FRASE = (r"(prologos?|limiar(?:es)?|introducion|introduccion|introducao|presentacion|prefacio|"
            r"estudo introdutorio|estudio introductorio|nota preliminar|palabras previas|epilogo|posfacio)")


def sem_acentos(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def ordem_direta(nome):
    """«Apelidos, Nome» -> «Nome Apelidos»."""
    if "," in nome:
        apelidos, proprio = nome.split(",", 1)
        return f"{proprio.strip()} {apelidos.strip()}"
    return nome


def valores(rec, dty):
    return [d["value"] for d in rec["details"] if d["dty_ID"] == dty]


def rotulos(rec, dty):
    return [d.get("termLabel", "") for d in rec["details"] if d["dty_ID"] == dty]


def papel_marc(nomes, texto):
    """Papel da pessoa segundo os campos MARC do livro: (papel, origem) ou (None, None)."""
    for n in nomes:
        m = re.search(re.escape(sem_acentos(n)) + RE_DATAS + r"[\s,.(]*" + RE_CODIGO, texto)
        if m:
            return CODIGOS[m.group(1)], "código MARC"
    for n in nomes:
        m = re.search(RE_FRASE + r"[^;\]|]{0,60}?" + re.escape(sem_acentos(ordem_direta(n))), texto)
        if m:
            fim = m.group(1) in ("epilogo", "posfacio")
            return ("epiloguista" if fim else "prologuista"), "menção de responsabilidade"
    return None, None


# --- escrita ----------------------------------------------------------------

def escrever_csv(caminho, cabecalho, linhas):
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(cabecalho)
        w.writerows(linhas)


def escrever_gexf(caminho, descricao, dirigida, cab_nos, nos, cab_arestas, arestas):
    """nos: linhas [Id, Label, atributos…]; arestas: linhas [Source, Target, Weight, atributos…]."""
    def tipo(coluna, linhas, i):
        return "integer" if all(isinstance(l[i], int) for l in linhas) else "string"

    with open(caminho, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<gexf xmlns="http://gexf.net/1.3" version="1.3">\n'
                f'<meta><creator>Projeto Livro Galego</creator><description>{descricao}</description></meta>\n'
                f'<graph mode="static" defaultedgetype="{"directed" if dirigida else "undirected"}">\n')
        for classe, cab, linhas, inicio in (("node", cab_nos, nos, 2), ("edge", cab_arestas, arestas, 3)):
            f.write(f'<attributes class="{classe}">\n')
            for i in range(inicio, len(cab)):
                f.write(f'<attribute id="{i}" title={quoteattr(cab[i])} type="{tipo(cab[i], linhas, i)}"/>\n')
            f.write("</attributes>\n")
        f.write("<nodes>\n")
        for l in nos:
            f.write(f"<node id={quoteattr(str(l[0]))} label={quoteattr(str(l[1]))}><attvalues>")
            f.write("".join(f'<attvalue for="{i}" value={quoteattr(str(l[i]))}/>'
                            for i in range(2, len(l)) if l[i] != ""))
            f.write("</attvalues></node>\n")
        f.write("</nodes>\n<edges>\n")
        for n, l in enumerate(arestas):
            f.write(f'<edge id="{n}" source={quoteattr(str(l[0]))} target={quoteattr(str(l[1]))} '
                    f'weight="{l[2]}"><attvalues>')
            f.write("".join(f'<attvalue for="{i}" value={quoteattr(str(l[i]))}/>'
                            for i in range(3, len(l)) if l[i] != ""))
            f.write("</attvalues></edge>\n")
        f.write("</edges>\n</graph>\n</gexf>\n")


# --- programa ---------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    saida = Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    with open(sys.argv[1], encoding="utf-8") as f:
        recs = json.load(f)["heurist"]["records"]
    por_id = {r["rec_ID"]: r for r in recs}

    def pessoa(pid):
        r = por_id[pid]
        return {
            "nome": str((valores(r, F_NOME_COMPLETO) or [r["rec_Title"]])[0]),
            "genero": (rotulos(r, F_GENERO) or [""])[0],
            "nasc": str((valores(r, F_NASC) or [""])[0])[:4], "morte": str((valores(r, F_MORTE) or [""])[0])[:4],
        }

    def editora(eid):
        r = por_id[eid]
        ini, fim = valores(r, F_ED_INICIO), valores(r, F_ED_FIM)
        return {
            "nome": str((valores(r, F_ED_NOME) or [r["rec_Title"]])[0]),
            "normalizado": str((valores(r, F_ED_NORMALIZADO) or [""])[0]),
            "inicio": min(ini) if ini else "", "fim": max(fim) if fim else "",
        }

    # livros
    livros = {}
    for r in recs:
        if r["rec_RecTypeName"] != "Livro":
            continue
        eds = [v["id"] for v in valores(r, F_EDITORA)]
        livros[r["rec_ID"]] = {
            "titulo": str((valores(r, F_TITULO) or [""])[0]),
            "ano": (valores(r, F_ANO) or [""])[0],
            "autores": [v["id"] for v in valores(r, F_AUTORIA)],
            "editoras": eds,
            "etiquetas": " | ".join(sorted(str(v) for v in valores(r, F_ETIQUETA))),
            "traducao": (rotulos(r, F_TRADUCAO) or ["não"])[0],
            "lingua_fonte": (rotulos(r, F_LINGUA_FONTE) or [""])[0],
            "natureza": (rotulos(r, F_NATUREZA) or [""])[0],
            "marc": sem_acentos(" || ".join(str(v) for dty in F_MARC for v in valores(r, dty))),
        }
    individuais = {lid for lid, l in livros.items() if len(l["autores"]) == 1}

    # papéis das pessoas ligadas por relação
    prologos, papeis = [], Counter()   # prologos: (prologuista, livro, origem)
    for r in recs:
        if r["rec_RecTypeName"] != "Record relationship":
            continue
        d = {x["dty_ID"]: x for x in r["details"]}
        if R_PESSOA not in d or R_LIVRO not in d:
            continue
        pid, lid = d[R_PESSOA]["value"]["id"], d[R_LIVRO]["value"]["id"]
        if lid not in livros or pid not in por_id or pid in livros[lid]["autores"]:
            continue
        funcao = d.get(R_FUNCAO, {}).get("termLabel") or "nd"
        origem = "registo de relação"
        if funcao == "nd":
            nomes = [str(v) for v in valores(por_id[pid], F_NOME_COMPLETO) + valores(por_id[pid], F_VARIANTES)]
            funcao, origem = papel_marc(nomes, livros[lid]["marc"])
            funcao = funcao or "nd"
        elif funcao in FUNCOES_PROLOGO:
            funcao = "prologuista"
        papeis[funcao] += 1
        if funcao == "prologuista":
            prologos.append((pid, lid, origem))

    def linha_livro(lid):
        l = livros[lid]
        return [lid, l["titulo"], l["ano"], l["natureza"], l["traducao"], l["lingua_fonte"],
                " | ".join(editora(e)["nome"] for e in l["editoras"]), l["etiquetas"]]
    cab_livro = ["Livro H-ID", "Título", "Ano", "Natureza da edição", "Tradução", "Língua fonte",
                 "Editora", "Etiquetas"]

    # --- Rede 1: prologuistas -> autores/as de livros individuais -------------
    por_livro, pares = [], defaultdict(list)
    for pid, lid, origem in sorted(set(prologos), key=lambda x: (int(x[1]), int(x[0]))):
        if lid not in individuais:
            continue
        aid = livros[lid]["autores"][0]
        por_livro.append([pid, aid, pessoa(pid)["nome"], pessoa(aid)["nome"], origem] + linha_livro(lid))
        pares[(pid, aid)].append(lid)
    n_prologos = Counter(p for (p, a), ls in pares.items() for _ in ls)
    n_prologados = Counter(a for (p, a), ls in pares.items() for _ in ls)
    n_individuais = Counter(livros[l]["autores"][0] for l in individuais)
    nos1 = []
    for pid in sorted({x for par in pares for x in par}, key=int):
        p = pessoa(pid)
        papel = "ambos" if n_prologos[pid] and n_prologados[pid] else \
            ("prologuista" if n_prologos[pid] else "autor/a")
        nos1.append([pid, p["nome"], papel, p["genero"], p["nasc"], p["morte"],
                     n_prologos[pid], n_prologados[pid], n_individuais[pid]])
    arestas1 = [[p, a, len(ls), "Directed", min(livros[l]["ano"] for l in ls), max(livros[l]["ano"] for l in ls),
                 " | ".join(ls)] for (p, a), ls in sorted(pares.items(), key=lambda x: -len(x[1]))]
    cab_nos1 = ["Id", "Label", "Papel na rede", "Género", "Nascimento", "Morte", "Prólogos escritos",
                "Prólogos recebidos", "Livros individuais como autor/a"]
    cab_ar1 = ["Source", "Target", "Weight", "Type", "Primeiro ano", "Último ano", "Livros H-ID"]
    base = saida / "rede1-prologuistas-autores"
    escrever_csv(f"{base}_nos.csv", cab_nos1, nos1)
    escrever_csv(f"{base}_arestas.csv", cab_ar1, arestas1)
    escrever_csv(f"{base}_arestas-por-livro.csv",
                 ["Source", "Target", "Prologuista", "Autor/a", "Origem do papel"] + cab_livro, por_livro)
    escrever_gexf(f"{base}.gexf", "Prologuistas e autores/as de livros individuais", True,
                  cab_nos1, nos1, cab_ar1, arestas1)

    # --- Rede 2: autores/as de livros individuais -- editoras -----------------
    # as editoras agrupam-se pelo nome normalizado (ou pelo nome, se não o tiverem)
    grupo_de, grupos = {}, defaultdict(lambda: {"ids": [], "inicio": [], "fim": [], "aberto": False})
    for r in recs:
        if r["rec_RecTypeName"] != "Editora":
            continue
        e = editora(r["rec_ID"])
        chave = e["normalizado"] or e["nome"]
        grupo_de[r["rec_ID"]] = chave
        g = grupos[chave]
        g["ids"].append(r["rec_ID"])
        if e["inicio"] != "":
            g["inicio"].append(e["inicio"])
            g["fim"].append(e["fim"])
    por_livro2, pares2 = [], defaultdict(list)
    for lid in sorted(individuais, key=int):
        aid = livros[lid]["autores"][0]
        for chave in sorted({grupo_de[eid] for eid in livros[lid]["editoras"]}):
            por_livro2.append([f"P{aid}", f"E:{chave}", pessoa(aid)["nome"], chave] + linha_livro(lid))
            pares2[(aid, chave)].append(lid)
    livros_autor = Counter(a for (a, e), ls in pares2.items() for _ in ls)
    livros_editora = Counter(e for (a, e), ls in pares2.items() for _ in ls)
    eds_autor = Counter(a for a, e in pares2)
    auts_editora = Counter(e for a, e in pares2)
    nos2 = []
    for aid in sorted({a for a, e in pares2}, key=int):
        p = pessoa(aid)
        nos2.append([f"P{aid}", p["nome"], "Pessoa", aid, p["genero"], p["nasc"], p["morte"], "", "", "",
                     livros_autor[aid], eds_autor[aid]])
    for chave in sorted({e for a, e in pares2}):
        g = grupos[chave]
        fins = [f for f in g["fim"] if f != ""]
        nos2.append([f"E:{chave}", chave, "Editora", " | ".join(g["ids"]), "", "", "", len(g["ids"]),
                     min(g["inicio"]) if g["inicio"] else "",
                     max(fins) if fins and len(fins) == len(g["fim"]) else "",
                     livros_editora[chave], auts_editora[chave]])
    arestas2 = [[f"P{a}", f"E:{e}", len(ls), "Undirected", min(livros[l]["ano"] for l in ls),
                 max(livros[l]["ano"] for l in ls), " | ".join(ls)]
                for (a, e), ls in sorted(pares2.items(), key=lambda x: -len(x[1]))]
    cab_nos2 = ["Id", "Label", "Tipo", "H-ID", "Género", "Nascimento", "Morte", "N.º de registos Editora",
                "Início de atividade (editora)", "Fim de atividade (editora)", "Livros individuais",
                "N.º de ligações distintas"]
    base = saida / "rede2-autores-editoras"
    escrever_csv(f"{base}_nos.csv", cab_nos2, nos2)
    escrever_csv(f"{base}_arestas.csv", cab_ar1, arestas2)
    escrever_csv(f"{base}_arestas-por-livro.csv",
                 ["Source", "Target", "Autor/a", "Editora (nome normalizado)"] + cab_livro, por_livro2)
    escrever_gexf(f"{base}.gexf", "Autores/as de livros individuais e editoras (nome normalizado)", False,
                  cab_nos2, nos2, cab_ar1, arestas2)

    # --- resumo ---------------------------------------------------------------
    print(f"Livros: {len(livros)}; individuais (1 pessoa em Autoria): {len(individuais)}")
    print("Papéis das pessoas ligadas por relação (fora da Autoria):")
    for k, v in papeis.most_common():
        print(f"  {v:5d}  {k}")
    print("\nRede 1 (prologuistas -> autores/as):")
    print(f"  {len(nos1)} pessoas, {len(arestas1)} ligações, {len(por_livro)} prólogos em "
          f"{len({l[5] for l in por_livro})} livros")
    print("  origem do papel:", dict(Counter(l[4] for l in por_livro)))
    print("  papel na rede:", dict(Counter(n[2] for n in nos1)))
    print("  mais prólogos escritos:", [(n[1], n[6]) for n in sorted(nos1, key=lambda n: -n[6])[:8]])
    print("  mais prólogos recebidos:", [(n[1], n[7]) for n in sorted(nos1, key=lambda n: -n[7])[:8]])
    print("\nRede 2 (autores/as -- editoras):")
    print(f"  {sum(1 for n in nos2 if n[2] == 'Pessoa')} pessoas, {sum(1 for n in nos2 if n[2] == 'Editora')} "
          f"editoras, {len(arestas2)} ligações, {len(por_livro2)} pares livro-editora")
    print("  editoras com mais autores/as:", [(n[1], n[11]) for n in
                                              sorted((n for n in nos2 if n[2] == "Editora"), key=lambda n: -n[11])[:8]])
    print("  autores/as com mais editoras:", [(n[1], n[11]) for n in
                                              sorted((n for n in nos2 if n[2] == "Pessoa"), key=lambda n: -n[11])[:8]])


if __name__ == "__main__":
    main()
