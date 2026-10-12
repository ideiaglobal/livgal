#!/usr/bin/env python3
"""
Procura na Wikidata as datas de nascimento (P569) e morte (P570) das entidades
Pessoa da exportação JSON do Heurist (livpoesia), para preencher as que faltam.

Uso:
    pip install requests
    python3 wikidata_pessoas_datas.py Export_livpoesia.json [pasta_saida] [--limite N]

Duas vias:
  1. Pessoas que já têm «ID da Wikidata»: lê as datas diretamente desse item.
  2. Pessoas sem ID: pesquisa o nome entre os itens humanos (P31 = Q5) e
     classifica o resultado por confiança (alta / média / baixa).

Saídas (UTF-8 com BOM, separador TAB, como as exportações do Heurist):
  pessoas-datas-wikidata.csv   todas as pessoas a que falta alguma data, com o
                               candidato encontrado e os dados para o avaliar
  pessoas-datas-importar.csv   só os casos fiáveis (ID já existente ou
                               confiança alta) em que há algo novo a importar

As respostas da Wikidata ficam em wikidata_cache.json; se repetir a execução,
só se pedem os nomes e itens que ainda não estão lá.
"""
import csv
import json
import os
import re
import sys
import time
import unicodedata
from collections import Counter

import requests

API = "https://www.wikidata.org/w/api.php"
# A Wikimedia exige um User-Agent identificável: ponha aqui o seu contacto
HEADERS = {"User-Agent": "LivroGalegoPessoas/1.0 (https://github.com/ideiaglobal/livgal; mailto:info@heurisko.io)"}
PAUSA = 0.25         # segundos entre pedidos
LOTE = 50            # itens por pedido wbgetentities (máximo da API)
MAX_CANDIDATOS = 8
CACHE = "wikidata_cache.json"
LINGUAS = ["gl", "pt", "es", "ca", "en", "fr", "mul"]

# dty_ID dos campos da entidade Pessoa
F_NOME_COMPLETO, F_VARIANTES, F_QID, F_NASC, F_MORTE = 990, 991, 1029, 1028, 1027

# Ocupações (P106) que tornam plausível que o candidato seja a pessoa da BD
OCUPACOES = {
    "Q36180": "escritor/a", "Q49757": "poeta", "Q6625963": "romancista", "Q11774202": "ensaísta",
    "Q214917": "dramaturgo/a", "Q4853732": "escritor/a infantil", "Q333634": "tradutor/a",
    "Q4263842": "crítico/a literário/a", "Q1930187": "jornalista", "Q1607826": "editor/a",
    "Q2516866": "editor/a (publisher)", "Q13418253": "filólogo/a", "Q14467526": "linguista",
    "Q1622272": "professor/a universitário/a", "Q37226": "professor/a", "Q201788": "historiador/a",
    "Q4964182": "filósofo/a", "Q644687": "ilustrador/a", "Q1028181": "pintor/a", "Q483501": "artista",
    "Q3391743": "artista visual", "Q1281618": "escultor/a", "Q33231": "fotógrafo/a",
    "Q715301": "autor/a de banda desenhada", "Q1114448": "cartunista", "Q627325": "designer gráfico/a",
    "Q639669": "músico/a", "Q177220": "cantor/a", "Q488205": "cantautor/a", "Q36834": "compositor/a",
    "Q33999": "ator/atriz", "Q2526255": "realizador/a", "Q28389": "argumentista", "Q186370": "trovador",
    "Q2306091": "sociólogo/a", "Q15980158": "autor/a de não ficção",
    "Q482980": "autor/a", "Q18844224": "escritor/a de ficção científica", "Q822146": "letrista",
    "Q12144794": "prosador/a", "Q3579035": "contista", "Q15949613": "contista", "Q1209498": "advogado/a poeta",
}


# Descrições que ligam o candidato à Galiza (em qualquer língua)
RE_GALEGO = re.compile(r"galeg|galleg|galici|galiza|galic", re.I)


# --- utilidades -------------------------------------------------------------

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", texto).split())


def nome_direto(nome_completo):
    """«Apelidos, Nome» -> «Nome Apelidos»."""
    if "," in nome_completo:
        apelidos, nome = nome_completo.split(",", 1)
        return f"{nome.strip()} {apelidos.strip()}"
    return nome_completo.strip()


def pesquisavel(nome):
    """Falso para nomes só com iniciais ou de uma só palavra (demasiado ambíguos)."""
    palavras = [p for p in re.split(r"\s+", nome) if p]
    completas = [p for p in palavras if len(p.strip(".")) > 2 and not p.endswith(".")]
    return len(palavras) >= 2 and len(completas) >= 2


