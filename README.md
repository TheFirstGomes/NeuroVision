# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href= "https://www.fiap.com.br/"><img src="assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=40% height=40%></a>
</p>

<br>

# NeuroVision — Plataforma de IA para Diagnóstico Neuro-Oftalmológico Aplicado à Medicina Espacial

## Grupo NeuroVision

## 👨‍🎓 Integrantes:
- <a href="https://www.linkedin.com/in/luan-g-432896b5/">Luan Gonçalves Gomes</a>

## 👩‍🏫 Professores:
### Tutor(a)
- <a href="https://www.linkedin.com/in/sabrina-otoni-22525519b/">Sabrina Otoni</a>
### Coordenador(a)
- <a href="https://www.linkedin.com/company/inova-fusca">Nome do Coordenador</a>

---

## 👩🏻‍💻 Sobre este Projeto

A exploração espacial de longa duração enfrenta uma ameaça silenciosa e crescente: a **Spaceflight-Associated Neuro-Ocular Syndrome (SANS)**, documentada pela NASA como um dos cinco maiores riscos para missões de longa duração. Estudos publicados no *New England Journal of Medicine* demonstram que aproximadamente **70% dos astronautas** em missões na ISS desenvolvem alterações estruturais no nervo óptico e na retina causadas pela redistribuição de fluido cefalorraquidiano em microgravidade.

As manifestações clínicas incluem **edema do disco óptico** (papiledema), **achatamento do globo ocular posterior**, **dobras coroideanas** e **hipermetropia progressiva** — todas visíveis e diagnosticáveis por exame de fundoscopia. Casos graves podem resultar em perda visual permanente, comprometendo missões tripuladas de longo prazo, incluindo futuras expedições à Lua e Marte.

> *"Optic disc edema, globe flattening, choroidal folds, and hyperopic shifts observed in astronauts after long-duration space flight."*
> — Mader TH et al., **New England Journal of Medicine**, 2011. DOI: 10.1056/NEJMoa1103053

---

## 🎯 Objetivo

**NeuroVision** é uma plataforma educacional e de diagnóstico assistido por IA, desenvolvida para capacitar profissionais de saúde a identificar e interpretar alterações neuro-oftalmológicas — especialmente aquelas associadas à medicina espacial. A plataforma conecta três pilares:

1. **Educação anatômica imersiva** — visualização 3D/2D interativa do sistema visual humano com simulador de campo visual clínico
2. **IA generativa como tutor clínico** — chat RAG com base em literatura médica peer-reviewed (Walsh & Hoyt, Lancet Neurology, ONTT, EGS Guidelines)
3. **Classificação automatizada de fundoscopia** — pipeline de 4 camadas: **YOLOv8n** (detecção de disco/cup óptico — dataset REFUGE2) → **EfficientNet-B4** (DR grading, APTOS 2019, AUC 0.9442) → **Claude Vision** → análise feature-based; calcula cup-to-disc ratio (CDR) para rastreamento de glaucoma

---

## 🧠 Tecnologias Aplicadas

| Critério de Avaliação | Implementação no NeuroVision |
|-----------------------|------------------------------|
| Inteligência Artificial | YOLOv8n (detecção), EfficientNet-B4 (CNN), LLaMA-3.3-70b (LLM), Claude Haiku (Vision) |
| Redes Neurais | Fine-tuning EfficientNet-B4 em 2 fases (AMP, WeightedRandomSampler) + YOLOv8 treinado do zero |
| Visão Computacional | YOLOv8: detecção disco/cup óptico (REFUGE2) + CDR; EfficientNet-B4: DR grading 5 classes |
| Algoritmos Genéticos | Busca de hiperparâmetros (lr, weight decay, batch size, augmentation) via GA |
| APIs Cognitivas | Groq API (LLaMA), Anthropic API (Claude Vision) |
| Pipelines de Dados | RAG pipeline com LangChain + ChromaDB + tracing por etapa |
| SQL/NoSQL | SQLite — sessões, histórico de chat, RAG traces, avaliações LLM-as-judge |
| Computação em Nuvem | FastAPI containerizado (Cloud Run compatible), Groq Cloud, Anthropic Cloud |
| Análise de Dados | Métricas QWK, AUC macro OvR, F1 macro, sensibilidade em graus graves |
| Avaliação de Modelos | LLM-as-judge (faithfulness + relevancy), QWK ordinal para DR grading |

---

## 📁 Estrutura de Pastas

