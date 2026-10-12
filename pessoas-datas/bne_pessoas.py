#!/usr/bin/env python3
"""
Cruza as entidades Pessoa da exportação JSON do Heurist (livpoesia) com o
catálogo de autoridades de pessoas da BNE (persona-JSON.json), pelo nome, para
trazer as datas de nascimento e morte, o género e os identificadores externos
(VIAF, ISNI, Wikidata, ORCID), e confronta as datas com as da Wikidata.

Uso:
    python3 bne_pessoas.py Export_livpoesia.json persona-JSON.json [pasta_saida]

Se existir na pasta de saída o ficheiro pessoas-datas-wikidata.csv (produzido
por wikidata_pessoas_datas.py), as datas da Wikidata entram no confronto.

Saídas (UTF-8 com BOM, separador TAB, como as exportações do Heurist):
  pessoas-bne.csv            todas as pessoas, com o registo da BNE encontrado,
                             os dados para o avaliar e o confronto de datas
  pessoas-bne-importar.csv   só os casos fiáveis em que há algo novo para a BD

Como se escolhe o registo da BNE
  O nome da BD («Apelidos, Nome» e as variantes) compara-se com o nome e os
  outros nomes de cada registo da BNE, sem acentos nem maiúsculas. Como há
  homónimos, procura-se confirmação independente:
    - ano MARC   o ano de nascimento que acompanha o nome nos campos MARC dos
                 livros da pessoa (p. ex. «Criado, Felipe, 1928-2013»)
    - ano BD     o ano de nascimento já registado na BD
    - Wikidata   o ID da Wikidata da BD igual ao do registo da BNE
    - VIAF       o ID do VIAF da BD igual ao do registo da BNE
    - título     um título de um livro da pessoa citado nas fontes do registo
  Confiança: alta = um único registo confirmado; média = sem confirmação, mas
  só há um registo com esse nome (ou só um coincide com o ano da Wikidata);
  baixa = vários registos possíveis, a escolher à mão.
"""
import csv
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

SEP = "/**/"

# dty_ID dos campos usados
F_NOME_COMPLETO, F_VARIANTES, F_GENERO = 990, 991, 20
F_QID, F_VIAF, F_NASC, F_MORTE = 1029, 1031, 1028, 1027
F_TITULO, F_MARC = 944, (946, 977)

GENERO = {"masculino": "Male", "femenino": "Female"}
CAMPOS_BNE = ["otros_identificadores", "fecha_nacimiento", "fecha_muerte", "otros_atributos_persona",
              "lugar_nacimiento", "lugar_muerte", "pais_relacionado", "otros_lugares_relacionados",
              "lugar_residencia", "campo_actividad", "grupo_o_entidad_relacionada", "ocupacion", "genero",
              "lengua", "otros_nombres", "persona_relacionada", "fuentes_de_informacion"]

RE_DATAS_FINAL = re.compile(r",?\s*\(\s*([^()]*\d[^()]*)\)\s*$")
RE_INTERVALO = re.compile(r"(\d{3,4})?\s*\??\s*-\s*(\d{3,4})?")
RE_MARC = re.compile(r"([^\d]{3,120}?)[,\s(]+(\d{4})\s*-\s*(\d{4})?")


# --- utilidades -------------------------------------------------------------

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", texto).split())


def limpar(valor):
    """Valores da BNE: tira espaços e separadores soltos."""
    if not valor:
        return ""
    partes = [p.strip(" ,") for p in str(valor).split(SEP)]
    return " | ".join(p for p in partes if p)


def nome_e_datas(cabecalho):
    """«Criado, Felipe, ( 1928-2013)» -> («Criado, Felipe», «1928», «2013»)."""
    m = RE_DATAS_FINAL.search(cabecalho)
    if m:
        d = RE_INTERVALO.search(m.group(1))
        if d and (d.group(1) or d.group(2)):
            return cabecalho[:m.start()].strip(" ,"), d.group(1) or "", d.group(2) or ""
    return cabecalho.strip(" ,"), "", ""


def ano(data):
    m = re.search(r"\d{4}", data or "")
    return m.group(0) if m else ""


