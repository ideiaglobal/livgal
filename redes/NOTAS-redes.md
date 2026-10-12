# Redes de relações: prologuistas, autores/as e editoras

Esclarecimentos metodológicos e dúvidas em aberto da operação que constrói duas redes de relações a partir da exportação `Export_livpoesia_20261012104901.json`, usando as associações diretas de autoria dos livros e os registos de relação (*relationships*).

- Scripts: `redes.py` (ficheiros de exportação) e `redes_html.py` com `redes_modelo.html` (página interativa)
- Resultados: quatro ficheiros por rede (`rede1-prologuistas-autores…` e `rede2-autores-editoras…`) e a página `redes.html`

## O que foi pedido

1. Uma rede que mostre as ligações entre as pessoas prologuistas e as pessoas autoras de livros individuais originais em galego, ativas no período.
2. Uma rede que mostre as ligações entre as pessoas autoras de livros individuais (ativas no período ou não) e as editoras.

Como ainda não está definido quem são as pessoas ativas, as redes foram construídas com o conjunto completo, deixando em cada ligação os dados necessários para filtrar depois.

## Dados de partida

| | |
|---|---|
| Livros | 3149 |
| Livros com uma pessoa no campo Autoria | 2570 |
| Livros com duas pessoas no campo Autoria | 12 |
| Livros sem ninguém no campo Autoria | 567 |
| Pessoas com autoria direta | 1114 |
| Registos de relação pessoa-livro | 4309 |

Função indicada nos registos de relação:

| Função | Relações |
|---|---|
| nd (não definida) | 3174 |
| autor/a | 958 |
| prologuista | 52 |
| ilustrador/a | 38 |
| editor/a | 35 |
| tradutor/a | 26 |
| outras | 26 |

## Esclarecimentos: como foi feito

### Livro individual

Considera-se **livro individual** o que tem exatamente uma pessoa no campo «Autoria». A etiqueta `individual a priori` existe em 312 livros, mas não foi usada como critério por cobrir só uma parte; vai na coluna de etiquetas, para filtrar.

### Papel de prologuista

O campo «Função» do registo de relação só diz «prologuista» em 52 casos, e em 3174 está por definir. Para os casos por definir, o script lê a função nos campos MARC do livro («Autoria (marc_map)» e «Autores secundários (marc_map)»):

- **Código MARC:** o código de função a seguir ao nome, com ou sem datas pelo meio, como em «Alvarez Cáccamo, Xosé María, 1950- , pr.».
- **Menção de responsabilidade:** uma expressão de prólogo seguida do nome em ordem direta, como em «prólogo, Xosé María Álvarez Cáccamo». Expressões reconhecidas: prólogo, limiar, introdución, presentación, prefacio, estudo introdutorio, nota preliminar, palabras previas.

A comparação ignora acentos e maiúsculas e usa o nome completo e as variantes da pessoa. A função «introduçom» do registo de relação conta como prólogo. Os epílogos e posfácios ficam à parte e não entram na rede.

Depois desta leitura, as relações de pessoas fora do campo Autoria ficam assim:

| Papel | Relações |
|---|---|
| nd (continua por definir) | 1448 |
| autor/a | 988 |
| ilustrador/a | 586 |
| prologuista | 470 |
| editor/a | 396 |
| tradutor/a | 225 |
| diretor/a | 69 |
| fotógrafo/a | 39 |
| outros | 37 |

### Rede 1: prologuistas → autores/as

- Uma ligação vai de quem prologa para o autor ou a autora do livro individual prologado. É uma rede dirigida.
- O peso da ligação é o número de livros.
- Dos 470 prólogos identificados, 344 são em livros individuais e entram na rede; os restantes são em livros coletivos ou sem autoria direta.

| | |
|---|---|
| Pessoas | 394 |
| Ligações | 327 |
| Prólogos | 344, em 315 livros |
| Só prologuistas | 175 |
| Só autores/as prologados | 181 |
| Prologuistas e prologados | 38 |

Origem do papel nos 344 prólogos:

| Origem | Prólogos |
|---|---|
| código MARC | 300 |
| menção de responsabilidade | 31 |
| registo de relação (preenchido à mão) | 13 |

### Rede 2: autores/as — editoras

- Uma ligação une o autor ou a autora de um livro individual à editora desse livro. É uma rede bipartida, não dirigida.
- O peso é o número de livros. Um livro coeditado gera uma ligação com cada editora.
- As editoras agrupam-se pelo campo «Nome normalizado» do próprio JSON, de modo que as variantes do mesmo selo são um só nó (os 37 registos da Xunta de Galicia, por exemplo). Uma editora sem nome normalizado fica com o seu nome.
- Os identificadores levam um prefixo (`P` para pessoas, `E:` para editoras) para não colidirem. Nas pessoas, a coluna «H-ID» traz o identificador do registo; nas editoras, traz os H-ID de todos os registos agrupados.

| | |
|---|---|
| Pessoas | 1091 |
| Editoras (nomes normalizados) | 417, a partir de 567 registos |
| Ligações | 2055 |
| Pares livro-editora | 2637 |

### Ficheiros

| Ficheiro | Conteúdo |
|---|---|
| `*_nos.csv` | nós, com género, anos de nascimento e morte e contagens; nas editoras, nome normalizado e anos de atividade |
| `*_arestas.csv` | ligações agregadas, com peso, primeiro e último ano e H-ID dos livros |
| `*_arestas-por-livro.csv` | uma linha por livro, com título, ano, natureza da edição, tradução, língua fonte, editora e etiquetas |
| `*.gexf` | a rede completa num só ficheiro, com os atributos dos nós e das ligações |