```bash
neurovision/
├── assets/                        # Screenshots e gráficos gerados (usados na documentação)
├── backend/                       # API FastAPI — servidor de IA e diagnóstico
│   ├── app/
│   │   ├── main.py                # Entrypoint FastAPI — 17 endpoints
│   │   ├── domain/models.py       # Schemas Pydantic
│   │   ├── services/
│   │   │   ├── classifier_service.py   # Pipeline 4 camadas (YOLO pre → CNN → Vision → feature)
│   │   │   ├── optic_disc_detector.py  # YOLOv8 ONNX Runtime — disco/cup + CDR
│   │   │   ├── cnn_classifier.py       # EfficientNet-B4 ONNX Runtime wrapper
│   │   │   ├── rag_service.py          # LangChain RAG chain com tracing
│   │   │   ├── cases_service.py        # 8 casos clínicos curados
│   │   │   ├── evaluation_service.py   # LLM-as-judge (faithfulness + relevancy)
│   │   │   └── anatomy_service.py      # 10 estruturas anatômicas com dados clínicos
│   │   └── infrastructure/
│   │       ├── vector_store.py    # ChromaDB abstraction
│   │       ├── database.py        # SQLite ORM
│   │       └── security.py        # Magic byte validation + rate limiting
│   ├── models/
│   │   ├── fundoscopy_efficientnet_b4_v1.onnx   # EfficientNet-B4 — DR grading (70 MB)
│   │   ├── model_metadata.json                   # Métricas, SHA-256, opset
│   │   ├── optic_disc_yolov8.onnx               # YOLOv8n — disco/cup óptico (12 MB)
│   │   └── yolo_metadata.json                   # mAP50=0.957, SHA-256, classes
│   └── requirements.txt
├── frontend/                      # Interface Next.js 14
│   ├── app/page.tsx               # Layout principal — viewer 3D + sidebar + modais
│   └── components/
│       ├── EyeViewer3D.tsx        # Three.js/React Three Fiber
│       ├── EyeViewer2D.tsx        # Modo 2D anatômico com hotspots
│       └── VisualFieldPanel.tsx   # Simulador de campo visual (SVG)
├── train/                         # Pipeline de treinamento dos modelos
│   ├── train_efficientnet.py      # Fine-tuning EfficientNet-B4 (APTOS 2019)
│   ├── export_to_onnx.py          # Export PyTorch → ONNX opset 17
│   ├── ga_hyperparam_search.py    # Otimização por Algoritmo Genético
│   ├── prepare_refuge_yolo.py     # Converte máscaras REFUGE2 → YOLO bounding boxes
│   └── train_yolo.py              # Treina YOLOv8n + export ONNX → backend/models/
├── test_images/                   # Imagens de teste curadas do REFUGE2
│   ├── glaucoma_alto/             # CDR 0.82–0.84 — risco alto
│   ├── glaucoma_moderado/         # CDR 0.75–0.76 — risco moderado
│   └── normal/                    # CDR 0.32–0.36 — sem suspeita
├── docs/
│   ├── ENTREGA_FIAP_GS.md         # Documento completo de entrega FIAP (Introdução → Conclusões)
│   └── TECHNICAL.md               # Documentação técnica detalhada (endpoints, stack, env vars)
├── tools/
│   └── generate_pdf.py            # Gera ENTREGA_FIAP_GS.pdf a partir do .md
├── ENTREGA_FIAP_GS.pdf            # PDF de entrega FIAP — pronto para download
├── README.md                      # Este arquivo — apresentação do projeto (formato FIAP)
├── docker-compose.yml             # Orquestra backend + frontend em containers
├── start.bat                      # Inicialização rápida no Windows
└── start.sh                       # Inicialização rápida no Linux/macOS
```

---

## 🔧 Como Executar

### Pré-requisitos