def identificadores(texto):
    """Extrai VIAF, ISNI, Wikidata e ORCID de «otros_identificadores»."""
    ids = {}
    for parte in (texto or "").split(SEP):
        m = re.match(r"\s*(\w+)\s*:\s*(\S+)", parte)
        if not m:
            continue
        tipo, url = m.group(1).lower(), m.group(2)
        if tipo == "viaf":
            v = re.search(r"viaf/(\d+)", url)
        elif tipo == "wikidata":
            v = re.search(r"(Q\d+)", url)
        elif tipo == "isni":
            v = re.search(r"isni/(\w+)", url)
        elif tipo == "orcid":
            v = re.search(r"orcid\.org/([\dX-]+)", url)
        else:
            v = None
        if v:
            ids.setdefault(tipo, v.group(1))
    return ids


def valores(rec, dty):
    return [str(d["value"]).strip() for d in rec["details"] if d["dty_ID"] == dty and str(d["value"]).strip()]


# --- BD (Heurist) -----------------------------------------------------------

def carregar_bd(caminho):
    with open(caminho, encoding="utf-8") as f:
        recs = json.load(f)["heurist"]["records"]
    por_id = {r["rec_ID"]: r for r in recs}

    # livros ligados a cada pessoa (ponteiros diretos e registos de relação)
    livros = defaultdict(set)
    for r in recs:
        if r["rec_RecTypeName"] == "Livro":
            for d in r["details"]:
                if d["fieldType"] == "resource" and d["value"].get("type") == "10":
                    livros[d["value"]["id"]].add(r["rec_ID"])
        elif r["rec_RecTypeName"] == "Record relationship":
            d = {x["dty_ID"]: x["value"] for x in r["details"]}
            if 5 in d and 7 in d:
                livros[d[5]["id"]].add(d[7]["id"])

    pessoas = []
    for r in recs:
        if r["rec_RecTypeName"] != "Pessoa":
            continue
        nomes = valores(r, F_NOME_COMPLETO) + valores(r, F_VARIANTES)
        chaves = {normalizar(n) for n in nomes} - {""}
        # anos que acompanham o nome nos campos MARC dos livros da pessoa
        anos_marc, titulos = set(), set()
        for lid in livros[r["rec_ID"]]:
            livro = por_id.get(lid)
            if not livro:
                continue
            for t in valores(livro, F_TITULO):
                tn = normalizar(t)
                if len(tn) >= 12 and len(tn.split()) >= 2:
                    titulos.add(tn)
            for dty in F_MARC:
                for texto in valores(livro, dty):
                    for m in RE_MARC.finditer(texto):
                        # o nome é o último troço antes das datas («…, il. Pestana, Paco»)
                        troco = re.split(r"[.)\]*/]\s+|\s{2,}", m.group(1).strip(" ,("))[-1]
                        if normalizar(troco) in chaves:
                            anos_marc.add((m.group(2), m.group(3) or ""))
        genero = [d.get("termLabel", "") for d in r["details"] if d["dty_ID"] == F_GENERO]
        pessoas.append({
            "id": r["rec_ID"], "nome": valores(r, F_NOME_COMPLETO)[0], "chaves": chaves,
            "genero": genero[0] if genero else "",
            "qid": (valores(r, F_QID) or [""])[0], "viaf": (valores(r, F_VIAF) or [""])[0],
            "nasc": (valores(r, F_NASC) or [""])[0], "morte": (valores(r, F_MORTE) or [""])[0],
            "anos_marc": anos_marc, "titulos": titulos,
        })
    return pessoas


# --- BNE --------------------------------------------------------------------

