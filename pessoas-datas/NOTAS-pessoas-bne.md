# Cruzamento das pessoas com o catálogo de autoridades da BNE

Esclarecimentos metodológicos e dúvidas em aberto da operação que cruza as entidades **Pessoa** da exportação `Export_livpoesia_20261012104901.json` com o catálogo de autoridades de pessoas da Biblioteca Nacional de España, para trazer datas de nascimento e morte, género e identificadores externos, e que confronta as datas com as da Wikidata.

- Script: `bne_pessoas.py`
- Entradas: a exportação JSON do Heurist; `persona-JSON.json` (catálogo da BNE); `pessoas-datas-wikidata.csv` (resultado de `wikidata_pessoas_datas.py`)
- Resultados: `pessoas-bne-importar.csv`, `pessoas-bne.csv`

Esta nota completa a `NOTAS-pessoas-datas.md`, que descreve a pesquisa na Wikidata.

## O que foi pedido

Um script que cruze as pessoas da BD com o ficheiro da BNE pelo nome e traga as datas de nascimento e morte, confrontando-as com as da Wikidata, guardando também o género e os outros identificadores.

## Dados de partida

| | |
|---|---|
| Pessoas na BD | 2708 |
| Registos no ficheiro da BNE | 3 316 906 |
| Tamanho do ficheiro da BNE | 2,78 GB |
| Fonte | <https://bnelab.bne.es/dato/catalogo-de-autoridades/> (conjunto «Persona», formato JSON) |
| Licença | Creative Commons CC0 |

O ficheiro da BNE tem 21 campos por registo. Os usados são: `id`, `nombre_de_persona`, `otros_nombres`, `fecha_nacimiento`, `fecha_muerte`, `genero`, `otros_identificadores`, `ocupacion`, `campo_actividad`, `lugar_nacimiento`, `lugar_muerte`, `pais_relacionado`, `lengua`, `otros_atributos_persona` e `fuentes_de_informacion`.

O ficheiro não está no repositório, por exceder o limite de 100 MB do GitHub (está excluído no `.gitignore`).

## Esclarecimentos: como foi feito

### Comparação dos nomes

- O nome da BD («Apelidos, Nome») e as suas variantes comparam-se com o nome e os outros nomes de cada registo da BNE, sem acentos, maiúsculas nem pontuação.
- A coincidência tem de ser exata depois dessa normalização. Não há correspondência aproximada.
- A coluna «Coincidência» indica se foi pelo nome principal da BNE («nome») ou por um nome alternativo («variante»).

### Particularidades do ficheiro da BNE

- **Datas dentro do nome.** Muitos registos trazem as datas no próprio nome («Criado, Felipe, ( 1928-2013)») e os campos de data vazios. O script lê as datas dos dois sítios.
- **Registos repetidos.** A mesma pessoa aparece muitas vezes em vários registos. Os que têm o mesmo nome e as mesmas datas fundem-se num só candidato, aproveitando os campos preenchidos de cada um.
- **Só anos.** A BNE dá apenas o ano de nascimento e de morte.
- **Identificadores.** O campo `otros_identificadores` traz VIAF, ISNI, Wikidata e ORCID, sob a forma de URL; o script extrai o identificador de cada um.

### Confirmação independente

Como há homónimos, o nome não basta. Procura-se confirmação noutra fonte:

| Evidência | O que significa | Casos (confiança alta) |
|---|---|---|
| ano MARC | o ano de nascimento da BNE aparece junto ao nome nos campos MARC dos livros da pessoa na BD (por exemplo «Criado, Felipe, 1928-2013») | 663 |
| título | um título de um livro da pessoa é citado nas fontes do registo da BNE | 518 |
| ano BD | o ano de nascimento da BNE é o que já está na BD | 471 |
| Wikidata | o ID da Wikidata da BD é o do registo da BNE | 378 |
| Wikidata (pesquisa) | o ID encontrado na pesquisa por nome é o do registo da BNE | 467 |
| VIAF | o ID do VIAF da BD é o do registo da BNE | 33 |

