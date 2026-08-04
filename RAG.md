# RAG pipeline — plan & implementation guide

A **plan only** (no code yet): a Retrieval-Augmented Generation API that answers questions
from **PDF** sources, using **ChromaDB** as the vector store, **Ollama** as the local LLM +
embedding model, orchestrated with **LangChain**. Written to double as an interview-grade
explanation of how RAG works and why each piece is there.

Status: 📋 **design**. Implementation is phased at the bottom; we build after reviewing this.

---

## 1. What RAG is, and why (not fine-tuning)

An LLM only knows what it was trained on. It has never seen your PDFs, and asked about them
it will **hallucinate** a confident-sounding wrong answer. Two ways to fix that:

- **Fine-tuning** — retrain the model on your documents. Expensive, slow, must be redone as
  documents change, and *still* blurs facts rather than quoting them.
- **RAG** — leave the model alone; at question time, **retrieve** the relevant passages from
  your documents and **paste them into the prompt** as context, instructing the model to
  answer *only* from that context. Cheap, updates instantly when documents change, and can
  **cite sources**.

RAG is the right tool when the knowledge is **yours, changing, and must be traceable** —
exactly the PDF case. The one-line mental model:

> **Retrieval** finds the right paragraphs; **Augmentation** stuffs them into the prompt;
> **Generation** writes the answer grounded in them.

---

## 2. The two phases

RAG has a clean split that the module layout mirrors. Confusing them is the usual beginner
mistake.

### Phase A — Ingestion / Indexing (offline, done once per document)

```
PDF ──▶ load text ──▶ split into chunks ──▶ embed each chunk ──▶ store vectors in Chroma
       (pypdf)        (~1000 chars,        (Ollama embedding    (with metadata: source,
                       150 overlap)         model → a vector)     page, chunk #)
```

### Phase B — Query / Retrieval + Generation (online, per request)

```
question ──▶ embed the question ──▶ similarity search in Chroma ──▶ top-k chunks
                (same embed model)     (nearest vectors)               │
                                                                       ▼
                                          build prompt: [system + chunks + question]
                                                                       │
                                                                       ▼
                                              Ollama LLM ──▶ answer (+ cited sources)
```

The pivotal detail linking them: **the same embedding model must be used in both phases.**
Vectors are only comparable if produced by the same model — index with `nomic-embed-text`
and query with something else and similarity search returns garbage. This is the #1 RAG bug.

---

## 3. Components & the choices

| Concern | Choice | Why |
|---|---|---|
| Orchestration | **LangChain** | glues loaders → splitter → embeddings → store → LLM with standard interfaces; swappable pieces |
| PDF loading | `pypdf` via LangChain's `PyPDFLoader` | extracts text per page (page number → citations) |
| Chunking | `RecursiveCharacterTextSplitter` | splits on paragraph/sentence boundaries, not mid-word |
| Embeddings | **Ollama** `nomic-embed-text` | local, free, no API key; good quality/size balance |
| Vector store | **ChromaDB** | simple, local, persistent; embedded or server mode |
| LLM | **Ollama** `llama3.2` (or `llama3.1`) | local, free, private — nothing leaves the machine |

Everything runs **locally** — no OpenAI key, no data leaving your box. That's a deliberate,
and interview-notable, property: a fully offline RAG stack.

LangChain packages we'll add: `langchain`, `langchain-community` (loaders),
`langchain-ollama` (`OllamaEmbeddings`, `ChatOllama`), `langchain-chroma`, `pypdf`.

---

## 4. Architecture (local, Docker)

```
                       ┌────────────────────────────────────────────┐
   POST /rag/ingest    │  FastAPI (app)                             │
   POST /rag/query ───▶│    app/rag/ : loaders, chunking, chain     │
                       └──────┬───────────────────────┬─────────────┘
                              │ embeddings + LLM       │ vectors
                              ▼                        ▼
                      ┌───────────────┐        ┌───────────────┐
                      │  Ollama       │        │  ChromaDB     │
                      │  (LLM +       │        │  (vector      │
                      │   embeddings) │        │   store)      │
                      │  :11434       │        │  :8001        │
                      └───────────────┘        └───────────────┘
```

Both are containers alongside the app (like Postgres/Redis). Ollama needs a **volume for
pulled models** (multi-GB); Chroma needs a **volume for the index**.