def carregar_bne(caminho, chaves_bd):
    """Lê o ficheiro linha a linha e guarda só os registos cujo nome (ou outro
    nome) coincide com algum nome da BD. Os registos repetidos da mesma pessoa
    (mesmo nome e mesmas datas) fundem-se num só."""
    grupos = {}                      # (chave do nome, nasc, morte) -> dados fundidos
    por_chave = defaultdict(set)     # chave de nome ou variante -> grupos
    n = 0
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip().rstrip(",")
            if linha.startswith("["):
                linha = linha[1:]
            if linha.endswith("]"):
                linha = linha[:-1]
            if not linha:
                continue
            n += 1
            if n % 500000 == 0:
                print(f"  BNE: {n} registos lidos", file=sys.stderr)
            try:
                r = json.loads(linha)
            except json.JSONDecodeError:
                continue
            nome, nasc, morte = nome_e_datas(r.get("nombre_de_persona") or "")
            chave = normalizar(nome)
            variantes = set()
            for v in (r.get("otros_nombres") or "").split(SEP):
                variantes.add(normalizar(nome_e_datas(v)[0]))
            variantes -= {"", chave}
            if chave not in chaves_bd and not (variantes & chaves_bd):
                continue
            nasc = ano(r.get("fecha_nacimiento")) or nasc
            morte = ano(r.get("fecha_muerte")) or morte
            gid = (chave, nasc, morte)
            g = grupos.setdefault(gid, {"nome": nome, "nasc": nasc, "morte": morte, "ids": [],
                                        "variantes": set(), **{c: "" for c in CAMPOS_BNE}})
            g["ids"].append(r["id"])
            g["variantes"] |= variantes
            for c in CAMPOS_BNE:
                if not g[c] and r.get(c) and str(r[c]).strip():
                    g[c] = str(r[c]).strip()
            por_chave[chave].add(gid)
            for v in variantes & chaves_bd:
                por_chave[v].add(gid)
    print(f"  BNE: {n} registos lidos; {len(grupos)} candidatos para a BD", file=sys.stderr)
    return grupos, por_chave


# --- Wikidata (resultado do outro script) -----------------------------------

def carregar_wikidata(caminho):
    dados = {}
    if not os.path.exists(caminho):
        return dados
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            dados[r["Pessoa H-ID"]] = {
                "conf": r["Confiança"], "qid": r["ID da Wikidata"],
                "nasc": r["Data de nacemento (Wikidata)"], "morte": r["Data da morte (Wikidata)"],
            }
    return dados


# --- escolha do registo e confronto -----------------------------------------

def escolher(p, grupos, por_chave, wd):
    """Devolve (confiança, grupo escolhido, evidências, tipo de coincidência, outros grupos)."""
    cands = set()
    for c in p["chaves"]:
        cands |= por_chave.get(c, set())
    if not cands:
        return "sem correspondência", None, [], "", []
    anos_bd = {a for a, _ in p["anos_marc"]}
    avaliados = []
    for gid in cands:
        g = grupos[gid]
        ids = identificadores(g["otros_identificadores"])
        fortes, fracas = [], []
        if g["nasc"] and g["nasc"] in anos_bd:
            fortes.append("ano MARC")
        if g["nasc"] and ano(p["nasc"]) == g["nasc"]:
            fortes.append("ano BD")
        if p["qid"] and ids.get("wikidata") == p["qid"]:
            fortes.append("Wikidata")
        if p["viaf"] and ids.get("viaf") == p["viaf"]:
            fortes.append("VIAF")
        fontes = normalizar(g["fuentes_de_informacion"])
        if fontes and any(t in fontes for t in p["titulos"]):
            fortes.append("título")
        if wd and wd["conf"] in ("alta", "média", "ID já na BD"):
            if g["nasc"] and ano(wd["nasc"]) == g["nasc"]:
                fracas.append("ano Wikidata")
            if wd["qid"] and ids.get("wikidata") == wd["qid"] and "Wikidata" not in fortes:
                fortes.append("Wikidata (pesquisa)")
        direto = gid[0] in p["chaves"]
        avaliados.append((len(fortes), len(fracas), direto, bool(g["nasc"]), gid, fortes + fracas))
    avaliados.sort(key=lambda a: a[:4], reverse=True)
    melhor = avaliados[0]
    empate = len(avaliados) > 1 and avaliados[1][:2] == melhor[:2]
    if melhor[0] and not empate:
        conf = "alta"
    elif not empate and (melhor[1] or len(avaliados) == 1):
        conf = "média"
    else:
        conf = "baixa"
    outros = [a[4] for a in avaliados[1:]]
    return conf, melhor[4], melhor[5], "nome" if melhor[2] else "variante", outros


def confrontar(bd, bne, wdata):
    """Compara os anos das três fontes. Devolve (confronto, proposta, fonte da proposta)."""
    anos = {k: ano(v) for k, v in (("BD", bd), ("BNE", bne), ("Wikidata", wdata)) if v}
    if not anos:
        return "", "", ""
    distintos = set(anos.values())
    if len(anos) == 1:
        confronto = f"só {next(iter(anos))}"
    elif len(distintos) == 1:
        confronto = "coincidem (" + ", ".join(anos) + ")"
    else:
        confronto = "DIVERGEM: " + ", ".join(f"{k} {v}" for k, v in anos.items())
    if bd:
        return confronto, "", ""
    if bne and wdata:
        if ano(bne) == ano(wdata):
            return confronto, wdata, "Wikidata (ano confirmado pela BNE)"
        return confronto, bne, "BNE (a Wikidata diverge)"
    if bne:
        return confronto, bne, "BNE"
    return confronto, wdata, "Wikidata"


