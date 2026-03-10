# Fase 2 — Batch Processing & Arquitetura de Produção

> **Data**: 2026-03-10  
> **Status**: Implementado  
> **Migration**: `ed0b08ebec92` (add error tracking to resume results)

---

## 1. Visão Geral

Evolução do endpoint `/analyze` (single-file, síncrono) para suportar **upload em lote** de até 10 currículos por requisição, com processamento assíncrono em background e disaster recovery automático.

### Arquitetura Resumida

```
Cliente                          Servidor (Free Tier)
───────                          ────────────────────
POST /upload-batch ──────► Validação (max 10, PDF only)
  - X-Session-ID                      │
  - files[]                           ▼
                              Salva PDFs em /tmp/
                              Cria BatchJob (PROCESSING)
  ◄── HTTP 202 { job_id }            │
                                      ▼
                              BackgroundTask → process_batch()
                                 ┌── Semaphore(1) ──┐
                                 │  asyncio.to_thread(nlp, text)  │
                                 └──────────────────┘
                                      │
                              Para cada PDF:
                                try → ResumeResult(SUCCESS)
                                except → ResumeResult(FAILED)
                                finally → deleta PDF, incrementa counter
                                      │
                              BatchJob.status = COMPLETED
```

---

## 2. Decisões de Arquitetura

### 2.1 Background Processing: `BackgroundTasks` + `asyncio.to_thread()`

**Alternativas consideradas:**

| Opção | Descartada porque |
|---|---|
| Celery + Redis | Adiciona 2 dependências pesadas; inviável em Free Tier |
| `asyncio.create_task()` puro | spaCy é CPU-bound — bloquearia o Event Loop |
| `ProcessPoolExecutor` | Duplica o modelo spaCy na RAM (~500MB) por worker |

**Decisão**: `BackgroundTasks` (nativo do FastAPI) com `asyncio.to_thread()` para offload da chamada síncrona do spaCy. O `Semaphore(1)` garante que apenas uma inferência NLP roda por vez, protegendo CPU e RAM.

**Trade-off**: Se o processo da API morrer, os Background Tasks em andamento são **perdidos**. Isso é mitigado pelo Disaster Recovery (seção 2.4).

---

### 2.2 Armazenamento Temporário em Disco

Os PDFs são salvos em `/tmp/vitae_uploads/{job_id}/` antes do processamento.

**Por quê?**
- **Economia de RAM**: Evita manter N PDFs em memória simultaneamente
- **Resiliência intra-processo**: Se um PDF travar, os outros ainda estão no disco

**Trade-off**: Em Free Tier, o disco é **efêmero** — formatado a cada reinicialização do contêiner. Os PDFs servem apenas para economia de RAM durante a vida do processo, **não para recovery cross-restart**.

---

### 2.3 Status por Arquivo (`ResultStatus`)

Cada `ResumeResult` tem seu próprio `status` (SUCCESS/FAILED) e `error_message`. O `BatchJob` final é sempre marcado como `COMPLETED` quando o loop termina, independente de quantos arquivos falharam individualmente.

**Por quê?** `COMPLETED` significa "o job terminou de processar", não "tudo deu certo". O status por arquivo dá granularidade ao frontend para mostrar quais currículos precisam ser reenviados.

---

### 2.4 Disaster Recovery ("Aceitar a Perda")

No `lifespan` (startup) da API, todos os `BatchJob` com status `PENDING` ou `PROCESSING` são marcados como `FAILED`.

**Premissa**: O disco do Free Tier é formatado a cada restart. Não há PDFs para reprocessar. A estratégia é **aceitar a perda** e notificar o frontend, que avisa o usuário para reenviar.

**Trade-off**: Jobs parcialmente processados antes do crash terão alguns `ResumeResult` salvos e outros não. O frontend deve tratar `FAILED` como "lote incompleto — reenvie".

---

### 2.5 Autenticação Pragmática (`X-Session-ID`)

O `user_id` é extraído do header `X-Session-ID` sem nenhuma validação de autenticidade.

**Riscos aceitos:**
- Qualquer cliente pode forjar qualquer `user_id`
- Sem isolamento real entre usuários

**Justificativa**: Para MVP/portfólio, autenticação real (JWT, OAuth) adicionaria complexidade desproporcional ao valor entregue. Este é o débito técnico mais significativo da Fase 2.

---

## 3. Débitos Técnicos

| # | Débito | Severidade | Quando resolver |
|---|---|---|---|
| **DT-01** | `X-Session-ID` sem autenticação real | 🔴 Alta | Antes de produção com dados reais |
| **DT-02** | `api.py` concentra endpoint, processing engine e lifespan (~350 linhas) | 🟡 Média | Quando atingir ~500 linhas, extrair para `routes/`, `services/` |
| **DT-03** | Sem endpoint de consulta de status do job (`GET /jobs/{id}`) | 🟡 Média | Fase 3 (frontend polling) |
| **DT-04** | Testes de integração (com banco real) não implementados | 🟡 Média | Quando CI/CD for configurado |
| **DT-05** | Sem rate limiting por `user_id` | 🟢 Baixa | Quando houver múltiplos usuários reais |
| **DT-06** | Sem paginação para listar resultados de um job | 🟢 Baixa | Quando lotes maiores que 10 forem suportados |

---

## 4. Arquivos Modificados

| Arquivo | O que mudou |
|---|---|
| `db/models.py` | Adicionado `ResultStatus` enum; colunas `status` e `error_message` em `ResumeResult` |
| `api.py` | Disaster Recovery no lifespan; endpoint `POST /upload-batch`; `process_batch()` engine |
| `tests/test_api.py` | 4 novos testes (missing session ID, exceeds limit, non-PDF, success) |
| `alembic/versions/ed0b08ebec92_*.py` | Migration com criação de enums PostgreSQL e conversão VARCHAR→enum |

---

## 5. Como Testar

```bash
# Unit tests (sem banco)
pytest tests/test_api.py -v

# Smoke test manual (com banco)
uvicorn api:app --reload
curl -X POST http://localhost:8000/upload-batch \
  -H "X-Session-ID: test-user" \
  -F "files=@curriculo.pdf"
# Esperado: HTTP 202 {"job_id": "..."}
```
