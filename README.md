# AQUA REDA — apoio local à revisão semanal

## Avaliação do repositório — 26 de outubro de 2026

Base inspecionada: `main`, commit `26c3dc0c7b3ee70983a7c94e3799283d79523371`.
A árvore continha a interface Streamlit, `requirements.txt` e a configuração de devcontainer. Não foram encontradas PRs abertas na consulta. A interface original assumia cinco colunas e não tinha fila, testes ou armazenamento de revisão. É aproveitável como base de um instrumento local de preparação, sem prova de adoção ou ligação ao processo oficial REDA.

## Executar

Recomendado: Python 3.12 num ambiente virtual.

```bash
python -m pip install -r requirements.txt
python -m streamlit run REDA_InterfaceGrafica_Streamlit.py
```

## Fluxo semanal implementado

1. Carregar um `.xlsx` e escolher a folha. Ficheiros inválidos apresentam erro; folhas vazias e colunas em falta não provocam acesso a colunas inexistentes.
2. Conferir as colunas disponíveis. Os cinco campos do catálogo são reconhecidos ignorando caixa, acentos e espaços. Outras designações podem ser associadas manualmente; alternativamente, criar campos vazios. As colunas adicionais são conservadas. A associação não valida o significado do conteúdo.
3. Selecionar explicitamente a coluna da data do pedido e, se existir, a do estado na fonte. Não se presume que uma data de edição seja a data de entrada, nem se converte um estado da fonte numa decisão local.
4. Introduzir o estado da revisão **local**, prioridade, bloqueios e próximo passo de cada recurso. Os campos começam vazios, com indicação de informação por introduzir/confirmar. Os IDs locais são referências técnicas aleatórias, não classificações nem IDs oficiais. Títulos ausentes têm uma referência à linha, sem inventar títulos.
5. Rever a fila: prioridade manual (Urgente, Alta, Normal, Baixa), depois maior antiguidade conhecida e ordem original em caso de empate. Sem prioridade fica no fim, por classificar. O destaque de pedidos antigos usa um limiar ajustável (30 dias inicialmente); não representa um prazo regulamentar. O cálculo usa a data corrente dos Açores. Datas ausentes, inválidas, numéricas ou futuras ficam por confirmar. Textos aceites: AAAA-MM-DD, DD/MM/AAAA, DD-MM-AAAA e AAAA-MM-DD HH:MM:SS; células Excel de data também são aceites.
6. Editar os campos do catálogo reconhecidos/associados, quando necessário. A lista de campos vazios serve de alerta, não de reprovação: por exemplo, vídeo/incorporação podem não se aplicar. Usar «Atualizar fila após edição» para atualizar a tabela imediatamente.
7. Guardar o Excel. O estado existe apenas na sessão até ser descarregado. Noutra semana, carregar o ficheiro exportado, selecionar `Recursos` e ativar **Restaurar notas de uma exportação desta aplicação**. Sem essa opção, começa uma nova revisão local.

A fila inclui todos os recursos importados com estado local desconhecido; o utilizador confirma quais aguardam realmente validação. «Revisão local concluída» apenas oculta o recurso na vista por defeito, reversível na opção de mostrar concluídos. Não significa aprovado nem rejeitado.

## Exportação e persistência

- `Recursos`: catálogo da folha selecionada e eventuais edições humanas, incluindo colunas adicionais e a coluna técnica reservada `__REDA_ID_LOCAL`.
- `Revisao_local`: o mesmo ID em `ID LOCAL`, notas locais e impressão do conteúdo `__REDA_CONTEUDO_SHA256_V1`, para retomar o trabalho independentemente da ordem das linhas.
- `Fila_semanal`: fotografia ordenada, incluindo concluídos, estado da fonte, antiguidade, avisos e campos por completar.

A exportação é uma cópia tabular, não preserva formatação, macros, fórmulas, outras folhas ou objetos do livro original. Texto que começa por `=` é guardado como texto. O original carregado não é escrito. A recuperação associa por ID persistente, nunca por posição ou título. Cada folha pode ser ordenada independentemente, movendo sempre a linha inteira, incluindo as colunas técnicas. A importação exige IDs preenchidos, únicos e com conjuntos iguais nas duas folhas; verifica ainda a impressão SHA-256 do conteúdo de cada recurso. Falhas interrompem toda a recuperação, sem atribuição parcial, e a interface apresenta um aviso. Não há reconciliação automática com novos ficheiros; um ficheiro novo inicia outra fila. A escolha de colunas de data/estado, associações manuais e o limiar devem ser confirmados em cada sessão; não são regras oficiais guardadas.

