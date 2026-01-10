# OBSERVAÇÕES (REVISÃO PROFUNDA) — ARQUITETURA CMSYS (SQL SERVER)

## 0) FATOS OBJETIVOS EXTRAÍDOS DO EXCEL
- Schemas: 16 (todas as tabelas listadas estão em `dbo`)
- Tabelas: 800
- Colunas: 11.092
- Primary Keys: 2.417 registros (PKs em 742 tabelas)
- Foreign Keys: 3.629 registros
- Índices: 593
- Views: 3

Padrões fortes de naming:
- Prefixos dominantes: `CD_` (631 tabelas) e `OP_` (135 tabelas)
  - `CD_` tende a “cadastro/dimensão operacional”
  - `OP_` tende a “operações/movimento/processo”

---

## 1) PADRÃO DE MODELAGEM (LEGADO)
O banco foi desenhado como OLTP enterprise tradicional:
- Muitos cadastros auxiliares (tabelas de parametrização e “códigos”)
- Muitas regras embutidas no próprio modelo (chaves compostas, escopos por empresa/filial)
- Forte orientação a processos internos e integrações

Isso é robusto para operação, mas custa caro para evoluir e para analytics.

---

## 2) CHAVES PRIMÁRIAS (O MAIOR ALERTA)
### Evidência
- 97,0% das tabelas com PK possuem PK composta (mais de 1 coluna).
- Colunas mais frequentes em PK:
  - `Cd_Empresa` aparece em 718 PKs (praticamente onipresente)
  - `Cd_Filial` aparece em 206 PKs
  - Outros: `Nr_Sequencia`, `Cd_Produto`, `Nr_Pedido`, etc.

### Implicações
- Modelo fortemente “scoped”: quase tudo é identificado por (empresa, filial, …).
- ORM e APIs ficam mais complexos (IDs grandes, joins chatos, endpoints difíceis).
- Migração/refatoração vira dor se você tentar copiar 1:1.

### Diretriz para a arquitetura alvo
- Manter o conceito de multi-empresa/multi-filial (tenant/branch), mas:
  - usar PK surrogate (id único) na maioria das tabelas
  - manter `tenant_id`/`empresa_id` como coluna + índice
  - aplicar UNIQUE constraints para garantir as chaves naturais quando fizer sentido

---

## 3) DENSIDADE DE RELACIONAMENTOS (FKs)
### Evidência
- 3.629 FKs no total
- Tabelas mais “conectadas” (muitos FKs) sugerem núcleo funcional:
  - `CD_Parametro_Filial` (77)
  - `OP_Lancamento_Financeiro` (51)
  - `CD_SOM` (47)
  - `OP_Lancamento_Pagamento_Parcela` (32)
  - `CD_Pedido_Venda` (31)
  - `CD_Pedido_Venda_Item` (27)
  - `CD_Cliente` (22)
  - `CD_Produto` (21)

### Implicações
- O núcleo do ERP está muito bem amarrado (bom sinal).
- Qualquer mudança no núcleo precisa ser feita por “estrangulamento” (migrar por módulos),
  não por big-bang.

---

## 4) “TABELAS NÚCLEO” PROVÁVEIS (PARA VOCÊ SEGUIR)
Com base em PK/FK e padrão de naming, as famílias centrais para autopeças tendem a ser:
- Produto: `CD_Produto` + atributos/preços/grade/lote/parametrizações
- Cliente/Pessoa: `CD_Cliente` (e possivelmente outras de pessoa/fornecedor/funcionário)
- Vendas: `CD_Pedido_Venda` e `CD_Pedido_Venda_Item`
- Financeiro: `OP_Lancamento_Financeiro` e parcelas/pagamentos
- Filial/Parâmetros: `CD_Parametro_Filial` (muita regra e comportamento por filial)

Diretriz: começar mapeando essas 8–12 tabelas e suas dependências diretas.

---

## 5) RISCO DE “GENERICÃO DE ERP”
O volume de `CD_` indica:
- muito cadastro auxiliar (tabelas de apoio, integrações, parametrização, campanhas, etc.)
- parte grande disso não é essencial para o MVP de autopeças

Diretriz:
- não tentar portar tudo
- classificar tabelas do legado em:
  - CORE (MVP): produto, cliente, pedido, estoque, financeiro
  - SUPPORT: parâmetros e auxiliares necessários
  - LEGACY/NO-MVP: integrações, módulos periféricos, customizações antigas

---

## 6) ESTOQUE, STATUS E HISTÓRICO (RISCO FUNCIONAL)
Mesmo sem “ler lógica de triggers/procs”, a modelagem típica desse padrão sugere:
- saldo e status tendem a ser “estado atual”
- histórico tende a ser parcial, espalhado ou inexistente

Diretriz para o alvo:
- separar explicitamente:
  - estado atual (tabelas operacionais)
  - eventos (movimentações, mudanças de status)
  - snapshots (ex.: estoque diário, preço diário, custo médio)

---

## 7) ESCALABILIDADE E ANALYTICS (COMO FAZER DIREITO)
### O que não fazer
- analytics diretamente em OLTP legado/portado
- “encher” o OLTP com colunas derivadas para relatório

### O que fazer
- OLTP limpo (transação)
- Camada analítica separada:
  - Bronze/Silver/Gold (mesmo que no início seja simples)
  - star schema desde cedo para vendas/estoque/financeiro
- Métricas precisam de “grão” definido:
  - item de pedido por dia/filial/produto
  - eventos de estoque por operação
  - títulos financeiros por competência/pagamento

---

## 8) DECISÃO TÉCNICA (BATER MARTELO)
- Usar a arquitetura como:
  - referência de domínio
  - mapa de relacionamento real
  - checklist de edge cases
- Não copiar 1:1 por causa de:
  - PKs compostas massivas
  - excesso de tabelas auxiliares
  - rigidez de evolução

Regra prática:
- copiar conceito, redesenhar a implementação.

---

## 9) PRÓXIMO PASSO OBJETIVO (PARA A GENTE TRAVAR O CAMINHO)
1) Escolher e listar as tabelas CORE do MVP (10–20)
2) Extrair “subgrafo” de FKs dessas tabelas (dependências diretas)
3) Definir o modelo alvo dessas entidades (com surrogate keys + constraints)
4) Definir eventos/snapshots mínimos (estoque, status de pedido, financeiro)
5) Só então começar backend e migração incremental
