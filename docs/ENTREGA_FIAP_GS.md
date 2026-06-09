# FIAP — Global Solution 2025
# Faculdade de Informática e Administração Paulista

---

**Grupo:** NeuroVision

**Integrantes:**
- Luan Gonçalves Gomes — RM: [566806]

**Turma:** [S]

**Curso:** [Inteligência Artificial]

**Professor Tutor:** Sabrina Otoni

**Professor Coordenador:** [--]

---

# QUERO CONCORRER

---

# NeuroVision — Plataforma de IA para Diagnóstico Neuro-Oftalmológico Aplicado à Medicina Espacial

---

## Sumário

1. [Introdução](#introdução)
2. [Desenvolvimento](#desenvolvimento)
3. [Resultados Esperados](#resultados-esperados)
4. [Conclusões](#conclusões)
5. [Referências Científicas](#referências-científicas)
6. [Links](#links)

---

## 1. Introdução

### 1.1 O Problema Real: Astronautas Estão Perdendo a Visão no Espaço

A exploração espacial de longa duração enfrenta uma ameaça silenciosa e crescente: a **Spaceflight-Associated Neuro-Ocular Syndrome (SANS)**, documentada pela NASA como um dos cinco maiores riscos para missões de longa duração. Estudos publicados no *New England Journal of Medicine* demonstram que aproximadamente **70% dos astronautas** em missões na Estação Espacial Internacional (ISS) desenvolvem alterações estruturais no nervo óptico e na retina causadas pela redistribuição de fluido cefalorraquidiano em microgravidade.

As manifestações clínicas incluem:
- **Edema do disco óptico** (papiledema)
- **Achatamento do globo ocular posterior**
- **Dobras coroideanas**
- **Hipermetropia progressiva**

Todas essas alterações são visíveis e diagnosticáveis por exame de **fundoscopia** — um exame de fundo de olho que pode ser realizado remotamente com equipamentos compactos a bordo de naves espaciais.

> *"Optic disc edema, globe flattening, choroidal folds, and hyperopic shifts observed in astronauts after long-duration space flight."*
> — Mader TH et al., **New England Journal of Medicine**, 2011.

Paralelamente, na medicina terrestre, a **retinopatia diabética** é a principal causa de cegueira prevenível no mundo — e seu diagnóstico precoce por análise de imagens de fundo de olho é um dos casos de uso mais consolidados de visão computacional aplicada à saúde.

### 1.2 A Solução: NeuroVision

**NeuroVision** é uma plataforma web de educação e diagnóstico assistido por IA que une três pilares:

1. **Educação anatômica imersiva** — visualização 3D/2D interativa do sistema visual humano com simulador de campo visual clínico
2. **Tutor clínico baseado em IA generativa** — chat RAG com base em literatura médica peer-reviewed (Walsh & Hoyt, Lancet Neurology, ONTT, EGS Guidelines — 21 documentos indexados)
3. **Classificação automatizada de fundoscopia** — pipeline de 4 camadas com dois modelos de deep learning treinados do zero para detectar retinopatia diabética e glaucoma

### 1.3 Conexão com a Economia Espacial e com o Tema da GS

A economia espacial não se limita a foguetes e satélites — abrange toda a cadeia de tecnologias que nascem ou se beneficiam da exploração espacial. A **visão computacional** é um pilar central desta economia: as mesmas arquiteturas de redes neurais que analisam imagens de satélite de observação da Terra são aplicadas aqui ao diagnóstico de imagens retinianas.

O raciocínio é bidirecional:
- **Espaço → Terra**: tecnologias desenvolvidas para missões espaciais (imagens multiespectrais, análise remota) melhoram o diagnóstico médico na Terra
- **Terra → Espaço**: plataformas como o NeuroVision são essenciais para missões tripuladas onde médicos especialistas não estão disponíveis — o diagnóstico de SANS precisa ser feito a bordo, de forma autônoma

> *"Telemedicine and AI-assisted diagnostics will be essential for deep space missions where real-time communication with Earth physicians is impossible."*
> — Komorowski M et al., **npj Digital Medicine**, 2021.

---
Interface NeuroVision - View 3D + Campo Visual
![Interface NeuroVision — Viewer 3D + Campo Visual](assets/screenshot_campo_visual_quiasma.png)

---

## 2. Desenvolvimento

### 2.1 Integração Entre Disciplinas

O NeuroVision foi construído integrando diretamente os conteúdos trabalhados ao longo do curso:

| Disciplina | Implementação no NeuroVision |
|---|---|
| **Inteligência Artificial** | YOLOv8n (detecção), EfficientNet-B4 (CNN), LLaMA-3.3-70b (LLM), Claude Haiku (Vision AI) |
| **Redes Neurais e Deep Learning** | Fine-tuning EfficientNet-B4 em 2 fases com AMP e WeightedRandomSampler + YOLOv8n treinado do zero no REFUGE2 |
| **Visão Computacional** | YOLOv8: detecção de disco/cup óptico com cálculo de cup-to-disc ratio; EfficientNet-B4: DR grading em 5 classes |
| **Algoritmos de Otimização** | Busca de hiperparâmetros com Algoritmo Genético (taxa de aprendizado, weight decay, batch size, intensidade de augmentation) |
| **APIs Cognitivas** | Groq API (LLaMA-3.3-70b) para RAG e avaliação; Anthropic API (Claude Haiku Vision) para análise multimodal de fundoscopia |
| **Banco de Dados** | SQLite — sessões de usuário, histórico de chat, RAG traces, avaliações LLM-as-judge |
| **Computação em Nuvem** | FastAPI containerizado (Cloud Run compatible); Groq Cloud; Anthropic Cloud |
| **Análise de Dados e Métricas** | AUC macro OvR, QWK ordinal, mAP50, mAP50-95; avaliação RAG automática (faithfulness + relevancy) |
| **Pipelines de Dados** | RAG pipeline completo com LangChain + ChromaDB + tracing por etapa (retrieval_ms · llm_ms · total_ms) |

![Stack de Tecnologias](assets/stack_overview.png)

### 2.2 Arquitetura Geral do Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NEUROVISION PLATFORM                          │
│                                                                       │
│  ┌──────────────────┐          ┌──────────────────────────────────┐  │
│  │  FRONTEND        │  HTTP    │  BACKEND (FastAPI)               │  │
│  │  Next.js 14      │◄────────►│  17 endpoints                    │  │
│  │  React Three     │          │                                  │  │
│  │  Fiber (3D)      │          │  ┌─────────────────────────────┐ │  │
│  │  Tailwind CSS    │          │  │  PIPELINE DE CLASSIFICAÇÃO  │ │  │
│  └──────────────────┘          │  │  4 camadas                  │ │  │
│                                │  │                             │ │  │
│                                │  │  [YOLO] → [CNN] →          │ │  │
│                                │  │  [Vision] → [Feature]      │ │  │
│                                │  └─────────────────────────────┘ │  │
│                                │                                  │  │
│                                │  ┌──────────┐  ┌─────────────┐  │  │
│                                │  │ RAG      │  │  SQLite DB  │  │  │
│                                │  │LangChain │  │  sessões    │  │  │
│                                │  │ChromaDB  │  │  traces     │  │  │
│                                │  │145 chunks│  │  avaliações │  │  │
│                                │  └──────────┘  └─────────────┘  │  │
│                                └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---
NeuroVision API — Swagger UI com todos os endpoints
![NeuroVision API — Swagger UI com todos os endpoints](assets/screenshot_swagger_ui.png)

---

### 2.3 Pipeline de Classificação de Fundoscopia — 4 Camadas

O coração técnico da plataforma é o pipeline de análise de imagens de fundo de olho:

```
Imagem de fundo de olho (fundoscopia)
        │
        ▼
┌────────────────────────────────────────────────────────┐
│  PRÉ-ETAPA — YOLOv8n  (optic_disc_yolov8.onnx)        │
│  Detecção de disco óptico e cup (escavação)            │
│  Dataset: REFUGE2 (1200 imagens com segmentação)       │
│  Saída: disc_bbox · cup_bbox · CDR · glaucoma_risk     │
└─────────────────────────┬──────────────────────────────┘
                          │ enriquece resultado com CDR
                          ▼
┌────────────────────────────────────────────────────────┐
│  TIER 0 — EfficientNet-B4  (fundoscopy_...v1.onnx)     │
│  DR grading 0–4 (APTOS 2019)  AUC 0.9442              │
│  Confiança mínima: 0.60                                │
└─────────────────────────┬──────────────────────────────┘
                          │ confiança < 0.60 ou modelo ausente
                          ▼
┌────────────────────────────────────────────────────────┐
│  TIER 1 — Claude Vision  (claude-haiku-4-5)            │
│  Análise multimodal — glaucoma, DMRI, papiledema, RD   │
└─────────────────────────┬──────────────────────────────┘
                          │ API indisponível
                          ▼
┌────────────────────────────────────────────────────────┐
│  TIER 2 — Feature-based (Pillow/NumPy)                 │
│  Heurísticas de cor e textura · zero APIs externas     │
└────────────────────────────────────────────────────────┘
```

**Decisão de design:** o pipeline é resiliente por design — se um tier falha ou não tem confiança suficiente, o próximo assume automaticamente. O sistema nunca retorna erro para o usuário final.

**Cup-to-Disc Ratio (CDR):** O YOLO calcula a razão entre a altura da escavação óptica (cup) e o disco óptico. É o principal marcador clínico de glaucoma:

| CDR | Risco |
|---|---|
| < 0.50 | Normal |
| 0.50 – 0.65 | Baixo |
| 0.65 – 0.80 | Moderado |
| ≥ 0.80 | **Alto** |

Se CDR ≥ 0.65 e a CNN classificou como "normal", o sistema **eleva automaticamente** a suspeita de glaucoma.

![Escala de Risco CDR](assets/cdr_risk_scale.png)

### 2.4 Treinamento dos Modelos de Deep Learning

#### 2.4.1 EfficientNet-B4 — Classificação de Retinopatia Diabética

**Dataset:** APTOS 2019 Blindness Detection (Kaggle) — 3.662 imagens, 5 classes (DR grau 0 a 4)

**Estratégia de treinamento em 2 fases:**
```python
# Fase 1: apenas o classificador (backbone congelado)
for param in model.model.parameters():
    param.requires_grad = False
# treina 10 epochs com lr=1e-3

# Fase 2: fine-tuning completo com lr menor
for param in model.model.parameters():
    param.requires_grad = True
# treina 20 epochs com lr=1e-4
```

**Técnicas aplicadas:**
- **Automatic Mixed Precision (AMP)** — reduz uso de memória e acelera treino
- **WeightedRandomSampler** — corrige desbalanceamento das classes (DR grau 0 é maioria)
- **Augmentation pesado** — RandomRotate90, HorizontalFlip, CLAHE, ColorJitter, CoarseDropout
- **Busca de hiperparâmetros com Algoritmo Genético** — otimizou: learning rate, weight decay, batch size, intensidade de augmentation

**Resultado:** AUC macro OvR = **0.9442** | QWK = 0.79

**Export para produção:** ONNX opset 17 com validação de consistência PyTorch ↔ ONNX e SHA-256 para auditoria.

```python
torch.onnx.export(
    model,
    dummy_input,
    output_path,
    opset_version=17,
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
)
```

#### 2.4.2 YOLOv8n — Detecção de Disco e Cup Óptico

**Dataset:** REFUGE2 (Retinal Fundus Glaucoma Challenge) — 1.200 imagens com máscaras de segmentação

**Pré-processamento das máscaras:**
O REFUGE2 usa codificação de 3 valores nas máscaras BMP:
- **0** = cup (escavação óptica)
- **128** = rim (anel neural)
- **255** = background

```python
def _parse_refuge2_mask(mask_path):
    mask = np.array(Image.open(mask_path).convert("L"))
    disc_mask = (mask < 255).astype(np.uint8)   # disco = cup + rim
    cup_mask  = (mask == 0).astype(np.uint8)    # só a escavação
    return disc_mask, cup_mask
```

**Conversão para formato YOLO:**
```python
def _mask_to_bbox(binary_mask, img_w, img_h):
    ys, xs = np.where(binary_mask > 0)
    if len(xs) == 0:
        return None
    xmin, xmax = xs.min(), xs.max()
    ymin, ymax = ys.min(), ys.max()
    cx = (xmin + xmax) / 2 / img_w
    cy = (ymin + ymax) / 2 / img_h
    w  = (xmax - xmin) / img_w
    h  = (ymax - ymin) / img_h
    return cx, cy, w, h
```

**Treinamento YOLOv8n:**
- 50 épocas (early stopping com patience=10 — convergiu em 28)
- Imagens 640×640
- Batch size 16
- GPU: RTX 3060 — duração total: ~3 minutos

**Resultados finais:**

| Classe | Precision | Recall | mAP50 |
|---|---|---|---|
| optic_disc | 0.997 | 0.992 | **0.995** |
| optic_cup | 0.896 | 0.897 | **0.918** |
| **Geral** | **0.947** | **0.945** | **0.957** |

![Métricas por Classe YOLOv8n](assets/yolo_class_metrics.png)

![Curva de Treinamento YOLOv8n](assets/yolo_training_curve.png)

#### 2.4.3 Inferência YOLO em Produção (ONNX Runtime)

O modelo exportado para ONNX é carregado diretamente no backend sem dependência do ultralytics:

```python
class OpticDiscDetector:
    def __init__(self, model_path: Path):
        self._session = ort.InferenceSession(
            str(model_path),
            providers=["CPUExecutionProvider"],
        )

    def _postprocess(self, output, orig_w, orig_h, conf_thresh=0.25):
        preds = output[0]
        if preds.shape[0] < preds.shape[-1]:
            preds = preds.T          # (1, 6, 8400) → (8400, 6)
        boxes = []
        for row in preds:
            x_c, y_c, w, h = row[:4]
            class_scores    = row[4:]
            cls_id          = int(np.argmax(class_scores))
            conf            = float(class_scores[cls_id])
            if conf < conf_thresh:
                continue
            boxes.append(BBox(
                xmin=int((x_c - w/2) * orig_w),
                ymin=int((y_c - h/2) * orig_h),
                xmax=int((x_c + w/2) * orig_w),
                ymax=int((y_c + h/2) * orig_h),
                confidence=conf,
                class_id=cls_id,
            ))
        return boxes
```

### 2.5 Pipeline RAG — Tutor Clínico com IA Generativa

```
PDF/artigo médico
      │
      ▼
[Ingestão] → chunking (1000 chars, overlap 200)
           → embeddings (all-MiniLM-L6-v2)
           → ChromaDB (persistente)
      │
      ▼
[Query do usuário]
      │
      ▼
[Retrieval] → top-5 chunks por similaridade coseno
           → threshold: 0.5 (abaixo = low-similarity alert)
      │
      ▼
[LLM] → LLaMA-3.3-70b-versatile (Groq API)
      → contexto = chunks + histórico da sessão
      │
      ▼
[Avaliação automática] → LLM-as-judge (faithfulness + relevancy)
                       → score persistido no SQLite
```

**Literatura indexada (21 documentos):** Walsh & Hoyt Clinical Neuro-Ophthalmology, IMO Guidelines, Lancet Neurology, AREDS2, ONTT Trial, European Glaucoma Society Guidelines, artigos PubMed de SANS.

### 2.6 Funcionalidades Implementadas

**Visualização Anatômica:**
- Viewer 3D com modelo GLTF do olho humano, 4 músculos extraoculares procedurais, bundle de 10 fibras nervosas semânticas interativas
- Viewer 2D com imagem anatômica e 10 hotspots interativos — mesma experiência sem WebGL
- Mapeamento retinotópico: 5 regiões de fibras (nasal superior/inferior · temporal superior/inferior · feixículo macular) com tooltip SVG ao hover

**Simulador de Campo Visual:**
Cada uma das 10 estruturas anatômicas tem mapeado o defeito perimétrico clínico correspondente em SVG:

| Estrutura | Defeito | Padrão Diagnóstico |
|---|---|---|
| Nervo Óptico | Amaurose monocular | OD inteiro + DPAR |
| Quiasma | Hemianopsia bitemporal | Adenoma hipofisário |
| Disco Óptico | Altitudinal superior | NOIA |
| Córtex V1 | Homônima + poupamento macular | AVC occipital |
| Radiações (temporal) | "Pie in the sky" | Lobo temporal |

**Casos Clínicos (8 casos de nível residência):**

| # | Caso | Estrutura |
|---|---|---|
| 1 | Neurite óptica — dor e escotoma central em mulher jovem | Nervo Óptico |
| 2 | Adenoma hipofisário — cefaleia e perda visual lateral | Quiasma |
| 3 | NOIA arterítica — perda súbita em idoso com cefaleia temporal | Disco Óptico |
| 4 | Retinopatia diabética proliferativa | Retina |
| 5 | Papiledema bilateral — HIC idiopática | Disco Óptico |
| 6 | AVC occipital com poupamento macular | Córtex Visual |
| 7 | Glaucoma avançado com campo tubular | Disco Óptico |
| 8 | DMRI úmida — metamorfopsia e escotoma central | Mácula |

---
Simulador de Campo Visual — Hemianopsia Bitemporal (Quiasma Óptico)
![Simulador de Campo Visual — Hemianopsia Bitemporal (Quiasma Óptico)](assets/screenshot_campo_visual_quiasma.png)

Casos Clínicos — Adenoma Hipofisário com perguntas diagnósticas e ponto de ensino
![Casos Clínicos — Adenoma Hipofisário com perguntas diagnósticas e ponto de ensino](assets/screenshot_casos_clinicos.png)

Classificador de Fundoscopia — análise em andamento
![Classificador de Fundoscopia — análise em andamento](assets/screenshot_classificador_analisando.png)

Classificador de Fundoscopia — resultado com análise completa
![Classificador de Fundoscopia — resultado com análise completa](assets/screenshot_classificador_resultado_full.png)
---

### 2.7 Observabilidade e Segurança

**Observabilidade:**
- Logging estruturado JSON via `structlog` em todos os serviços
- RAG tracing completo: chunks recuperados, scores de similaridade, latência por etapa (retrieval_ms · llm_ms · total_ms)
- Avaliação RAG automática: LLM-as-judge avalia faithfulness e relevancy em background
- Endpoints de auditoria: `/evaluation/stats` · `/traces` · `/traces/stats`
- Metadados dos modelos com SHA-256 para rastreabilidade (`model_metadata.json`, `yolo_metadata.json`)

**Segurança:**
- Magic byte validation nos uploads (rejeita arquivos falsos mesmo com extensão .jpg)
- Filename sanitization (previne path traversal)
- Rate limiting: `/chat` 30 req/min · `/classify` 10 req/min · `/ingest` 5 req/min por IP

### 2.8 Stack Técnica Completa

**Backend:**

| Componente | Tecnologia | Versão |
|---|---|---|
| API Server | FastAPI + Uvicorn | 0.115 |
| LLM (RAG + Avaliação) | Groq — LLaMA-3.3-70b-versatile | — |
| Detector YOLO | YOLOv8n via ONNX Runtime | 8.4.62 |
| Classificador CNN | EfficientNet-B4 via ONNX Runtime | opset 17 |
| Classificador Vision | Anthropic Claude Haiku Vision | claude-haiku-4-5 |
| Classificador fallback | Pillow + NumPy feature-based | — |
| RAG Framework | LangChain | 0.3 |
| Vector Store | ChromaDB | 0.5 |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | — |
| Persistência | SQLite | built-in |
| Rate Limiting | slowapi | 0.1.9 |
| Logging | structlog (JSON) | — |
| Containerização | Docker + docker-compose | — |

**Frontend:**

| Componente | Tecnologia | Versão |
|---|---|---|
| Framework | Next.js App Router | 14.2 |
| 3D Engine | React Three Fiber + Three.js | — |
| Campo Visual | SVG puro | — |
| Estilização | Tailwind CSS | — |

**Treinamento:**

| Componente | Tecnologia |
|---|---|
| Arquitetura CNN | EfficientNet-B4 (timm) |
| Arquitetura YOLO | YOLOv8n (ultralytics) |
| Framework | PyTorch 2.1 + CUDA |
| Otimização | Algoritmo Genético (DEAP-inspired, manual) |
| Export | ONNX opset 17 |

---

## 3. Resultados Esperados

### 3.1 Métricas dos Modelos

**EfficientNet-B4 — Retinopatia Diabética (APTOS 2019):**

| Métrica | Valor |
|---|---|
| AUC macro OvR | **0.9442** |
| Quadratic Weighted Kappa (QWK) | **0.79** |
| Dataset de treino | 3.662 imagens (5 classes) |
| Arquitetura | EfficientNet-B4 fine-tuned |
| Export | ONNX opset 17, 70 MB |

**YOLOv8n — Disco/Cup Óptico (REFUGE2):**

| Classe | Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|---|
| optic_disc | 0.997 | 0.992 | **0.995** | 0.849 |
| optic_cup | 0.896 | 0.897 | **0.918** | 0.439 |
| **Geral** | **0.947** | **0.945** | **0.957** | **0.644** |

Treinado em 28 épocas (early stopping), ~3 minutos no RTX 3060.

![Comparativo de Métricas dos Modelos](assets/models_metrics.png)

### 3.2 Casos de Teste Curados

As imagens a seguir foram selecionadas do conjunto de teste do REFUGE2 com base nos CDRs medidos a partir das máscaras de segmentação ground-truth:

**Glaucoma — Risco Alto (CDR ≥ 0.80):**

| Arquivo | CDR Real | Risco YOLO Esperado |
|---|---|---|
| T0304_CDR0.84.jpg | 0.84 | `alto` — neurological_flag=true |
| T0310_CDR0.83.jpg | 0.83 | `alto` |
| T0271_CDR0.82.jpg | 0.82 | `alto` |

**Glaucoma — Risco Moderado (CDR 0.65–0.79):**

| Arquivo | CDR Real | Risco YOLO Esperado |
|---|---|---|
| T0017_CDR0.76.jpg | 0.76 | `moderado` |
| T0119_CDR0.75.jpg | 0.75 | `moderado` |

**Normal (CDR < 0.50):**

| Arquivo | CDR Real | Risco YOLO Esperado |
|---|---|---|
| T0007_CDR0.32.jpg | 0.32 | `normal` |
| T0002_CDR0.35.jpg | 0.35 | `normal` |
| T0012_CDR0.36.jpg | 0.36 | `normal` |

**Classificador em ação — progressão de resultados:**

Resultado completo com análise detalhada
![Resultado 86% — Fundo de Olho Normal](assets/screenshot_classificador_resultado_86.png)

Resultado 72% — análise com suspeita
![Resultado 72% — análise com suspeita](assets/screenshot_classificador_resultado_72.png)

Resultado 86% — Fundo de Olho Normal
![Resultado completo com análise detalhada](assets/screenshot_classificador_resultado_full.png)

### 3.3 Resposta da API — Exemplo Real

Ao enviar uma imagem de fundoscopia para o endpoint `/classify`, a resposta inclui os dados dos 4 tiers do pipeline:

```json
{
  "condition": "glaucoma_suspect",
  "confidence": 0.91,
  "severity": "moderado",
  "neurological_flag": true,
  "disc_detected": true,
  "disc_confidence": 0.997,
  "cup_disc_ratio": 0.84,
  "glaucoma_risk": "alto",
  "features_detected": [
    "YOLO detectou escavação óptica aumentada (CDR=0.84) — suspeita de glaucoma elevada",
    "Escavação óptica ampliada",
    "Assimetria de disco"
  ],
  "analysis": "Imagem apresenta escavação óptica aumentada com cup-to-disc ratio de 0.84...",
  "recommendations": [
    "Consulta urgente com oftalmologista especialista em glaucoma",
    "Tonometria e perimetria computadorizada"
  ],
  "tier_used": "yolo+cnn+vision"
}
```

### 3.4 Impacto Esperado

- **Para astronautas**: treinamento de equipes médicas em missões espaciais para identificar SANS precocemente via fundoscopia remota
- **Para medicina terrestre**: rastreamento de retinopatia diabética com IA acessível — principal causa de cegueira prevenível no mundo
- **Para educação**: tutoria clínica interativa que reduz a curva de aprendizado em neuro-oftalmologia — especialidade com escassez global de profissionais
- **Para a economia espacial**: demonstração prática de que tecnologias de visão computacional desenvolvidas para análise de imagens orbitais são diretamente transferíveis para diagnóstico médico

Tutor Clínico RAG — resposta sobre SANS e sinais no disco óptico
![Tutor Clínico RAG — resposta sobre SANS e sinais no disco óptico](assets/screenshot_sans_chat.png)

## 4. Conclusões

### 4.1 O que foi Entregue

O NeuroVision entrega uma POC funcional e completa de plataforma de IA médica, implementando de forma integrada os principais conteúdos do curso:

- Dois modelos de deep learning treinados do zero com datasets científicos reais (APTOS 2019 e REFUGE2)
- Pipeline de 4 camadas com fallback automático entre tiers — arquitetura production-ready
- RAG com literatura médica peer-reviewed indexada e avaliação automática de qualidade
- Interface 3D/2D interativa com simulador clínico de campo visual
- 8 casos clínicos curados de nível residência médica
- Observabilidade completa: logging estruturado, traces, métricas, SHA-256 de modelos
- Containerização com Docker para deploy reprodutível

### 4.2 Decisões Técnicas Relevantes

**Por que YOLOv8n e não um modelo maior?**
YOLOv8n tem 3M de parâmetros e roda em CPU em ~2ms por imagem. Para um ambiente de diagnóstico remoto (bordo de uma nave, por exemplo), eficiência computacional é crítica. O mAP50=0.957 obtido mostra que o modelo pequeno é suficiente para esta tarefa.

**Por que ONNX Runtime no backend?**
Elimina a dependência de PyTorch e Ultralytics em produção, reduzindo o container de ~4GB para ~400MB. A imagem de produção roda em Cloud Run sem GPU.

**Por que pipeline com tiers ao invés de um único modelo?**
Resiliência: o sistema nunca retorna erro. Se o modelo CNN não tem confiança suficiente, Claude Vision assume. Se a API está offline, a análise feature-based garante uma resposta. Esta é a arquitetura correta para sistemas críticos.

**Por que Algoritmo Genético para hiperparâmetros?**
Grid search com 4 hiperparâmetros e 3 valores cada = 81 experimentos. O GA convergiu em ~15 experimentos (5 gerações × 3 pais), economizando ~80% do tempo de busca.

### 4.3 Próximos Passos

- **Fase 3 — Deploy em produção**: frontend no Vercel, backend no Railway ou Cloud Run
- **Fase 4 — WebXR imersivo**: visualização anatômica em realidade aumentada para treinamento médico
- **Dataset próprio**: coletar e rotular imagens de fundo de olho de astronautas (parceria com NASA Human Research Program)
- **Multi-label**: detectar simultaneamente múltiplas patologias em uma única fundoscopia

---

## 5. Referências Científicas

1. **Mader TH et al.** (2011). *Optic Disc Edema, Globe Flattening, Choroidal Folds, and Hyperopic Shifts Observed in Astronauts after Long-Duration Space Flight.* New England Journal of Medicine, 365, 1944–1964. DOI: 10.1056/NEJMoa1103053

2. **Lee AG et al.** (2020). *Spaceflight associated neuro-ocular syndrome (SANS) and the neuro-ophthalmologic effects of microgravity: a systematic review and meta-analysis.* npj Microgravity, 6, 7. DOI: 10.1038/s41526-020-0097-9

3. **Stenger MB et al.** (2022). *Towards a comprehensive and integrated strategy for addressing spaceflight-associated neuro-ocular syndrome.* NASA Human Research Program Technical Report.

4. **Tan M & Le QV** (2019). *EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks.* ICML 2019. arXiv: 1905.11946

5. **Orlando JI et al.** (2020). *REFUGE2 Challenge: Evaluation Framework for Glaucoma Grading from Fundus Photographs.* Medical Image Analysis, 59, 101570. DOI: 10.1016/j.media.2019.101570

6. **Redmon J & Farhadi A** (2018). *YOLOv3: An Incremental Improvement.* arXiv: 1804.02767. (arquitetura base estendida ao YOLOv8 pela Ultralytics)

7. **Gulshan V et al.** (2016). *Development and Validation of a Deep Learning Algorithm for Detection of Diabetic Retinopathy in Retinal Fundus Photographs.* JAMA, 316(22), 2402–2410. DOI: 10.1001/jama.2016.17216

8. **Komorowski M et al.** (2021). *Intensive care medicine in 2050: precision medicine, artificial intelligence, and space medicine.* Intensive Care Medicine, 47(2), 236–238.

9. **NASA Human Research Program** (2023). *Human Research Roadmap — SANS Evidence Report.* NASA Technical Reports Server. https://humanresearchroadmap.nasa.gov

10. **APTOS 2019 Blindness Detection** (2019). Kaggle Competition Dataset — Asia Pacific Tele-Ophthalmology Society.

---

## 6. Links

| Item | Link |
|---|---|
| Repositório GitHub | https://github.com/TheFirstGomes/NeuroVision |
| Vídeo YouTube (não listado) | [INSERIR LINK DO VÍDEO AQUI] |
| Demo local — Frontend | http://localhost:3000 |
| Demo local — API Swagger | http://localhost:8000/docs |

---

*Documento gerado em 09/06/2026. Todos os códigos apresentados estão em formato texto conforme exigido pelo regulamento da GS.*