Uma pessoa pode ter várias evidências. Há ainda uma evidência fraca, «ano Wikidata» (o ano da Wikidata coincide com o da BNE), que não chega sozinha para a confiança alta.

### Níveis de confiança

| Confiança | Pessoas | Critério |
|---|---|---|
| alta | 1455 | um único registo com evidência forte |
| média | 673 | sem evidência forte, mas só há um registo com esse nome, ou só um coincide com o ano da Wikidata |
| baixa | 74 | vários registos possíveis sem nada que os distinga |
| sem correspondência | 506 | o nome não aparece na BNE |

### Confronto das datas e proposta

Para cada pessoa comparam-se os anos das três fontes (BD, BNE, Wikidata). Só entram no confronto os registos da BNE de confiança alta e as ligações à Wikidata fiáveis (ID já na BD ou confiança alta na pesquisa).

A proposta de data segue estas regras:

| Situação | Proposta | Casos (nascimento) |
|---|---|---|
| a BD já tem data | nenhuma | — |
| BNE e Wikidata com o mesmo ano | a data da Wikidata, por ser mais precisa | 404 |
| só a BNE | o ano da BNE | 295 |
| só a Wikidata | a data da Wikidata | 251 |
| BNE e Wikidata divergem | o ano da BNE | 6 |

Quando o ID da Wikidata da BNE é diferente do encontrado na pesquisa por nome, a pesquisa é tratada como homónimo e as suas datas são descartadas.

### Resultado do confronto

| Nascimento | Pessoas |
|---|---|
| coincidem BNE e Wikidata | 404 |
| coincidem BD, BNE e Wikidata | 330 |
| coincidem BD e BNE | 141 |
| coincidem BD e Wikidata | 71 |
| só BNE | 295 |
| só Wikidata | 251 |
| só BD | 35 |
| divergem | 15 |

| Morte | Pessoas |
|---|---|
| coincidem BD e BNE | 136 |
| coincidem BNE e Wikidata | 117 |
| só Wikidata | 69 |
| só BNE | 56 |
| só BD | 41 |
| divergem | 4 |

## Resultado

### Ficheiro `pessoas-bne-importar.csv`

Tem 1489 pessoas com algo novo para a BD. Substitui o `pessoas-datas-importar.csv` da operação anterior.

| Dado novo | Pessoas |
|---|---|
| Data de nascimento | 956 |
| Data da morte | 243 |
| Género | 35 |
| ID do VIAF | 1154 |
| ISNI | 951 |
| ID da Wikidata | 811 |

Cada data vem acompanhada da coluna de fonte. As colunas «Confiança BNE» e «Confiança Wikidata» permitem filtrar.

### Efeito na BD

| | Na BD hoje | Só com a Wikidata | Com BNE + Wikidata |
|---|---|---|---|
| Com data de nascimento | 586 (21,6 %) | 1251 (46,2 %) | 1542 (56,9 %) |
| Com data de morte | 179 (6,6 %) | 368 (13,6 %) | 422 (15,6 %) |
| Com ambas | 179 (6,6 %) | 364 (13,4 %) | 418 (15,4 %) |

### Ficheiro `pessoas-bne.csv`

Tem as 2708 pessoas, com o registo da BNE escolhido, a evidência, todos os dados da BNE (incluindo ocupação, locais, língua, fontes e ligação ao catálogo), os outros candidatos, os dados da BD e da Wikidata, os quatro confrontos (nascimento, morte, género, ID da Wikidata) e as propostas.

## Limitações a ter em conta

