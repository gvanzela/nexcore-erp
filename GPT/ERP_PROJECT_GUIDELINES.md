# ERP_PROJECT_GUIDELINES.md

## CONTEXTO
Projeto real de ERP (autopeças), usado como produto e como laboratório para aprender Data Engineering de verdade.

Regra base:
> Se quebrar na loja do meu pai, é bug de produção.

---

## MENTALIDADE
- Projeto tratado como empresa real
- Decisão técnica sempre ligada a problema de negócio
- Escala, custo e manutenção importam

---

## ARQUITETURA GERAL

### Backend
- API REST bem definida
- Camadas claras: ingestão → lógica → persistência
- Versionamento de API

### Banco de Dados
- OLTP bem normalizado
- Histórico (snapshots / event-light)
- Separar operacional vs analítico

---

## DADOS (núcleo do aprendizado)

### Ingestão
- APIs externas (fornecedores, NF-e, bancos)
- Arquivos (CSV, XML)
- Jobs idempotentes

### ELT
- Bronze → Silver → Gold
- dbt como ferramenta central
- Regras de negócio versionadas

### Data Warehouse
- Métricas reais:
  - Faturamento
  - Margem
  - Estoque
  - Giro
- Star schema desde o início

---

## QUALIDADE & GOVERNANÇA

### Data Quality
- Testes de integridade
- Alertas simples (volume, null, outlier)
- Logs, retry, falha visível

### Governança
- Dicionário de dados
- Definição clara de métricas
- Ownership explícito

---

## CLOUD & ESCALA

### Infra
- Começar simples
- Storage separado de compute
- Pensar custo desde o dia 1

### Segurança
- RBAC
- Dados sensíveis isolados
- Logs de acesso

---

## ANALYTICS & USO REAL

### Dashboards
- Financeiro: caixa, margem, lucro
- Operacional: estoque, vendas
- Crescimento: clientes, ticket médio

### Feedback
- Usuário real (pai)
- Feedback vira backlog
- Métrica inútil é removida

---

## PRODUTO & PORTFÓLIO

### Documentação
- README claro
- Arquitetura desenhada
- Decisões técnicas explicadas

### Narrativa (entrevista)
- Problema real
- Solução construída
- Trade-offs
- Evolução ao longo do tempo

---

## O QUE ESSE PROJETO ENSINA
- Data modeling real
- dbt com regra viva
- SQL pesado
- Pipeline que quebra
- Dado errado = dinheiro errado
- Pensar como engenheiro e dono

---

## RESULTADO FINAL
- Produto vendável
- Projeto técnico forte
- Portfólio real
- Base pra vaga internacional
- Base pra empreender
