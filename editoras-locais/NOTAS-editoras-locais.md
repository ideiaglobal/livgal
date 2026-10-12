# Associação de locais às editoras

Esclarecimentos metodológicos e dúvidas em aberto da operação que atribui a cada **Editora** o local (ou locais) de publicação dos seus livros, para importar na BD por correspondência de H-ID.

- Script: `editoras_locais.py`
- Entradas: `livpoesia-t54-livro-2026-10-12_19-15.csv`, `livpoesia-t53-editora-2026-10-12_19-11.csv`, `livpoesia-t12-local-2026-10-12_19-12.csv`
- Resultados: `editoras-com-local.csv`, `editoras-varios-locais.csv`

## O que foi pedido

Ler no ficheiro de livros as colunas de editora e de local de publicação, estabelecer a correspondência com o ficheiro de locais e criar no ficheiro de editoras uma coluna nova com o H-ID do local (e, opcionalmente, o nome). As editoras associadas a mais de um local vão para um segundo ficheiro, para exame e eventual importação.

## Dados de partida

| | |
|---|---|
| Editoras | 729 |
| Locais | 195 |
| Livros | 3149 |
| Livros sem editora | 42 |
| Livros sem local | 57 |
| Livros com várias editoras | 183 |
| Livros com várias editoras e vários locais | 55 |
| Livros com uma editora e vários locais | 12 |

Todos os H-ID de editora e de local que aparecem no ficheiro de livros existem nos ficheiros respetivos.

## Resultado

| Situação | Editoras | Onde ficaram |
|---|---|---|
| Um único local | 611 | `editoras-com-local.csv`, colunas preenchidas |
| Mais de um local | 102 | `editoras-varios-locais.csv` |
| Sem local nenhum | 16 | `editoras-com-local.csv`, colunas vazias |

## Esclarecimentos: como foi feito

### Correspondência

A ligação é feita só por H-ID (`Editora H-ID` e `Local de publicação H-ID` do ficheiro de livros). Os nomes não entram na correspondência; servem apenas para leitura.

### Três níveis de evidência

Nos livros com várias editoras e vários locais, a ordem das duas colunas não é fiável: no livro 105, «Asociación Cultural e Xuvenil de Ramirás|Edizer» aparece com «Santiago de Compostela|Ramirás». Não se pode, por isso, emparelhar por posição. Usaram-se três níveis:

| Nível | Situação do livro | Leitura |
|---|---|---|
| 1. Direta | uma só editora | os locais do livro são da editora |
| 2. Coedição | várias editoras, um só local | o local vale para todas as coeditoras |
| 3. Ambígua | várias editoras, vários locais | não se sabe que local é de que editora |

Para cada editora usa-se **só o nível mais fiável que ela tiver**. Uma editora com livros a solo ignora, portanto, os locais que só lhe aparecem em coedições.

| Nível usado | Um único local | Vários locais |
|---|---|---|
| Direta | 564 | 77 |
| Coedição | 47 | 2 |
| Ambígua | — | 23 |

### Ficheiro `editoras-com-local.csv`

- Tem as 729 editoras, na mesma ordem e com o mesmo formato do original (UTF-8 com BOM, separador de tabulação).
- As duas colunas originais não foram alteradas.
- Colunas novas: `Local H-ID` e `Local nome`.
- Só estão preenchidas as 611 editoras com um único local. As 102 com vários locais e as 16 sem local ficam com as colunas vazias.

### Ficheiro `editoras-varios-locais.csv`

Uma linha por editora, com:

| Coluna | Conteúdo |
|---|---|
| `Local H-ID (todos)` / `Local nome (todos)` | todos os locais, separados por `\|`, do mais para o menos frequente |
| `Local H-ID (mais frequente)` / `Local nome (mais frequente)` | o local com mais livros; vazio quando há empate |
| `N.º de livros por local` | por exemplo «Santiago de Compostela: 51\|A Coruña: 1» |
| `Tipo de evidência` | direta, coediçom ou ambígua |
| `Livros H-ID por local` | H-ID dos livros de cada local (até 15), para consulta |