- **A confiança alta não é verificação manual.** Assenta em coincidências de ano, título ou identificador. É bastante mais segura do que a pesquisa por nome na Wikidata, mas não foi conferida pessoa a pessoa.
- **Datas só da Wikidata.** 251 nascimentos e 68 mortes do ficheiro de importação vêm apenas da Wikidata, sem confirmação da BNE. São os casos menos seguros; valem as reservas da nota anterior sobre homónimos.
- **Anos MARC.** A extração do nome e do ano dos campos MARC dos livros funciona por padrão de texto. Só conta quando o nome extraído é exatamente o da pessoa e o livro está ligado a ela.
- **Sem data de morte não quer dizer viva.** Vale para a BNE tal como para a Wikidata.
- **Cobertura.** 506 pessoas não têm correspondência na BNE; muitas não estão lá, outras têm o nome escrito de outra forma (por exemplo, forma galega na BD e castelhana na BNE).
- **O ficheiro da BNE é o descarregado em 12 de outubro de 2026.** A página do conjunto de dados indica última modificação em 19 de junho de 2025.

## Dúvidas em aberto

### 1. Datas que divergem da BD

A BD e a BNE dão anos diferentes. O script não propõe alterar o que já existe; é preciso decidir caso a caso.

| H-ID | Pessoa | Nascimento na BD | Na BNE | Na Wikidata |
|---|---|---|---|---|
| 3942 | Vidal Alvarinho, Ramiro | 1973 | 1975 | 1973 |
| 4167 | Figueroa Panisse, Adela | 1948 | 1947 | 1948 |
| 4551 | Pita, Emilio | 1907 | 1909 | — |
| 4722 | Carballeira, Johán | 1902 | 1903 | — |
| 5583 | Torres, Xohana | 1929 | 1931 | — |
| 5669 | Álvarez Blázquez, Emilio | 1919 | 1916 | — |
| 5786 | Cuña Novás, Manuel | 1924 | 1926 | — |
| 6382 | Campos Villar, Xabier | 1974 | 1973 | 1974 |
| 7496 | Vidal Martínez, Aurora | 1910 | 1911 | — |

Nas mortes: Domingo Campio Devesa Naveiro (BD 1895, BNE 1923) e Manuel Pardo de Andrade (BD 1823, BNE 1832).

### 2. Datas em que a BNE e a Wikidata divergem

O script propõe o ano da BNE. Em alguns casos é a mesma pessoa com datas diferentes nas duas fontes; noutros a Wikidata apanhou um homónimo.

| H-ID | Pessoa | BNE | Wikidata |
|---|---|---|---|
| 4996 | Menezes, Margareth | 1963 | 1962 |
| 5569 | Santamarina, Antón | 1928 | 1942 |
| 7763 | Uceda, Julia | 1926 | 1925 |
| 8293 | Pérez Gómez, José Juan | 1933 | 1891 |
| 8700 | Camba, Julio | 1882 | 1884 |
| 10313 | Fientosa, Francisco de | 1913 | 1912 |

Nas mortes: Manuel Vilanova (BNE 1944, Wikidata 2019) e María Guerrero (BNE 1927, Wikidata 1928). Prefere-se, nestes casos, não importar nada até verificar?

### 3. Género divergente entre a BD e a BNE

Em 14 pessoas o género não coincide. Em vários casos a BD parece estar errada; noutros pode ser a BNE, ou um homónimo.

| H-ID | Pessoa | BD | BNE | Confiança |
|---|---|---|---|---|
| 3000 | Romero, Medos | Male | Female | alta |
| 4366 | Caramés, Vari | Female | Male | alta |
| 4400 | Porto Mato, Andrea | Male | Female | alta |
| 4683 | Suras, Alberte | Female | Male | alta |
| 4773 | Botana Iglesias, Rocío | Female | Male | alta |
| 5292 | Jano, Andrea | Male | Female | alta |
| 7875 | Pagán, Alberte | Female | Male | alta |
| 8892 | Rodríguez Rial, Nel | Female | Male | alta |
| 4876 | Oro Claro, Alberte | Female | Male | sem confirmação |
| 5877 | Rueda Alonso, Margarita | Male | Female | sem confirmação |
| 6431 | Nunes, Airas | Female | Male | sem confirmação |
| 8261 | Payne, Keith | Male | Female | sem confirmação |
| 9478 | Yu, Jian | Male | Female | sem confirmação |
| 9969 | Álvarez Blanco, Palmar | Male | Female | sem confirmação |