Os CSV usam as colunas `Id`, `Label`, `Source`, `Target` e `Weight`, que o Gephi reconhece na importação.

### Página interativa

`redes.html` abre-se diretamente no navegador, sem instalar nada e sem ligação à internet: os dados e a disposição dos nós vão dentro do ficheiro.

- **Separadores:** uma rede de cada vez.
- **Filtros:** intervalo de anos, só livros com uma etiqueta, excluir livros com uma etiqueta, excluir traduções e mínimo de livros por ligação. Os filtros aplicam-se aos livros; as ligações e o tamanho dos nós recalculam-se.
- **Exploração:** arrastar para mover, roda do rato para aproximar, passar o rato para ver o nome, clicar num nó para ver no painel lateral as suas ligações e os livros de cada uma. A caixa «Procurar» leva a um nome.
- **Cores:** na rede 1, prologuista, autor/a prologado/a e quem tem os dois papéis; na rede 2, pessoa e editora. Na rede 1 as cores recalculam-se com os filtros.
- **Disposição:** calculada uma vez por `redes_html.py` (algoritmo de forças, ao estilo do ForceAtlas 2) e fixa; os filtros escondem ligações mas não mudam as posições.

Para atualizar a página com uma nova exportação, corre-se `python3 redes_html.py <export.json> .` (demora cerca de meio minuto).

### Como visualizar no Gephi

No Gephi: abrir o `.gexf`; na vista geral, aplicar a disposição ForceAtlas 2; dimensionar os nós pelo grau (ou, na rede 1, pelos prólogos escritos ou recebidos). Na rede 2, colorir pelo atributo «Tipo» separa pessoas de editoras.

Para filtrar por ano, etiqueta ou tradução, parte-se do ficheiro `*_arestas-por-livro.csv`, eliminam-se as linhas que não interessam e importa-se o resultado como tabela de arestas.

## Limitações a ter em conta

- **A rede 1 está incompleta por defeito.** Ficam 1448 relações sem função identificada, e entre elas haverá prologuistas. A leitura dos campos MARC só apanha o que está escrito de forma reconhecível.
- **A função lida no MARC não foi verificada caso a caso.** Assenta em padrões de texto; pode haver falsos positivos quando o nome aparece perto de um código que pertence a outra pessoa.
- **Prólogos em livros coletivos ficam de fora.** São 126 prólogos identificados em livros sem autoria individual.
- **Reedições pesam.** Os autores clássicos têm muitas ligações por serem reeditados: Rosalía de Castro recebe 14 prólogos e está ligada a 34 editoras. Não significa atividade no período.
- **Auto-edições.** Com o nome normalizado, as 101 auto-edições ficam num só nó, «Edição de autor», ligado a 98 autores. É útil para ver quem se autoeditou, mas não é uma editora.
- **Pessoas duplicadas.** Registos Pessoa repetidos aparecem como nós distintos (por exemplo «Carballeira, Johán» e «Gómez de la Cueva, José», ver `pessoas-datas/NOTAS-pessoas-busc.md`).

## Dúvidas em aberto

### 1. Quem conta como «ativa no período»

A etiqueta `autoria ativa` está nos livros (2517), não nas pessoas. É preciso definir a regra: basta um livro com essa etiqueta? Ou é uma condição biográfica (viva e a publicar entre 2000 e 2019)? Com as datas de nascimento e morte agora recolhidas, pode calcular-se uma aproximação (por exemplo, pessoas não falecidas antes de 2000).

### 2. Que são «originais em galego»

O JSON marca as traduções (247 livros) e a língua fonte, mas não tem um campo com a língua do livro. Excluir traduções é imediato; excluir livros escritos noutras línguas exige uma etiqueta ou um campo. As etiquetas `traduçom_para`, `edição_crítica` e `poesia_infantil` podem servir de filtros adicionais; diga quais se aplicam.

### 3. A condição «ativa» aplica-se a quem?

Na rede 1, a pessoa ativa é a autora, a prologuista, ou ambas? Uma autora ativa pode ser prologada por alguém já falecido (prólogo recuperado) e vice-versa.

### 4. Completar a função nas relações

As 1448 relações por definir e as cerca de 400 funções de prologuista lidas no MARC podiam ser carregadas na BD, para o campo «Função» deixar de estar em «nd». O script pode gerar um CSV de importação com o H-ID da relação e a função proposta. Interessa?

### 5. Outros papéis

A mesma leitura dá ilustradores (586), editores literários (396) e tradutores (225). Podem construir-se redes equivalentes (por exemplo, tradutores e autores traduzidos).

### 6. Editoras: registo ou nome normalizado (resolvido)

Decidido: usa-se o nome normalizado, tanto nos ficheiros exportados como na página. Fica por decidir se o nó «Edição de autor» deve manter-se, ser excluído ou voltar a separar-se por autor.

### 7. Livros com duas pessoas em Autoria

Há 12 livros com duas pessoas no campo Autoria, que ficaram fora das duas redes por não serem individuais. Incluem-se?

### 8. Livros sem autoria direta

Os 567 livros sem ninguém no campo Autoria têm 958 relações com a função «autor/a»; são na maioria coletivos. Ficam fora por definição, mas podiam dar uma terceira rede, de coautoria em volumes coletivos.

### 9. Publicar a página

A página `redes.html` pode ser servida pelo GitHub Pages a partir do repositório, o que daria um endereço público para a partilhar. Interessa?