Das 102 editoras, 59 têm um local mais frequente e 43 estão empatadas (19 de evidência direta e 24 das 25 de coedição ou ambíguas).

## O que se observa no ficheiro de revisão

- **Local dominante com casos isolados.** Muitas editoras têm quase todos os livros num local e um ou dois noutro (Positivas: Santiago 51, A Coruña 1; Follas Novas: Santiago 76, A Coruña 1; Toxosoutos: Noia 75 e um livro em cada um de três outros locais). Os casos isolados podem ser erros no registo do livro.
- **Mudanças de sede ou locais vizinhos.** Espiral Maior tem Culleredo 121, A Coruña 119, Rutis 11, O Burgo 4 e Ferrol 1; Biblos tem Cesuras 10, A Coruña 2 e Oza-Cesuras 1. Aqui os vários locais parecem reais.
- **Registos genéricos.** «O autor» (H-ID 3669) aparece com 8 locais, porque agrupa auto-edições de pessoas diferentes.

## Dúvidas em aberto

### 1. Editoras com local atribuído só por coedição (47)

Estão no ficheiro principal sem marca que as distinga das de evidência direta. Confirma-se que o local do livro coeditado deve ser importado para todas as coeditoras? Se for útil, acrescenta-se uma coluna com o tipo de evidência.

### 2. Que importar quando há vários locais

Para as 102 editoras do segundo ficheiro, há que decidir entre importar todos os locais (valor múltiplo), só o mais frequente, ou corrigir primeiro os livros. O campo de local da editora na BD admite valores múltiplos?

### 3. Editoras com evidência ambígua (23)

Só aparecem em livros com várias editoras e vários locais. É preciso atribuir o local à mão. Exemplos: Papelesmínimos (Madrid ou Santiago de Compostela), Radio Galega (Padrón ou Santiago de Compostela), Caixanova (Galiza ou Vigo).

### 4. Locais que não são localidades

Alguns registos de local são regiões ou países. Seriam importados como local da editora tal como estão.

No ficheiro principal (15 editoras):

| Local | Editoras |
|---|---|
| Galiza | Editora 3D1T0R4; ALGA, Activadores da Lingua; Xalundes Grupo Surrealista Galego; Gelría; Nesto Pilán; Finis Terrae Ediciones; Quequeres; Xefatura Superior de Policía de Galicia; Xosé María Guillén Rodríguez; Ediciones Anxelo Novo; Lulu.com |
| España | Chiado Editorial |
| Japón | Ronso; Secretaría de Estado de Cultura, Ministerio de Cultura, Gobierno de España |
| Valdeorras | Cupire Padesa |

No ficheiro de revisão, «Galiza» aparece como um dos locais de Galaxia, Centro PEN de Galicia, Litoral das Rías, Técnicas & Gramaxe, Caixanova, X. García, «O autor» e Proxecto de Unión Libre; «Brasil» em Editora Urutau; «Condado» em S.C.D. Condado; «La Alpujarra» em Trifolium; «Isla de San Borondón» em Liliputienses.

### 5. Local do livro ou sede da editora?

O local de publicação de um livro nem sempre é a sede da editora (por exemplo, o Ministerio de Cultura espanhol fica com «Japón» por causa de um único livro). A operação assume que são o mesmo; convém ter isso presente ao importar.

### 6. Editoras sem local (16)

Não têm livros com local, ou não têm livros:

Loaira; Arteu; Asociación Petón do Lobo; C. Cuesta; Club de Opinión Portocelo; Perseidas Editor SLU; Momán Noval, Alberte; Xunta de Confrarías da Semana Santa de Viveiro; N. Fernandez; Atlantia Edicións; Ricardo Seixo Fernández; Non ou edicións; Son Relanzo; Pepitas de Calabaza; Arc Publications; Dial Discos.

### 7. Livros a rever

- 57 livros sem local de publicação.
- 42 livros sem editora.
- 12 livros com uma só editora e vários locais: os dois locais foram atribuídos à editora.

### 8. Editoras que já têm local na BD

Na exportação JSON de 12 de outubro, 4 registos Editora já tinham o campo «Location (places)» preenchido. Convém verificar que a importação não os duplica nem os substitui indevidamente.