O script não altera géneros existentes. A BNE também tem erros: no nível de confiança média, «Vázquez Vidal, Vicente» aparece como feminino.

### 4. ID da Wikidata divergente

| Pessoa | Na BNE | Na BD ou na pesquisa |
|---|---|---|
| Perec, Georges | Q157303 | BD: «T00:00:00Z» |
| Fidalgo Lareo, Pablo | Q112498707 | BD: Q12396938 |
| Santamarina Delgado, Antón | Q10963569 | BD: Q12383149 |
| Mouzo, Antón | Q55769568 | pesquisa: Q12383147 |
| Bello Sánchez, Juan | Q112504566 | pesquisa: Q71045767 |
| Xosé Tomás | Q19844282 | pesquisa: Q67179850 |
| Capdevila Vinaja, Gemma | Q53552044 | pesquisa: Q118818165 |
| López, Teresa | Q6004705 | pesquisa: Q52279955 |

- O valor de Georges Perec na BD é claramente um erro de preenchimento.
- Há dois registos Pessoa, «Santamarina, Antón» (5569) e «Santamarina Delgado, Antón», que a BNE liga ao mesmo item Q10963569. Podem ser um duplicado, ou pai e filho mal distinguidos.
- Nos casos «pesquisa», o ficheiro de importação usa o ID da BNE.

### 5. Que fazer com a confiança média

Os 673 registos de confiança média são nomes únicos na BNE, em geral corretos, mas sem confirmação. Não entraram na importação. Trariam mais 152 datas de nascimento, 470 géneros para conferência e 345 VIAF. Aceita-se importá-los, pelo menos para nomes com dois apelidos?

### 6. Os 74 casos de confiança baixa

Têm vários homónimos na BNE. A coluna «Outros candidatos BNE» do ficheiro completo lista-os com datas e identificador, para escolha manual.

### 7. Que campos importar

O ficheiro de importação traz datas, género, VIAF, ISNI e ID da Wikidata. A BD tem campos para VIAF e Wikidata (ID e URL); o ISNI e o identificador da BNE não têm campo próprio. Criam-se? O identificador da BNE seria a ligação mais direta, dado que os registos bibliográficos vêm de lá.

### 8. Precisão das datas

As datas propostas têm três formatos: ano (`1962`), ano e mês (`1970-10`) e data completa (`1964-07-30`). Convém confirmar que o Heurist aceita os três no mesmo campo. Alternativa: importar só o ano, que é o que a BNE garante.

### 9. Consultar a Wikidata pelos ID da BNE

A BNE dá o ID da Wikidata de 884 pessoas de confiança alta. Para as que a pesquisa por nome não encontrou, as datas completas podem ser lidas diretamente desses itens, sem risco de homónimos. Isso exigiria um pequeno acrescento ao script da Wikidata.

### 10. Outros dados da BNE por aproveitar

O ficheiro completo guarda ocupação, área de atividade, local de nascimento e de morte, país e língua. Interessa importá-los para a BD?

### 11. Pessoas sem género

Das 11 pessoas que tinham ficado sem género na operação anterior (ver `gender/NOTAS-genero-pessoas.md`), a BNE só resolve com confiança alta Caxigueiro (`Male`). Com confiança média indica `Male` para Lodeiro e Orballo. Os outros 34 géneros novos do ficheiro de importação são de pessoas que não constavam do CSV então preenchido.

### 12. Formas do nome

Parte das 506 pessoas sem correspondência pode estar na BNE com outra grafia (por exemplo «Xosé» na BD e «José» na BNE). Uma segunda passagem com equivalências de nomes próprios galego-castelhano poderia recuperar algumas, à custa de mais risco de homónimos.