Não existe base de dados, gravação automática em disco, serviço de agendamento, acesso a Notion, chamadas ao REDA nem aprovação/rejeição automática. Para uso local, executar na própria máquina. Uma instalação Streamlit remota processará os ficheiros no respetivo servidor.

## Testes

```bash
python -m unittest discover -s tests -v
```

Dados exclusivamente fictícios. Cobertura: importação de Excel, colunas ausentes e variantes, valores incompletos, folha vazia, datas desconhecidas/inválidas/futuras, prioridades e desempates, separação dos estados, exportação/reimportação, texto semelhante a fórmulas e interação da interface (início, importação, criação de campos, prioridade e bloqueio).

Verificado na correção de 26 de outubro de 2026: 24 testes aprovados (`python -m unittest discover -s tests -v`) e compilação Python (`python -m compileall -q reda_queue.py REDA_InterfaceGrafica_Streamlit.py tests`). Dados exclusivamente fictícios; inclui três testes de interface Streamlit.

## Recuperação segura — limites e compatibilidade

- Exportações anteriores sem ID nas duas folhas e sem impressão do conteúdo não permitem provar a ligação. A recuperação automática é bloqueada, mesmo com contagens iguais. Conservar o original; conferir e transcrever as notas manualmente ou importar sem restaurar para iniciar uma revisão vazia. Não existe migração por posição nem por títulos semelhantes.
- Inserção/eliminação numa só folha, IDs vazios/repetidos ou conjuntos diferentes bloqueiam a recuperação. Alterações externas no catálogo, incluindo ordenação de células sem mover o ID, também bloqueiam. Para editar o catálogo e conservar as notas, restaurar primeiro, editar na aplicação e voltar a exportar: a impressão é recalculada sobre o Excel produzido.
- A impressão inclui todas as colunas do catálogo, não as notas humanas. É uma verificação de consistência, não uma assinatura ou proteção contra manipulação deliberada. Não editar colunas técnicas. Recursos com conteúdo integralmente idêntico só são distinguíveis pelos IDs; uma troca manual dos seus IDs não pode ser detetada pelo conteúdo.
- Remover o mesmo par ID/recurso de ambas as folhas deixa um subconjunto internamente consistente: não há histórico externo para detetar essa remoção conjunta. Uma troca integral entre livros de registos com ID e conteúdo coincidentes também não é distinguível. Conservar sempre a exportação original.
- A coluna `__REDA_ID_LOCAL` é reservada, omitida dos campos editáveis e regenerada com novos IDs ao escolher importar sem restaurar. Não a usar como coluna de dados próprios nem como identificador oficial REDA.
- Não há reconciliação entre catálogos semanais distintos. O hash não serve para procurar correspondências entre ficheiros e não estabelece identidade oficial. Essa funcionalidade continua dependente de critérios de identificação validados.

Os testes adicionais cobrem reordenação independente e simultânea, títulos repetidos, IDs duplicados/vazios nas duas folhas, substituição com igual contagem, inserção/eliminação em cada folha, alteração externa de conteúdo, recuperação de exportações novas, bloqueio de exportações antigas, sucessivas edições humanas/exportações, fórmulas como texto, datas/números/vazios, catálogo vazio e aviso de bloqueio na interface. Mantêm-se os testes de edição, prioridades e separação entre estados locais e oficiais.

## Ainda necessita de validação efetiva

- Experimentar um Excel real autorizado, confirmar cabeçalhos, tipos de datas e significado dos estados.
- Confirmar critérios humanos de urgência e o limiar de antiguidade.
- Confirmar quem usará a aplicação, onde será executada e como serão guardados os ficheiros.
- Validar a adequação à rotina REDA e a reabertura do Excel com a ferramenta habitual.

Os testes demonstram comportamento técnico com dados fictícios; não demonstram utilização efetiva, integração oficial, instalação ou aceitação operacional.