def pedir(params):
    params = dict(params, format="json")
    for tentativa in range(8):
        try:
            r = requests.get(API, params=params, headers=HEADERS, timeout=60)
            if r.status_code == 200:
                dados = r.json()
                if "error" not in dados:
                    time.sleep(PAUSA)
                    return dados
                # erros temporários (servidor ocupado, limite de pedidos): espera e repete
                if not re.search(r"busy|maxlag|ratelimit|timeout|internal", dados["error"].get("code", "")):
                    raise SystemExit(f"Erro da API: {dados['error']}")
        except requests.RequestException as e:
            print(f"  (erro de rede: {e}; nova tentativa)", file=sys.stderr)
        time.sleep(10 * (tentativa + 1))
    raise SystemExit("A Wikidata não respondeu depois de várias tentativas.")


def data_wikidata(claims, prop):
    """Devolve (data, nota). Data como AAAA, AAAA-MM ou AAAA-MM-DD segundo a precisão."""
    valores = []
    for c in claims.get(prop, []):
        if c.get("rank") == "deprecated" or c["mainsnak"].get("snaktype") != "value":
            continue
        v = c["mainsnak"]["datavalue"]["value"]
        t, prec = v["time"], v["precision"]
        if not t.startswith("+") or prec < 9:
            continue
        ano, mes, dia = t[1:5], t[6:8], t[9:11]
        data = ano if prec == 9 else (f"{ano}-{mes}" if prec == 10 else f"{ano}-{mes}-{dia}")
        valores.append((c.get("rank") == "preferred", prec, data))
    if not valores:
        return "", ""
    valores.sort(reverse=True)  # preferidas primeiro, depois as mais precisas
    anos = {d[:4] for _, _, d in valores}
    nota = f"{prop}: vários anos na Wikidata ({', '.join(sorted(anos))})" if len(anos) > 1 else ""
    return valores[0][2], nota


def rotulo(entidade):
    for l in LINGUAS:
        if l in entidade.get("labels", {}):
            return entidade["labels"][l]["value"]
    return next((v["value"] for v in entidade.get("labels", {}).values()), "")


def descricao(entidade):
    for l in LINGUAS:
        if l in entidade.get("descriptions", {}):
            return entidade["descriptions"][l]["value"]
    return ""


def nomes_do_item(entidade):
    nomes = {v["value"] for v in entidade.get("labels", {}).values()}
    for lista in entidade.get("aliases", {}).values():
        nomes |= {a["value"] for a in lista}
    return {normalizar(n) for n in nomes}


def ids_claim(claims, prop):
    return [c["mainsnak"]["datavalue"]["value"]["id"] for c in claims.get(prop, [])
            if c["mainsnak"].get("snaktype") == "value"]


# --- Wikidata ---------------------------------------------------------------

def pesquisar(nome, cache):
    """QIDs de itens humanos cujo texto contém o nome (frase exata; se nada, palavras soltas)."""
    if nome not in cache["pesquisas"]:
        qids = []
        for consulta in (f'"{nome}"', nome):
            dados = pedir({"action": "query", "list": "search", "srlimit": MAX_CANDIDATOS,
                           "srsearch": f"{consulta} haswbstatement:P31=Q5"})
            qids = [h["title"] for h in dados["query"]["search"]]
            if qids:
                break
        cache["pesquisas"][nome] = qids
    return cache["pesquisas"][nome]


def carregar_itens(qids, cache):
    faltam = sorted({q for q in qids if q not in cache["itens"]})
    for i in range(0, len(faltam), LOTE):
        lote = faltam[i:i + LOTE]
        dados = pedir({"action": "wbgetentities", "ids": "|".join(lote),
                       "props": "labels|aliases|descriptions|claims"})
        for q, ent in dados["entities"].items():
            claims = ent.get("claims", {})
            nasc, n1 = data_wikidata(claims, "P569")
            morte, n2 = data_wikidata(claims, "P570")
            item = {
                "rotulo": rotulo(ent), "descricao": descricao(ent), "nomes": sorted(nomes_do_item(ent)),
                "humano": "Q5" in ids_claim(claims, "P31"),
                "galego": any(RE_GALEGO.search(d["value"]) for d in ent.get("descriptions", {}).values()),
                "ocupacoes": ids_claim(claims, "P106"), "pais": ids_claim(claims, "P27"),
                "nasc": nasc, "morte": morte, "nota": "; ".join(n for n in (n1, n2) if n),
            }
            # itens redirecionados chegam com outro id: guarda-se sob o id pedido
            cache["itens"][q] = item
            if ent.get("id") and ent["id"] != q:
                cache["itens"][ent["id"]] = item
        for q in lote:
            cache["itens"].setdefault(q, None)  # item apagado ou inexistente
        print(f"  itens carregados: {min(i + LOTE, len(faltam))}/{len(faltam)}", file=sys.stderr)