---

## 5. Module layout (follows the project's router/service/schema convention)

```
app/rag/
  __init__.py
  loaders.py       load a PDF and split it into chunks (Phase A, steps 1–2)
  embeddings.py    OllamaEmbeddings factory (one place; used by BOTH phases)
  vectorstore.py   Chroma client + get_vectorstore() (connect/persist)
  llm.py           ChatOllama factory
  chain.py         build the retrieval+generation chain (retriever + prompt + llm)
  service.py       ingest_pdf(file) and answer_question(q) — the two public operations
app/routers/rag.py     POST /rag/ingest, POST /rag/query   (+ GET /rag/status)
app/schemas/rag.py     IngestResponse, QueryRequest, QueryResponse (answer + sources)
```

Same separation as everywhere else: **router** = HTTP, **service** = orchestration, the
`rag/` submodules = the pipeline stages, each swappable in isolation.

---

## 6. The API surface

| Endpoint | Body | Returns | Notes |
|---|---|---|---|
| `POST /rag/ingest` | a PDF (multipart upload) | `{filename, chunks_indexed}` | Phase A: load→chunk→embed→store. Likely **auth-protected**. |
| `POST /rag/query` | `{question, top_k?}` | `{answer, sources[]}` | Phase B: retrieve→augment→generate. `sources` = the chunks used (file + page) so answers are **traceable**. |
| `GET /rag/status` | — | `{ollama, chroma, collection_count}` | readiness of the two deps + how many chunks are indexed |

`sources` in the query response is what makes this trustworthy rather than a black box — the
user sees *which page of which PDF* each claim came from.

---

## 7. Config additions (`config.py`)

| Env var | Default | Meaning |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama endpoint (compose service name; `localhost` for host run) |
| `OLLAMA_LLM_MODEL` | `llama3.2` | generation model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | embedding model — **must match** between ingest & query |
| `CHROMA_HOST` / `CHROMA_PORT` | `localhost` / `8001` | Chroma server. Port is **8001**, not 8000 — the app owns 8000, and a host port can't be bound twice. |
| `RAG_CHUNK_SIZE` | `1000` | characters per chunk |
| `RAG_CHUNK_OVERLAP` | `150` | overlap so a sentence split across chunks isn't lost |
| `RAG_TOP_K` | `4` | how many chunks to retrieve and stuff into the prompt |

---

## 8. Local setup (Docker) — the infra piece

Add two services (a separate compose, like the ETL playground, to keep the heavy AI deps
isolated from the app stack):

- **Ollama** (`ollama/ollama` image) + a one-shot init that pulls the two models
  (`ollama pull llama3.2`, `ollama pull nomic-embed-text`) into a named volume. First pull is
  multi-GB and slow; cached after. CPU-only works (slower); GPU optional.
- **ChromaDB** (`chromadb/chroma` image) in **server mode** with a persistent volume.

> **Embedded vs server Chroma — a decision that echoes the Redis lesson.** Chroma can run
> *embedded* (an in-process library writing to a local dir) or as a *server* (a separate
> container). Embedded is simplest but is **per-pod** — with multiple replicas each has its
> own index, and an ingest on pod A is invisible to a query on pod B. For the same
> multi-pod reason we chose Redis over `lru_cache`, we'll run **Chroma in server mode** so all
> pods share one index. Embedded is fine only for a single-process local demo.

---

## 9. Key design decisions & gotchas (the interview material)

- **Same embedding model both phases** (§2). The single most common RAG bug.
- **Chunk size & overlap are a tuning trade-off.** Too big → retrieval returns mostly
  irrelevant text and dilutes the prompt; too small → a chunk loses the context that makes it
  meaningful. ~1000 chars with ~150 overlap is a sane start; overlap stops a fact that
  straddles a boundary from being lost. Tune per corpus.
- **Grounding prompt = the hallucination guard.** The system prompt must say *"answer only
  from the context below; if it's not there, say you don't know."* Without it the model falls
  back on its training data and invents answers — defeating the point of RAG.
- **Return sources.** Carry `source` + `page` in each chunk's metadata from ingestion, and
  surface them in the response. Traceability is a feature, not a nice-to-have.
