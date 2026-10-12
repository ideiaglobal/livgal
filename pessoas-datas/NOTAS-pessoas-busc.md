# Cruzamento das pessoas com o catálogo de autoridades da BUSC

Esclarecimentos metodológicos e dúvidas em aberto da operação que procura as entidades **Pessoa** da exportação `Export_livpoesia_20261012104901.json` no catálogo de autoridades da Biblioteca Universitaria de Santiago de Compostela (BUSC), centrado em autorias galegas, para trazer datas de nascimento e morte e confrontá-las com as da BD, da BNE e da Wikidata.

- Script: `busc_pessoas.py` (usa funções de `bne_pessoas.py`)
- Entradas: a exportação JSON do Heurist; `pessoas-bne.csv` (resultado de `bne_pessoas.py`)
- Resultados: `pessoas-busc-importar.csv`, `pessoas-busc.csv`
- Cache das respostas do catálogo: `busc_cache.json`

Esta nota completa a `NOTAS-pessoas-datas.md` (Wikidata) e a `NOTAS-pessoas-bne.md` (BNE).

## O que foi pedido

Usar o catálogo de autoridades da BUSC para procurar dados, nomeadamente datas de nascimento ou morte, de autores galegos; e testá-lo em particular com os nomes para os quais não havia dados ou estes eram ambíguos.

## A fonte

| | |
|---|---|
| Catálogo | <https://cisug-usc.primo.exlibrisgroup.com/nde/authsearch?vid=34CISUG_USC:NDE&lang=gl> |
| Conteúdo declarado | mais de 46 000 nomes de pessoa, dos quais mais de 24 000 de autoras e autores galegos ou relacionados com a Galiza |
| Acesso | consulta nome a nome, pelo mesmo endereço que a página de pesquisa usa; sem autenticação |
| Data da consulta | 12 e 13 de outubro de 2026 |

Cada registo traz o nome com datas («Torres, Xohana, 1931-2017»), as formas alternativas do nome e as notas de fonte, que muitas vezes indicam local e ano de nascimento. Alguns (81 dos encontrados) trazem ainda um campo de datas codificadas, ocupação, área de atividade e lugar.

## Esclarecimentos: como foi feito

### Pesquisa e coincidência

- Pesquisa-se cada nome da BD («Apelidos, Nome») entre os nomes pessoais do catálogo; a pesquisa devolve os registos que contêm essas palavras (até 150).
- Só se aceitam os registos cujo nome, ou uma das formas alternativas, coincide exatamente com o nome ou as variantes da BD, sem acentos, maiúsculas nem pontuação.
- A coluna «Coincidência» indica se foi pelo nome principal («nome») ou por uma forma alternativa («variante»).
- Foram pesquisadas as 2708 pessoas, uma a uma, com uma pausa entre pedidos; a execução completa demorou cerca de 35 minutos.

### Confirmação independente

| Evidência | O que significa | Casos (confiança alta) |
|---|---|---|
| ano BNE | o ano de nascimento da BUSC é o do registo da BNE (confiança alta) | 894 |
| ano MARC | o ano aparece junto ao nome nos campos MARC dos livros da pessoa | 766 |
| ano BD | o ano é o que já está na BD | 455 |
| título | um título de um livro da pessoa é citado nas fontes do registo | 273 |

Uma pessoa pode ter várias evidências. A Wikidata não entra como evidência, só no confronto.

### Níveis de confiança

| Confiança | Pessoas | Critério |
|---|---|---|
| alta | 1199 | um único registo com evidência |
| média | 388 | sem evidência, mas só há um registo com esse nome |
| baixa | 22 | vários registos possíveis |
| sem correspondência | 1099 | o nome não está no catálogo, ou não coincide exatamente |

### Confronto

Comparam-se os anos de quatro fontes: BD, BNE (confiança alta), Wikidata (ligação fiável) e BUSC (confiança alta).

| Nascimento | Pessoas |
|---|---|
| coincidem as quatro fontes | 278 |
| coincidem BNE, Wikidata e BUSC | 332 |
| coincidem BNE e BUSC | 167 |
| coincidem BD, BNE e BUSC | 112 |
| coincidem Wikidata e BUSC | 69 |
| outras coincidências | 232 |
| só BUSC | 126 |
| só Wikidata | 180 |
| só BNE | 125 |
| só BD | 19 |
| divergem | 28 |

Nas mortes, divergem 6.

## Resultado para os nomes sem dados ou ambíguos