def carregar_rotulos(qids, cache):
    faltam = sorted({q for q in qids if q not in cache["rotulos"] and q not in OCUPACOES})
    for i in range(0, len(faltam), LOTE):
        dados = pedir({"action": "wbgetentities", "ids": "|".join(faltam[i:i + LOTE]),
                       "props": "labels", "languages": "|".join(LINGUAS)})
        for q, ent in dados["entities"].items():
            cache["rotulos"][q] = rotulo(ent) or q


# --- avaliação dos candidatos ----------------------------------------------

def tipo_coincidencia(nomes_bd, item):
    """'exata' se algum nome da BD coincide com um rótulo/alias; 'parcial' se as palavras estão contidas."""
    alvo = set(item["nomes"])
    if nomes_bd & alvo:
        return "exata"
    for n in nomes_bd:
        pn = set(n.split())
        for a in alvo:
            pa = set(a.split())
            if len(pn) >= 2 and len(pa) >= 2 and (pn <= pa or pa <= pn):
                return "parcial"
    return ""


def avaliar(nomes_bd, qids, cache):
    """Devolve (confiança, melhor QID, outros QIDs, tipo de coincidência).

    alta   nome exato, candidato sem rival equivalente e uma destas situações:
           - descrito como galego, com ocupação cultural ou com o nome igual
             ao rótulo principal do item (não só a um alias);
           - único humano com esse nome, com ocupação cultural e com o nome
             igual ao rótulo principal
    média  há um candidato que se destaca, mas com menos garantias
    baixa  vários candidatos equivalentes: é preciso escolher à mão
    """
    cands = []
    for q in qids:
        item = cache["itens"].get(q)
        if not item or not item["humano"]:
            continue
        tipo = tipo_coincidencia(nomes_bd, item)
        if tipo:
            relevante = any(o in OCUPACOES for o in item["ocupacoes"])
            cands.append((tipo == "exata", item["galego"], relevante, q))
    if not cands:
        return "sem candidato", "", [], ""
    cands.sort(key=lambda c: tuple(not x for x in c[:3]))
    exata, galego, relevante, melhor = cands[0]
    iguais = [c for c in cands if c[:3] == cands[0][:3]]
    exatos = [c for c in cands if c[0]]
    outros = [c[3] for c in cands if c[3] != melhor]
    rotulo_igual = normalizar(cache["itens"][melhor]["rotulo"]) in nomes_bd
    if len(iguais) > 1:
        conf = "baixa"
    elif exata and ((galego and (relevante or rotulo_igual))
                    or (relevante and rotulo_igual and len(exatos) == 1)):
        conf = "alta"
    elif exata or galego or relevante:
        conf = "média"
    else:
        conf = "baixa"
    return conf, melhor, outros, "exata" if exata else "parcial"


# --- programa ---------------------------------------------------------------

def valores(rec, dty):
    return [str(d["value"]).strip() for d in rec["details"] if d["dty_ID"] == dty and str(d["value"]).strip()]