- **Retrieval strategy.** Start with top-k similarity; consider **MMR** (maximal marginal
  relevance) to avoid returning four near-duplicate chunks, and later a **reranker** for
  quality. Note the "context window" limit — you can only stuff so many chunks before the LLM
  prompt overflows.
- **Idempotent ingestion.** Re-ingesting the same PDF should not double the chunks. Key
  chunks by a deterministic id (file hash + chunk index) so a re-ingest upserts, not
  duplicates — the same idempotency principle as the Spark/DB work.
- **Async & latency.** LLM generation is slow (seconds on CPU). The query endpoint should be
  `async` (Ollama calls are network I/O), and **streaming** the tokens (Server-Sent Events)
  is the real UX win — deferred to a later phase.
- **Model pull timing.** The app must not block startup waiting for a model; `/rag/status`
  reports readiness, and ingestion/query 503 cleanly if a model isn't pulled yet — the same
  graceful-degradation stance as Redis.

---

## 10. Production considerations (later, not phase 1)

- **Chroma server mode + a persistent, backed-up volume** (or a managed vector DB like
  pgvector/Pinecone/OpenSearch on AWS). Embedded Chroma does not survive a pod restart or
  scale-out.
- **Ollama on AWS** needs GPU nodes to be fast; the local Ollama would likely become **Bedrock**
  or a hosted model in prod — and because LangChain abstracts the LLM, that swap is a factory
  change in `llm.py`, not a rewrite (same portability lesson as everything else).
- **Auth** on `/rag/ingest` (who can add documents) and probably `/rag/query`.
- **Evaluation.** RAG quality needs measuring — retrieval hit-rate, answer faithfulness (does
  the answer actually follow from the sources?). A held-out Q&A set + a judge.
- **Caching** identical questions (Redis) to skip repeat LLM calls.
- **Chunking upgrades** — semantic/structure-aware splitting for tables and headings, which
  `RecursiveCharacterTextSplitter` handles poorly.

---

## 11. Phased implementation plan (the todo list)

- [ ] **Phase 0 — Infra.** `rag/docker-compose.yml` with Ollama + Chroma (server mode) +
      model-pull init. Confirm `ollama list` shows both models and Chroma answers on :8000.
- [ ] **Phase 1 — Ingestion.** `loaders.py` (PyPDFLoader + RecursiveCharacterTextSplitter),
      `embeddings.py`, `vectorstore.py`; `service.ingest_pdf()` writing chunks+metadata to
      Chroma. Verify chunk count and that vectors land in the collection.
- [ ] **Phase 2 — Query.** `llm.py`, `chain.py` (retriever + grounding prompt + ChatOllama);
      `service.answer_question()` returning answer + source chunks.
- [ ] **Phase 3 — API.** `schemas/rag.py`, `routers/rag.py` (`/rag/ingest`, `/rag/query`,
      `/rag/status`); wire into `main.py`; add config vars.
- [ ] **Phase 4 — Trust.** Source citations in responses, grounding-prompt "I don't know"
      behaviour, idempotent re-ingest (upsert by chunk id).
- [ ] **Phase 5 — Polish/prod.** Streaming responses (SSE), query caching (Redis), a small
      eval set, `/rag/status` health wiring, k8s manifests (Chroma StatefulSet, Ollama).
- [ ] **Phase 6 — (optional) UI.** A "chat with your PDFs" page reusing the existing UI
      pattern (upload → ask → answer with citations).

---

## 12. The 60-second interview summary

> "The problem: an LLM doesn't know your private PDFs and will hallucinate about them.
> Instead of fine-tuning, I used RAG — at ingestion I load each PDF, split it into
> ~1000-char overlapping chunks, embed them with a local Ollama embedding model, and store
> the vectors in Chroma with page metadata. At query time I embed the question with the
> *same* model, do a similarity search for the top-k chunks, stuff them into a grounding
> prompt that says 'answer only from this context', and let a local Ollama LLM generate the
> answer — returning the source pages so it's traceable. Everything runs locally via
> LangChain, so no data leaves the box. The two things I watch: the embedding model must be
> identical at index and query time, and Chroma runs in server mode so multiple pods share
> one index rather than each holding its own — the same multi-pod reasoning that made me pick
> Redis over an in-process cache."