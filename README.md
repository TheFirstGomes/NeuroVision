# NeuroVision — Plataforma Educacional de Neuro-Oftalmologia

> Ferramenta interativa para ensino de neuro-oftalmologia com visualização anatômica 3D, tutor clínico baseado em IA, simulador de campo visual e casos clínicos curados.

---

## O que é

NeuroVision é uma plataforma web educacional que une visualização 3D do sistema visual humano com um tutor inteligente alimentado por RAG (Retrieval-Augmented Generation). O objetivo é tornar o aprendizado de neuro-oftalmologia mais visual, interativo e acessível para estudantes de medicina e oftalmologistas.

A plataforma explora a retina como "janela do sistema nervoso central" — único ponto do corpo onde neurônios vivos podem ser observados de forma não-invasiva — conectando patologias oculares às suas origens neurológicas.

---

## Fase 2.2 — atual (YOLO + CNN + Pipeline 4 camadas)

### Classificador de Fundoscopia — Pipeline Completo

```
Imagem de fundo de olho
        │
        ▼
┌────────────────────────────────────────────────────────┐
│  Pre — YOLOv8n  (optic_disc_yolov8.onnx)               │
│  Detecção de disco e cup óptico                        │
│  Dataset: REFUGE2 (1200 imagens c/ segmentação)        │
│  Saída: disc_bbox · cup_bbox · CDR · glaucoma_risk     │
└─────────────────────────┬──────────────────────────────┘
                          │ enriquece resultado com CDR
                          ▼
┌────────────────────────────────────────────────────────┐
│  Tier 0 — EfficientNet-B4  (fundoscopy_...v1.onnx)     │
│  DR grading 0–4 (APTOS 2019)  AUC 0.9442  QWK primário│
│  Confiança mínima: 0.60                                │
└─────────────────────────┬──────────────────────────────┘
                          │ confiança < 0.60 ou modelo ausente
                          ▼
┌────────────────────────────────────────────────────────┐
│  Tier 1 — Claude Vision  (claude-haiku-4-5-20251001)   │
│  Análise multimodal — glaucoma, DMRI, papiledema, RD   │
└─────────────────────────┬──────────────────────────────┘
                          │ API indisponível
                          ▼
┌────────────────────────────────────────────────────────┐
│  Tier 2 — Feature-based (Pillow/NumPy)                 │
│  Heurísticas de cor e textura · zero APIs externas     │
└────────────────────────────────────────────────────────┘
```

Classes DR (Tier 0): `normal` · `dr_mild` · `dr_moderate` · `dr_severe` · `dr_proliferative`

#### Modelos ONNX em produção

| Modelo | Arquivo | Métrica | Dataset | Uso |
|--------|---------|---------|---------|-----|
| EfficientNet-B4 | `fundoscopy_efficientnet_b4_v1.onnx` | AUC 0.9442 · QWK 0.79 | APTOS 2019 (3662 imgs, 5 classes) | DR grading |
| YOLOv8n | `optic_disc_yolov8.onnx` | mAP50 (treinado) | REFUGE2 (1200 imgs, 2 classes) | Disco/cup detection |

#### Saída enriquecida com YOLO

Quando o modelo YOLO está presente, cada `ClassificationResult` inclui:

```json
{
  "disc_detected":   true,
  "disc_confidence": 0.91,
  "cup_disc_ratio":  0.68,
  "glaucoma_risk":   "moderado"
}
```

Se `cup_disc_ratio >= 0.65` e a CNN classificou como `normal`, o resultado eleva automaticamente a suspeita de glaucoma nos `features_detected`.

### Treinamento e Export

```powershell
# ── EfficientNet-B4 (DR classification) ──────────────────
pip install -r train/requirements-train.txt

python train/train_efficientnet.py `
  --data-dir <caminho/aptos2019> `
  --output-dir train/output `
  --csv train_1.csv `
  --image-subdir "train_images/train_images"

python train/ga_hyperparam_search.py `
  --data-dir <caminho/aptos2019> --pop-size 12 --generations 5