def escrever(caminho, cabecalho, linhas):
    with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(cabecalho)
        w.writerows(linhas)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    limite = int(sys.argv[sys.argv.index("--limite") + 1]) if "--limite" in sys.argv else None
    if limite is not None:
        args = [a for a in args if a != str(limite)]
    if not args:
        raise SystemExit(__doc__)
    saida = args[1] if len(args) > 1 else "."
    cache_path = os.path.join(saida, CACHE)

    with open(args[0], encoding="utf-8") as f:
        recs = json.load(f)["heurist"]["records"]
    pessoas = [r for r in recs if r["rec_RecTypeName"] == "Pessoa"]
    # só interessam as pessoas a que falta alguma das duas datas
    alvo = [p for p in pessoas if not valores(p, F_NASC) or not valores(p, F_MORTE)]
    if limite:
        alvo = alvo[:limite]
    print(f"{len(pessoas)} pessoas; {len(alvo)} com alguma data em falta", file=sys.stderr)

    cache = {"pesquisas": {}, "itens": {}, "rotulos": {}}
    if os.path.exists(cache_path):
        with open(cache_path, encoding="utf-8") as f:
            cache.update(json.load(f))

    def guardar_cache():
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)

    # 1. pesquisa por nome (só para quem não tem ID da Wikidata)
    nomes_de = {}
    for n, p in enumerate(alvo, 1):
        nome = nome_direto(valores(p, F_NOME_COMPLETO)[0])
        variantes = [nome_direto(v) for v in valores(p, F_VARIANTES)]
        nomes_de[p["rec_ID"]] = [nome] + variantes
        if valores(p, F_QID) or not pesquisavel(nome):
            continue
        novo = nome not in cache["pesquisas"]
        pesquisar(nome, cache)
        if novo and len(cache["pesquisas"]) % 50 == 0:
            guardar_cache()
            print(f"  pesquisas: {n}/{len(alvo)} pessoas vistas", file=sys.stderr)
    guardar_cache()

    # 2. dados dos itens (os já ligados e os candidatos)
    qids = {q for p in alvo for q in valores(p, F_QID)}
    qids |= {q for p in alvo for q in cache["pesquisas"].get(nomes_de[p["rec_ID"]][0], [])}
    carregar_itens(qids, cache)
    guardar_cache()
    carregar_rotulos({q for i in cache["itens"].values() if i for q in i["ocupacoes"] + i["pais"]}, cache)
    guardar_cache()

    def nome_ocupacao(q):
        return OCUPACOES.get(q) or cache["rotulos"].get(q, q)

    # 3. tabela de resultados
    cab = ["Pessoa H-ID", "Nome completo", "Origem", "Confiança", "Coincidência do nome", "ID da Wikidata",
           "URL da Wikidata", "Nome na Wikidata", "Descrição na Wikidata", "Descrita como galega", "Ocupações", "País",
           "Data de nacemento (Wikidata)", "Data da morte (Wikidata)", "Data de nacemento (BD)",
           "Data da morte (BD)", "Novo: nascimento", "Novo: morte", "Outros candidatos", "Notas"]
    linhas, importar, resumo = [], [], Counter()
    for p in alvo:
        hid, nome_bd = p["rec_ID"], valores(p, F_NOME_COMPLETO)[0]
        nasc_bd, morte_bd = (valores(p, F_NASC) or [""])[0], (valores(p, F_MORTE) or [""])[0]
        qid_bd = (valores(p, F_QID) or [""])[0]
        notas, outros, coinc = [], [], ""
        if qid_bd:
            origem, conf, qid = "ID já na BD", "ID já na BD", qid_bd
        elif not pesquisavel(nomes_de[hid][0]):
            origem, conf, qid = "não pesquisado", "nome insuficiente", ""
        else:
            origem = "pesquisa por nome"
            nomes_bd = {normalizar(n) for n in nomes_de[hid]}
            conf, qid, outros, coinc = avaliar(nomes_bd, cache["pesquisas"][nomes_de[hid][0]], cache)
        item = cache["itens"].get(qid) if qid else None
        if qid and not item:
            notas.append("item não encontrado na Wikidata")
        nasc_wd, morte_wd = (item["nasc"], item["morte"]) if item else ("", "")
        if item and item["nota"]:
            notas.append(item["nota"])
        if nasc_bd and nasc_wd and nasc_bd[:4] != nasc_wd[:4]:
            notas.append("ano de nascimento diferente na BD e na Wikidata")
        if morte_bd and morte_wd and morte_bd[:4] != morte_wd[:4]:
            notas.append("ano de morte diferente na BD e na Wikidata")
        novo_nasc = nasc_wd if not nasc_bd else ""
        novo_morte = morte_wd if not morte_bd else ""
        linhas.append([
            hid, nome_bd, origem, conf, coinc, qid, f"https://www.wikidata.org/wiki/{qid}" if qid else "",
            item["rotulo"] if item else "", item["descricao"] if item else "",
            "sim" if item and item["galego"] else "",
            "; ".join(nome_ocupacao(o) for o in item["ocupacoes"]) if item else "",
            "; ".join(cache["rotulos"].get(q, q) for q in item["pais"]) if item else "",
            nasc_wd, morte_wd, nasc_bd, morte_bd, novo_nasc, novo_morte,
            " ".join(outros), "; ".join(notas),
        ])
        chave = conf if conf != "ID já na BD" else "ID já na BD"
        resumo[(chave, "com data nova" if (novo_nasc or novo_morte) else "sem data nova")] += 1
        if conf in ("ID já na BD", "alta") and (novo_nasc or novo_morte or not qid_bd):
            importar.append([hid, nome_bd, "" if qid_bd else qid,
                             "" if qid_bd else f"https://www.wikidata.org/wiki/{qid}", novo_nasc, novo_morte, conf])

    escrever(os.path.join(saida, "pessoas-datas-wikidata.csv"), cab, linhas)
    escrever(os.path.join(saida, "pessoas-datas-importar.csv"),
             ["Pessoa H-ID", "Nome completo", "ID da Wikidata (novo)", "URL da Wikidata (novo)",
              "Data de nacemento", "Data da morte", "Confiança"], importar)

    print("\nResumo (pessoas com alguma data em falta):")
    for (conf, novo), n in sorted(resumo.items()):
        print(f"  {n:5d}  {conf:18s} {novo}")
    print(f"\n{len(importar)} linhas em pessoas-datas-importar.csv")


if __name__ == "__main__":
    main()