- Python 3.12+
- Node.js 18+
- Chave de API **Groq** — gratuita em [console.groq.com](https://console.groq.com)
- Chave de API **Anthropic** *(opcional)* — habilita Claude Vision

### Instalação e execução (Windows)

```bash
# 1. Clone o repositório
git clone https://github.com/TheFirstGomes/NeuroVision.git
cd NeuroVision

# 2. Configure as variáveis de ambiente
# Crie backend/.env com o seguinte conteúdo:
# GROQ_API_KEY=gsk_...
# ANTHROPIC_API_KEY=sk-ant-...   (opcional)
# ALLOWED_ORIGINS=http://localhost:3000

# 3. Inicie backend e frontend
.\start.bat
```

### Execução manual

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (outro terminal)
cd frontend
npm install
npm run dev
```

### URLs após inicialização

| Serviço | URL |
|---------|-----|
| Interface principal | http://localhost:3000 |
| API REST | http://localhost:8000 |
| Documentação interativa (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

---

## 🗃 Histórico de Lançamentos

* **1.1.0** — 09/06/2026
    * YOLOv8n treinado no REFUGE2 (1200 imgs) para detecção de disco/cup óptico
    * Cup-to-disc ratio (CDR) calculado automaticamente em cada classificação
    * Elevação automática de suspeita de glaucoma quando CDR >= 0.65
    * Pipeline expandido para 4 camadas: YOLO pre → CNN → Vision → feature-based

* **1.0.0** — 09/06/2026
    * Pipeline 3 tiers: EfficientNet-B4 ONNX → Claude Vision → feature-based
    * EfficientNet-B4 treinado no APTOS 2019 — AUC 0.9442 / QWK salvo como métrica primária
    * Busca de hiperparâmetros com Algoritmo Genético (GA)
    * Export ONNX opset 17 com validação de consistência PyTorch ↔ ONNX

* **0.4.0** — 08/06/2026
    * RAG tracing completo — chunks, similarity scores, latência por etapa
    * Mapeamento retinotópico fibra → campo visual com 5 regiões semânticas interativas
    * Modelo 3D anatômico com músculos extraoculares e bundle de fibras do nervo óptico

* **0.3.0** — 07/06/2026
    * Classificador de fundoscopia — Tier 1 (Claude Vision) + Tier 2 (feature-based)
    * Simulador de Campo Visual — 10 estruturas com defeitos perimétricos clínicos precisos
    * 8 Casos Clínicos curados com gabarito (nível residência)
    * Avaliação RAG automática — LLM-as-judge (faithfulness + relevancy)

* **0.2.0** — 06/06/2026
    * Chat RAG com tutor clínico — LangChain + ChromaDB + LLaMA-3.3-70b
    * Ingestão de PDFs — Walsh & Hoyt, IMO, Lancet Neurology, AREDS2, ONTT, EGS Guidelines
    * Rate limiting, magic byte validation, persistência de sessão (SQLite)

* **0.1.0** — 05/06/2026
    * Viewer 3D/2D interativo do olho humano com React Three Fiber
    * 10 estruturas anatômicas clicáveis com painel de patologias e conexões neurológicas

---

## 🔬 Referências Científicas

1. **Mader TH et al.** (2011). *Optic Disc Edema, Globe Flattening, Choroidal Folds, and Hyperopic Shifts Observed in Astronauts after Long-Duration Space Flight.* New England Journal of Medicine, 365, 1944–1964. DOI: 10.1056/NEJMoa1103053

2. **Lee AG et al.** (2020). *Spaceflight associated neuro-ocular syndrome (SANS) and the neuro-ophthalmologic effects of microgravity: a systematic review and meta-analysis.* npj Microgravity, 6, 7. DOI: 10.1038/s41526-020-0097-9

3. **Stenger MB et al.** (2022). *Towards a comprehensive and integrated strategy for addressing spaceflight-associated neuro-ocular syndrome.* NASA Human Research Program Technical Report.

4. **Tan M & Le QV** (2019). *EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks.* ICML 2019. arXiv: 1905.11946

5. **Komorowski M et al.** (2021). *Intensive care medicine in 2050: precision medicine, artificial intelligence, and space medicine.* Intensive Care Medicine, 47(2), 236–238. DOI: 10.1007/s00134-020-06303-5

6. **Gulshan V et al.** (2016). *Development and Validation of a Deep Learning Algorithm for Detection of Diabetic Retinopathy in Retinal Fundus Photographs.* JAMA, 316(22), 2402–2410. DOI: 10.1001/jama.2016.17216

7. **NASA Human Research Program** (2023). *Human Research Roadmap — SANS Evidence Report.* NASA Technical Reports Server.

8. **APTOS 2019 Blindness Detection** (2019). Kaggle Competition Dataset — Asia Pacific Tele-Ophthalmology Society.

9. **Orlando JI et al.** (2020). *REFUGE2 Challenge: Evaluation Framework for Glaucoma Grading from Fundus Photographs.* Medical Image Analysis, 59, 101570. DOI: 10.1016/j.media.2019.101570

10. **Redmon J & Farhadi A** (2018). *YOLOv3: An Incremental Improvement.* arXiv: 1804.02767. (base architecture extended to YOLOv8 by Ultralytics)

---

## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/SabrinaOtoni/TEMPLATE-FIAP-GRAD-ON-IA">MODELO GIT FIAP</a> por <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">FIAP</a> está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>