| Grupo | Pessoas | BUSC alta | BUSC média | BUSC baixa | Sem correspondência | Com ano de nascimento (alta + média) |
|---|---|---|---|---|---|---|
| Sem dados | 494 | 69 | 69 | 0 | 356 | 55 + 28 |
| Ambíguas | 672 | 83 | 162 | 11 | 416 | 71 + 98 |
| Divergentes | 19 | 12 | 1 | 1 | 5 | — |

- **Sem dados:** pessoas sem data de nascimento na BD e sem nenhum candidato na BNE nem na Wikidata.
- **Ambíguas:** pessoas que só tinham candidatos de confiança média ou baixa nessas duas fontes.
- **Divergentes:** as 15 datas de nascimento e 4 de morte em que as fontes anteriores não coincidiam.

Nas ambíguas em que é possível comparar anos, a BUSC coincide com o candidato anterior em 71 casos e discorda em 34. Nas discordâncias, a BUSC aponta em geral para a pessoa galega e as outras fontes para um homónimo (por exemplo «Rubio, Antonio»: 1953 na BUSC, 1717 na BNE, 1882 na Wikidata).

## O que a BUSC acrescenta

`pessoas-busc-importar.csv` tem 255 pessoas com datas que a BD não tinha e que `pessoas-bne-importar.csv` não propunha.

| Confiança BUSC | Nascimentos novos | Mortes novas |
|---|---|---|
| alta | 126 | 12 |
| média | 126 | 7 |

Efeito acumulado nas pessoas com data de nascimento:

| | Pessoas | % |
|---|---|---|
| Na BD hoje | 586 | 21,6 % |
| Com BNE + Wikidata | 1542 | 56,9 % |
| Mais BUSC, confiança alta | 1668 | 61,6 % |
| Mais BUSC, confiança média | 1794 | 66,2 % |

A BUSC só dá anos. O ficheiro inclui o identificador do registo da BUSC, a evidência e as fontes citadas, para conferência.

## Limitações a ter em conta

- **A confiança média precisa de revisão.** São nomes únicos no catálogo sem outra confirmação. Na amostra vista há casos duvidosos: «Roel, Manuel» ficou ligado a «Roel, Xiao, 1954-» por uma forma alternativa do nome, e «Montes, María» a uma professora de Filologia Italiana.
- **Coincidência exata.** Não apanha nomes abreviados ou com grafia diferente: «Pérez Gómez, José Juan» na BD não coincide com «Pérez Gómez, José J., 1894-1947» no catálogo.
- **Nomes muito comuns.** A pesquisa devolve no máximo 150 registos por nome; para nomes como «Rodríguez, Luis» o registo certo pode ficar de fora.
- **A BUSC também diverge.** Em 11 casos a BUSC é a única fonte a dar um ano diferente das outras (ver dúvida 2); pode ser erro do catálogo ou um homónimo.
- **Acesso não documentado.** O endereço consultado é o que a página de pesquisa usa internamente, não uma API pública documentada; pode mudar sem aviso. O catálogo declara estar em revisão contínua.

## Dúvidas em aberto

### 1. Casos em que a BUSC desempata

| H-ID | Pessoa | Divergência anterior | BUSC | Fica do lado de |
|---|---|---|---|---|
| 3942 | Vidal Alvarinho, Ramiro | BD e Wikidata 1973, BNE 1975 | 1973 | BD e Wikidata |
| 4167 | Figueroa Panisse, Adela | BD e Wikidata 1948, BNE 1947 | 1948 | BD e Wikidata |
| 4722 | Carballeira, Johán | BD 1902, BNE 1903 | 1902 | BD |
| 5669 | Álvarez Blázquez, Emilio | BD 1919, BNE 1916 | 1919 | BD |
| 7496 | Vidal Martínez, Aurora | BD 1910, BNE 1911 | 1910 | BD |
| 4551 | Pita, Emilio | BD 1907, BNE 1909 | 1909 | BNE |
| 5583 | Torres, Xohana | BD 1929, BNE 1931 | 1931 | BNE |
| 5786 | Cuña Novás, Manuel | BD 1924, BNE 1926 | 1926 | BNE |
| 6382 | Campos Villar, Xabier | BD e Wikidata 1974, BNE 1973 | 1973 | BNE |
| 8700 | Camba, Julio | BNE 1882, Wikidata 1884 | 1882 | BNE |
| 7981 | Pardo de Andrade, Manuel (morte) | BD 1823, BNE 1832 | 1832 | BNE |