def escrever(caminho, cabecalho, linhas):
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(cabecalho)
        w.writerows(linhas)


def main():
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    saida = sys.argv[3] if len(sys.argv) > 3 else "."
    pessoas = carregar_bd(sys.argv[1])
    print(f"{len(pessoas)} pessoas na BD", file=sys.stderr)
    chaves_bd = set().union(*(p["chaves"] for p in pessoas))
    grupos, por_chave = carregar_bne(sys.argv[2], chaves_bd)
    wikidata = carregar_wikidata(os.path.join(saida, "pessoas-datas-wikidata.csv"))

    cab = ["Pessoa H-ID", "Nome completo", "Confiança BNE", "Evidência", "Coincidência", "ID BNE",
           "Nome na BNE", "Data de nacemento (BNE)", "Data da morte (BNE)", "Género (BNE)",
           "ID do VIAF (BNE)", "ISNI (BNE)", "ID da Wikidata (BNE)", "ORCID (BNE)",
           "Ocupação (BNE)", "Área de atividade (BNE)", "Local de nascimento (BNE)", "Local de morte (BNE)",
           "País (BNE)", "Língua (BNE)", "Outros nomes (BNE)", "Outros atributos (BNE)", "Fontes (BNE)",
           "URL no catálogo BNE", "N.º de candidatos BNE", "Outros candidatos BNE",
           "Género (BD)", "Data de nacemento (BD)", "Data da morte (BD)", "ID da Wikidata (BD)",
           "Confiança Wikidata", "ID da Wikidata (pesquisa)", "Data de nacemento (Wikidata)",
           "Data da morte (Wikidata)", "Confronto nascimento", "Confronto morte", "Confronto género",
           "Confronto ID da Wikidata", "Proposta: nascimento", "Fonte nascimento", "Proposta: morte",
           "Fonte morte"]
    cab_imp = ["Pessoa H-ID", "Nome completo", "ID BNE", "Data de nacemento", "Fonte nascimento",
               "Data da morte", "Fonte morte", "Género", "ID do VIAF", "URL do VIAF", "ISNI",
               "ID da Wikidata", "URL da Wikidata", "Confiança BNE", "Confiança Wikidata"]
    linhas, importar, resumo = [], [], Counter()
    for p in pessoas:
        wd = wikidata.get(p["id"])
        conf, gid, evid, tipo, outros = escolher(p, grupos, por_chave, wd)
        g = grupos[gid] if gid else None
        fiavel = conf == "alta"
        ids = identificadores(g["otros_identificadores"]) if g else {}
        genero_bne = GENERO.get(normalizar(g["genero"]), limpar(g["genero"])) if g else ""

        # a Wikidata só entra no confronto se a ligação for fiável e não contradisser a BNE
        wd_fiavel = bool(wd) and wd["conf"] in ("alta", "ID já na BD")
        qid_bd_ou_pesquisa = p["qid"] or (wd["qid"] if wd_fiavel else "")
        confronto_qid = ""
        if fiavel and ids.get("wikidata") and qid_bd_ou_pesquisa:
            confronto_qid = "coincide" if ids["wikidata"] == qid_bd_ou_pesquisa else \
                f"DIVERGE: BNE {ids['wikidata']}, {'BD' if p['qid'] else 'pesquisa'} {qid_bd_ou_pesquisa}"
            if confronto_qid != "coincide" and not p["qid"]:
                wd_fiavel = False  # a pesquisa por nome apanhou um homónimo
        wd_nasc, wd_morte = (wd["nasc"], wd["morte"]) if wd_fiavel else ("", "")
        bne_nasc, bne_morte = (g["nasc"], g["morte"]) if fiavel else ("", "")

        c_nasc, prop_nasc, fonte_nasc = confrontar(p["nasc"], bne_nasc, wd_nasc)
        c_morte, prop_morte, fonte_morte = confrontar(p["morte"], bne_morte, wd_morte)
        # se os anos de nascimento divergem, as datas da Wikidata não são de fiar
        if c_nasc.startswith("DIVERGEM") and bne_nasc and wd_nasc and not p["qid"]:
            if fonte_morte.startswith("Wikidata"):
                prop_morte, fonte_morte = (bne_morte, "BNE") if bne_morte else ("", "")
        c_genero = ""
        if g and genero_bne and p["genero"]:
            c_genero = "coincide" if genero_bne == p["genero"] else f"DIVERGE: BD {p['genero']}, BNE {genero_bne}"

        def descrever(o):
            x = grupos[o]
            datas = f" ({x['nasc']}-{x['morte']})" if x["nasc"] or x["morte"] else ""
            return f"{x['nome']}{datas} [{x['ids'][0]}]"

        linhas.append([
            p["id"], p["nome"], conf, ", ".join(evid), tipo,
            " | ".join(g["ids"][:5]) if g else "", g["nome"] if g else "",
            g["nasc"] if g else "", g["morte"] if g else "", genero_bne,
            ids.get("viaf", ""), ids.get("isni", ""), ids.get("wikidata", ""), ids.get("orcid", ""),
            *([limpar(g[c]) for c in ("ocupacion", "campo_actividad", "lugar_nacimiento", "lugar_muerte",
                                      "pais_relacionado", "lengua", "otros_nombres",
                                      "otros_atributos_persona")] if g else [""] * 8),
            limpar(g["fuentes_de_informacion"])[:300] if g else "",
            (f"https://catalogo.bne.es/discovery/fulldisplay?docid=alma{g['ids'][0]}"
             "&vid=34BNE_INST:CATALOGO") if g else "",
            (1 + len(outros)) if g else 0, " ; ".join(descrever(o) for o in outros[:8]),
            p["genero"], p["nasc"], p["morte"], p["qid"],
            wd["conf"] if wd else "", wd["qid"] if wd else "", wd["nasc"] if wd else "",
            wd["morte"] if wd else "",
            c_nasc, c_morte, c_genero, confronto_qid, prop_nasc, fonte_nasc, prop_morte, fonte_morte,
        ])
        resumo[conf] += 1

        # ficheiro de importação: só o que é novo para a BD e vem de fonte fiável
        novo_genero = genero_bne if fiavel and not p["genero"] and genero_bne in GENERO.values() else ""
        novo_viaf = ids.get("viaf", "") if fiavel and not p["viaf"] else ""
        novo_isni = ids.get("isni", "") if fiavel else ""
        novo_qid = ""
        if not p["qid"]:
            novo_qid = ids.get("wikidata", "") if fiavel else ""
            if not novo_qid and wd_fiavel:
                novo_qid = wd["qid"]
        if prop_nasc or prop_morte or novo_genero or novo_viaf or novo_isni or novo_qid:
            importar.append([
                p["id"], p["nome"], g["ids"][0] if fiavel else "", prop_nasc, fonte_nasc, prop_morte,
                fonte_morte, novo_genero, novo_viaf, f"https://viaf.org/viaf/{novo_viaf}" if novo_viaf else "",
                novo_isni, novo_qid, f"https://www.wikidata.org/wiki/{novo_qid}" if novo_qid else "",
                conf, wd["conf"] if wd else "",
            ])

    escrever(os.path.join(saida, "pessoas-bne.csv"), cab, linhas)
    escrever(os.path.join(saida, "pessoas-bne-importar.csv"), cab_imp, importar)

    print("\nCorrespondência com a BNE:")
    for k in ("alta", "média", "baixa", "sem correspondência"):
        print(f"  {resumo[k]:5d}  {k}")
    i = {c: n for n, c in enumerate(cab_imp)}
    print(f"\n{len(importar)} linhas em pessoas-bne-importar.csv")
    for c in ("Data de nacemento", "Data da morte", "Género", "ID do VIAF", "ISNI", "ID da Wikidata"):
        print(f"  {sum(1 for l in importar if l[i[c]]):5d}  {c}")
    j = {c: n for n, c in enumerate(cab)}
    for c in ("Confronto nascimento", "Confronto morte", "Confronto género", "Confronto ID da Wikidata"):
        print(f"\n{c}:")
        for k, v in Counter(re.sub(r":.*", "", l[j[c]]) for l in linhas if l[j[c]]).most_common():
            print(f"  {v:5d}  {k}")


if __name__ == "__main__":
    main()