python train/export_to_onnx.py `
  --checkpoint train/output/efficientnet_b4_aptos.pt `
  --output backend/models/fundoscopy_efficientnet_b4_v1.onnx

# ── YOLOv8n (optic disc detection) ───────────────────────
python train/prepare_refuge_yolo.py `
  --refuge-dir <caminho/REFUGE2> `
  --output-dir <caminho/refuge2_yolo>

python train/train_yolo.py `
  --data <caminho/refuge2_yolo/optic_disc.yaml> `
  --output-dir train/yolo_output `
  --epochs 50
# Copia automaticamente para backend/models/optic_disc_yolov8.onnx
```

---

## Fase 2 — base

### Funcionalidades

- **Visualizador duplo 3D / 2D** — toggle no viewer; modo 3D usa Three.js + GLTF; modo 2D usa imagem anatômica de referência com hotspots sobrepostos
- **Modelo 3D anatômico realista** — olho GLTF com 4 músculos retos extraoculares procedurais (CatmullRomCurve3, semi-transparentes), bundle de fibras nervosas (10 strands individuais do disco → quiasma), esquema de cores semântico (vermelho → dourado → laranja → verde → azul → roxo → ciano)
- **Posicionamento anatômico correto** — disco óptico em polo posterior nasal, mácula em polo posterior temporal, tube da via visual ancorada ao DISC_POSITION derivado da anatomy-data
- **10 estruturas clicáveis** com painel de anatomia: conexões neurológicas, patologias associadas, relevância clínica
- **Simulador de Campo Visual** — selecionar uma estrutura exibe os dois campos visuais (OE | OD) em SVG com o defeito perimétrico correspondente e pérola clínica diagnóstica
- **Chat educacional RAG** — perguntas respondidas com base em literatura médica peer-reviewed indexada
- **21 documentos indexados**: IMO, Walsh & Hoyt, Lancet Neurology, AREDS2, ONTT, EGS Guidelines
- **Ingestão de PDFs** — upload de artigos e guidelines que passam a ser consultados pelo chat imediatamente
- **Classificador de fundoscopia** — dois tiers: Claude Vision (claude-haiku-4-5) como primário e análise de características visuais como fallback automático
- **8 Casos Clínicos curados** — nível de residência, com história clínica, exame, 3 perguntas com gabarito revelável e ponto de ensino
- **Sidebar com abas** — Chat · Anatomia · Campo Visual; viewer 3D sempre limpo, sem sobreposição de painéis
- **Integração bidirecional** — patologia no painel injeta pergunta no chat; chat destaca estruturas no 3D; classificador destaca estruturas relevantes; casos clínicos abrem diretamente a estrutura e o campo visual no viewer
- **Nav header funcional** — botões Anatomia 3D · Patologias · Via Visual · Diagnóstico conectados às respectivas funcionalidades
- **Persistência de sessão** — histórico do chat salvo em SQLite e restaurado automaticamente via `localStorage` no próximo acesso
- **Rate limiting** — `/chat` 30 req/min · `/classify` 10 req/min · `/ingest` 5 req/min por IP
- **Validação de upload** — magic bytes verificados antes de processar (rejeita arquivos falsos/maliciosos)
- **Avaliação RAG automática** — LLM-as-judge (Groq) avalia cada resposta em background: faithfulness + relevancy (1–5) → composite score ponderado (0.6F + 0.4R)
- **RAG Tracing completo** — cada query persiste: chunks recuperados, scores de similaridade, contexto enviado ao LLM, latência por etapa (retrieval_ms · llm_ms · total_ms); detecta automaticamente queries com similaridade < 0.5
- **Visualizador 2D com hotspots** — imagem anatômica com 10 pontos interativos; clicar num ponto dispara o mesmo callback do 3D (sidebar, anatomia, campo visual funcionam identicamente)
- **Mapeamento fibra → campo visual (retinotopia)** — 10 fibras do nervo óptico organizadas em 5 regiões semânticas (sup. nasal · sup. temporal · feixículo macular · inf. temporal · inf. nasal); hover mostra tooltip com mini diagrama SVG de campo visual OD; clique abre o Campo Visual com o patch da região e descrição clínica da lesão isolada
- **LOD e performance** — músculos extraoculares fundidos em 1 draw call (`mergeGeometries`); segmentos de tubos reduzidos ~40% (TubeGeometry: 24→12 músculos, 40→24 fibras, 50→32 via); esferas: 32→16 segmentos; hitboxes invisíveis mais largos nas fibras para hover confortável

### Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  NeuroVision    Anatomia 3D │ Patologias │ Via Visual │ Diagnóstico           │
├────────────────────────────────────────────────┬─────────────────────────────┤
│  [3D] [2D]  ← toggle                           │  Chat │ Anatomia │ Campo    │
│                                                │─────────────────────────────│
│          Viewer 3D ou 2D                       │                             │
│          (sempre limpo, sem sobreposição)       │  conteúdo da aba ativa      │
│                                                │                             │
└────────────────────────────────────────────────┴─────────────────────────────┘
```

- Clicar numa estrutura → abre aba **Anatomia** automaticamente
- "Perguntar ao Tutor" → troca para aba **Chat** com pergunta injetada
- Aba **Campo Visual** disponível ao lado
- **Via Visual** no header → troca diretamente para Campo Visual
- **Patologias** no header → abre Casos Clínicos
- **Diagnóstico** no header → abre Classificador de Fundoscopia

### Casos Clínicos

| # | Caso | Dificuldade | Estrutura |
|---|------|-------------|-----------|
| 1 | Neurite óptica — dor ocular e escotoma central em mulher jovem | ●● | Nervo Óptico |
| 2 | Adenoma hipofisário — cefaleia e perda visual lateral | ● | Quiasma |
| 3 | NOIA arterítica — perda visual súbita em idoso com cefaleia temporal | ●● | Disco Óptico |
| 4 | Retinopatia diabética proliferativa | ● | Retina |
| 5 | Papiledema bilateral — hipertensão intracraniana idiopática | ●● | Disco Óptico |
| 6 | AVC occipital com poupamento macular | ●● | Córtex Visual |
| 7 | Glaucoma avançado com campo tubular | ●●● | Disco Óptico |
| 8 | DMRI úmida — metamorfopsia e escotoma central | ● | Mácula |

### Defeitos de Campo Visual por Estrutura

| Estrutura | Defeito | Padrão Diagnóstico |
|-----------|---------|-------------------|
| Córnea | Redução de acuidade | Bilateral, sem defeito de campo |
| Retina | Escotoma arqueado | Segue camada de fibras nervosas |
| Mácula | Escotoma central | Ipsilateral, perda de leitura |
| Disco Óptico | Altitudinal superior | NOIA — borda horizontal precisa |
| Nervo Óptico | Amaurose monocular | OD inteiro + DPAR (Marcus Gunn) |
| Quiasma | Hemianopsia bitemporal | Temporais de ambos — adenoma hipofisário |
| Trato Óptico | Homônima incongruente | Lesão anterior = assimetria entre olhos |
| CGL | Hemianopsia homônima | Lesão talâmica — sem DPAR |
| Radiações (temporal) | "Pie in the sky" | Quadrante superior — lobo temporal |
| Córtex V1 | Homônima + poupamento macular | AVC occipital — duplo suprimento vascular |

### Estruturas Anatômicas Cobertas

| Estrutura | Camada | Patologias Principais |
|-----------|--------|----------------------|
| Córnea | Olho | Ceratocone, ceratite herpética, anestesia corneana |
| Retina | Olho | Retinopatia diabética, DMRI |
| Mácula / Fóvea | Olho | DMRI, edema macular diabético |
| Disco Óptico | Olho | Papiledema, glaucoma, papilite |
| Nervo Óptico | Via Visual | Neurite óptica, NOIA, meningioma |
| Quiasma Óptico | Via Visual | Adenoma hipofisário, craniofaringioma |
| Trato Óptico | Via Visual | Hemianopsia homônima incongruente |
| Corpo Geniculado Lateral | Via Visual | Lesões talâmicas vasculares |
| Radiações Ópticas | Via Visual | Quadrantanopsia ("pie in the sky") |
| Córtex Visual V1 | Via Visual | AVC occipital, migrânea com aura |

---

## Stack Técnica

### Backend

| Componente | Tecnologia |
|-----------|-----------|
| API Server | FastAPI 0.115 |
| LLM (RAG + Avaliação) | Groq — LLaMA-3.3-70b-versatile |
| Detector YOLO | YOLOv8n via ONNX Runtime — disco/cup óptico (REFUGE2) — CDR + glaucoma risk (pre-step) |
| Classificador CNN | EfficientNet-B4 via ONNX Runtime — AUC 0.9442 no APTOS 2019 (tier 0) |
| Classificador Vision | Anthropic claude-haiku-4-5 (tier 1) |
| Classificador fallback | Pillow/NumPy feature-based (tier 2) |
| RAG Framework | LangChain 0.3 |
| Vector Store | ChromaDB 0.5 (persistente) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Persistência de sessão | SQLite (built-in) — sessions + chat_messages + rag_evaluations + rag_traces |
| Rate Limiting | slowapi 0.1.9 |
| Observabilidade | structlog (JSON structured logging) |

### Frontend

| Componente | Tecnologia |
|-----------|-----------|
| Framework | Next.js 14 (App Router) |
| 3D Engine | React Three Fiber + Three.js |
| 3D Helpers | @react-three/drei |
| Campo Visual | SVG puro (sem dependências) |
| Estilização | Tailwind CSS |
| HTTP Client | fetch nativo (tipado) |
| Persistência de sessão | localStorage (session ID) |

---

## Estrutura do Projeto

```
neurovision/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entrypoint — 17 endpoints
│   │   ├── domain/
│   │   │   └── models.py              # Schemas Pydantic (Chat, Anatomy, Classification, Cases, Session, Evaluation)
│   │   ├── services/
│   │   │   ├── rag_service.py         # Pipeline RAG explícito — 3 etapas com timing por step
│   │   │   ├── classifier_service.py  # Pipeline 4 camadas: YOLO pre + CNN + Vision + feature
│   │   │   ├── cnn_classifier.py      # EfficientNet-B4 ONNX Runtime wrapper
│   │   │   ├── optic_disc_detector.py # YOLOv8 ONNX Runtime — disco/cup detection + CDR
│   │   │   ├── cases_service.py       # 8 casos clínicos curados
│   │   │   ├── evaluation_service.py  # LLM-as-judge (Groq) — faithfulness + relevancy
│   │   │   ├── ingestion_service.py   # Ingestão de PDFs (idempotente via MD5)
│   │   │   ├── knowledge_base.py      # 21 documentos de literatura indexados
│   │   │   └── anatomy_service.py     # 10 estruturas com dados clínicos
│   │   └── infrastructure/
│   │       ├── database.py            # SQLite — sessions, chat_messages, rag_evaluations, rag_traces
│   │       ├── security.py            # Magic byte validation + filename sanitization
│   │       └── vector_store.py        # Abstração ChromaDB + similarity_search_with_score
│   ├── models/
│   │   ├── fundoscopy_efficientnet_b4_v1.onnx  # EfficientNet-B4 — DR grading 5 classes
│   │   ├── model_metadata.json                  # Métricas, SHA-256, opset
│   │   ├── optic_disc_yolov8.onnx               # YOLOv8n — disco/cup detection (REFUGE2)
│   │   └── yolo_metadata.json                   # mAP50, SHA-256, classes
│   ├── neurovision.db                 # SQLite (gerado automaticamente no startup)
│   ├── requirements.txt
│   └── Dockerfile
├── train/
│   ├── train_efficientnet.py          # Fine-tuning EfficientNet-B4 no APTOS 2019 (2 fases, AMP, WeightedSampler)
│   ├── export_to_onnx.py              # PyTorch → ONNX opset 17 + validação de consistência + SHA-256
│   ├── ga_hyperparam_search.py        # Busca de hiperparâmetros com Algoritmo Genético (DEAP-style manual)
│   ├── prepare_refuge_yolo.py         # Converte máscaras REFUGE2 → YOLO bounding boxes
│   ├── train_yolo.py                  # Treina YOLOv8n e exporta para ONNX
│   └── requirements-train.txt        # torch, timm, albumentations, onnx, onnxruntime, ultralytics
├── frontend/
│   ├── app/
│   │   ├── page.tsx                   # Layout principal — viewer 3D + sidebar com abas + modais
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── EyeViewer3D.tsx            # Three.js — modelo 3D + músculos (merged) + 10 fibras semânticas interativas
│   │   ├── EyeViewer2D.tsx            # Imagem anatômica + 10 hotspots interativos
│   │   ├── AnatomyPanel.tsx           # Aba Anatomia — dados clínicos da estrutura
│   │   ├── VisualFieldPanel.tsx       # Aba Campo Visual — SVG perimetria
│   │   ├── ChatPanel.tsx              # Aba Chat — tutor RAG + restauração de histórico
│   │   ├── CasesPanel.tsx             # Modal de casos clínicos
│   │   ├── ImageClassifier.tsx        # Modal de análise de fundoscopia
│   │   ├── IngestPanel.tsx            # Modal de ingestão de PDFs
│   │   └── Header.tsx                 # Nav (Anatomia 3D · Patologias · Via Visual · Diagnóstico) + status + ações
│   ├── lib/
│   │   ├── api.ts                     # Cliente HTTP tipado (inclui session history)
│   │   ├── anatomy-data.ts            # Metadados e posições das estruturas 3D
│   │   ├── fiber-region-data.ts       # 5 regiões de fibra com patches SVG + mapeamento retinotópico
│   │   └── visual-field-data.ts       # Defeitos de campo visual por estrutura (SVG paths)
│   └── public/
│       ├── models/                    # Modelos GLTF (eye.glb)
│       └── eye-anatomy-2d.png         # Ilustração anatômica para o modo 2D
├── docker-compose.yml
├── start.bat                          # Start no Windows
├── start.sh                           # Start no Linux/Mac
└── .env.example
```

---

## Como Rodar

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- Chave de API Groq — gratuita em [console.groq.com](https://console.groq.com)
- Chave de API Anthropic *(opcional)* — habilita Claude Vision no classificador; sem ela usa análise de características visuais

### Setup local (Windows)

```bash
# 1. Entre na pasta do projeto
cd neurovision