- Em quatro casos (Pita, Torres, Cuña Novás, Pardo de Andrade) duas fontes independentes contradizem a data da BD. Corrige-se a BD?
- Em Campos Villar, a fonte citada pela BUSC dá a data completa (28 de janeiro de 1973), contra o 1974 da BD e da Wikidata.
- **Vilanova, Manuel (2987):** a BUSC dá-o como nascido em 1944, sem morte. O «1944» que a BNE tem como ano de morte é, portanto, o de nascimento; a morte em 2019 vem só da Wikidata.
- **Uceda, Julia (7763):** o registo da BUSC não tem datas no nome, mas a fonte citada diz 1925, como a Wikidata.
- **Santamarina, Antón (5569):** a BUSC tem 1942, como a Wikidata, mas com dois registos possíveis.

### 2. Casos em que a BUSC é a fonte divergente

| H-ID | Pessoa | Outras fontes | BUSC |
|---|---|---|---|
| 3258 | Martínez-Conde, Ricardo | BD, BNE e Wikidata 1949 | 1951 |
| 4085 | Lugrís, Urbano | BNE e Wikidata 1908 | 1906 |
| 4091 | Fandiño Veiga, Xosé Ramón | Wikidata 1946 | 1947 |
| 6384 | Acuña, Manuel Luís | BD e BNE 1899 | 1900 |
| 7115 | Sánchez García, Francisco | BNE e Wikidata 1874 | 1876 |
| 8113 | Gómez de la Cueva, José | BNE 1903 | 1902 |
| 8131 | Penalta, Soledad | Wikidata 1943 | 1944 |
| 8533 | Lloria, Matilde | BD e BNE 1912 | 1914 |
| 8863 | Vidal Villaverde, Manuel | BNE e Wikidata 1946 | 1944 |
| 9957 | Díaz de Herrera, Gabino | BNE e Wikidata 1906 | 1908 |
| 3808 | Llompart, Josep M. (morte) | BD e BNE 1993 | 1995 |
| 6933 | Barros, Tomás (morte) | BNE 1989 | 1986 |

São diferenças de um a três anos, provavelmente erros de uma das fontes e não homónimos.

### 3. Homónimos prováveis

Três casos com dezenas de anos de diferença indicam que uma das fontes ligou a pessoa errada:

| H-ID | Pessoa | Fontes |
|---|---|---|
| 4441 | Rodríguez Gómez, Fernando | BNE 1867, BUSC 1966 |
| 5383 | Costa, Luis | BNE 1879, BUSC 1968 |
| 6605 | Sandoval, Ramón | BD e Wikidata 1931, BUSC 1961 |

É preciso ver os livros de cada um para decidir. Em «José Gómez de la Cueva» e «Johán Carballeira» (pseudónimo do mesmo autor), a BD tem dois registos Pessoa para a mesma pessoa.

### 4. Importar a confiança média?

As 126 datas de nascimento de confiança média quase duplicam o contributo da BUSC, mas exigem conferência pelas fontes citadas. Prefere-se importar só as de confiança alta e rever as outras à mão?

### 5. Datas completas nas notas de fonte

As notas de fonte da BUSC trazem muitas vezes a data ou o local completos («Naceu en Bralo, Concello de Rois, o 28 de xaneiro de 1973»). O script guarda o texto mas só usa o ano do nome. Interessa extrair datas completas e locais de nascimento a partir dessas notas?

### 6. Pessoas sem correspondência

1099 pessoas não têm registo com nome exatamente igual. Parte são pessoas de fora da Galiza, que o catálogo não cobre; parte estão lá com outra forma do nome. Uma segunda passagem com coincidência aproximada (iniciais, segundo apelido em falta) recuperaria algumas, à custa de mais risco de homónimos.

### 7. Um ficheiro de importação único

Há agora dois ficheiros de importação complementares (`pessoas-bne-importar.csv` e `pessoas-busc-importar.csv`). Pode gerar-se um único, com uma data por pessoa e a indicação da fonte, aplicando uma regra de prioridade entre BD, BNE, BUSC e Wikidata. Qual deve ser a ordem de prioridade? Para autores galegos, a BUSC parece a mais fiável nos casos de divergência.

### 8. Guardar o identificador da BUSC na BD

O identificador do registo de autoridade da BUSC permite voltar ao registo e acompanhar correções futuras. A BD não tem campo para ele.

### 9. Guardar a cache no repositório?

`busc_cache.json` ocupa cerca de 1,9 MB e permite reproduzir os resultados sem voltar a consultar o catálogo. Como o catálogo está em revisão contínua, uma nova consulta pode dar resultados diferentes.