# 2. Configure as variáveis de ambiente
# Edite backend/.env com suas chaves

# 3. Inicie (abre backend e frontend automaticamente)
.\start.bat
```

### Setup manual

```bash
# Terminal 1 — Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

### Com Docker

```bash
cp .env.example .env
# Edite .env com as chaves de API
docker-compose up --build
```

### URLs

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger Docs | http://localhost:8000/docs |

---

## Endpoints da API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Status do sistema e RAG |
| `POST` | `/chat` | Chat educacional RAG — pipeline explícito com tracing por etapa (30 req/min) |
| `GET` | `/anatomy` | Lista todas as estruturas anatômicas |
| `GET` | `/anatomy/{id}` | Dados clínicos de uma estrutura |
| `POST` | `/classify` | Analisa imagem de fundoscopia — magic byte validation (10 req/min) |
| `POST` | `/ingest` | Indexa PDF na base de conhecimento RAG — magic byte validation (5 req/min) |
| `GET` | `/documents` | Lista documentos indexados com contagem de chunks |
| `GET` | `/cases` | Lista os casos clínicos disponíveis |
| `GET` | `/cases/{id}` | Retorna caso clínico completo com perguntas e gabarito |
| `GET` | `/sessions/{id}/messages` | Histórico de mensagens da sessão |
| `DELETE` | `/sessions/{id}` | Remove sessão e todo o histórico |
| `GET` | `/evaluation/stats` | Scores LLM-as-judge: faithfulness, relevancy, composite |
| `GET` | `/traces` | Traces RAG: chunks, similarity scores, latência por etapa |
| `GET` | `/traces/stats` | Métricas agregadas: latência média, avg similarity, low-sim ratio |

### Exemplo — Chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "O que é neurite óptica e qual sua relação com esclerose múltipla?",
    "structure": "nervo_optico"
  }'
```

### Exemplo — Classificar imagem

```bash
curl -X POST http://localhost:8000/classify \
  -F "file=@fundoscopia.jpg"
```

### Exemplo — Estatísticas RAG

```bash
curl http://localhost:8000/evaluation/stats
```

---

## Variáveis de Ambiente

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `GROQ_API_KEY` | ✅ | — | Chave da API Groq (chat RAG + avaliação LLM-as-judge) |
| `GROQ_MODEL` | ❌ | `llama-3.3-70b-versatile` | Modelo LLM |
| `ANTHROPIC_API_KEY` | ❌ | — | Habilita Claude Vision no classificador de fundoscopia |
| `ALLOWED_ORIGINS` | ❌ | `http://localhost:3000` | CORS origins (separar por vírgula para múltiplos) |

---

## Integrantes

- [Luan Gonçalves Gomes](https://www.linkedin.com/in/luan-g-432896b5/)

---

## Aviso Legal

> **Esta plataforma é exclusivamente educacional.**
> As respostas são geradas por IA com base em literatura médica indexada e **não substituem diagnóstico clínico, avaliação médica ou conduta terapêutica.**
> Fontes utilizadas: IMO, Walsh & Hoyt Clinical Neuro-Ophthalmology, Lancet Neurology, PubMed, AREDS2, ONTT, European Glaucoma Society Guidelines.

---

## Roadmap

- [x] **Fase 1** — Plataforma educacional 3D + chat RAG
- [x] **Fase 1.1** — Ingestão de PDFs reais (IMO, artigos PubMed)
- [x] **Fase 2** — Classificador de fundoscopia (Claude Vision + fallback) · Simulador de Campo Visual · 8 Casos Clínicos · Sidebar com abas
- [x] **Fase 2.0.1** — Segurança (magic byte validation, rate limiting, filename sanitization) · Persistência de sessão (SQLite) · Avaliação RAG (LLM-as-judge) · Nav header funcional
- [x] **Fase 2.0.2** — RAG tracing completo (chunks, scores, latência por etapa) · Modelo 3D corrigido (posicionamento anatômico, músculos extraoculares, bundle de fibras, esquema semântico de cores) · Modo 2D com hotspots interativos
- [x] **Fase 2.0.3** — SQLite: retenção automática de traces (1000 max, purge no startup), context_sent truncado a 500 chars · LOD: músculos fundidos em 1 draw call, segmentos reduzidos ~40% · Coordenação semântica fibra→campo visual: 5 regiões retinotópicas interativas com tooltip SVG + painel Campo Visual integrado
- [x] **Fase 2.1** — Classificador CNN EfficientNet-B4 treinado no APTOS 2019 (AUC 0.9442) · Pipeline 3 tiers (CNN → Claude Vision → feature-based) · Busca de hiperparâmetros com Algoritmo Genético · Export ONNX opset 17 com validação de consistência PT↔ONNX
- [x] **Fase 2.2** — YOLOv8n treinado no REFUGE2 (mAP50=0.957) · Detecção de disco/cup óptico + cup-to-disc ratio (CDR) · Pipeline expandido para 4 camadas: YOLO pre → CNN → Vision → feature-based · Elevação automática de suspeita de glaucoma (CDR ≥ 0.65)
- [ ] **Fase 3** — Deploy em produção (Vercel + Railway/Cloud Run)
- [ ] **Fase 4** — Modo imersivo WebXR
