"""
Clinical Cases Service — NeuroVision

8 curated neuro-ophthalmology cases for resident-level education.
Each case includes patient history, examination findings, 3 questions
with gabarito + explanation, and links to the 3D viewer and visual field simulator.

Cases cover:
  1. Neurite óptica (EM)
  2. Adenoma hipofisário com hemianopsia bitemporal
  3. NOIA arterítica (arterite de células gigantes)
  4. Retinopatia diabética proliferativa
  5. Papiledema bilateral (hipertensão intracraniana idiopática)
  6. AVC occipital com poupamento macular
  7. Glaucoma avançado com campo tubular
  8. DMRI úmida com metamorfopsia
"""
from app.domain.models import ClinicalCase, CaseListItem, CasePatient, CaseQuestion

# ── Case data ─────────────────────────────────────────────────────────────────

_CASES_RAW: list[dict] = [
    {
        "id": "case_001",
        "title": "Dor ocular e escotoma central em mulher jovem",
        "category": "Nervo Óptico",
        "difficulty": 2,
        "related_structure": "nervo_optico",
        "visual_field_structure": "nervo_optico",
        "patient": {
            "age": 27,
            "sex": "F",
            "chief_complaint": "Dor ocular direita há 3 dias, piora com movimentação ocular, associada a visão turva central.",
            "history": (
                "Saudável. Refere episódio similar há 18 meses com resolução espontânea em 6 semanas. "
                "Sem outras queixas neurológicas no momento."
            ),
            "examination": (
                "AV OD: 20/200. AV OE: 20/20. DPAR positivo OD (swing flashlight test). "
                "Fundoscopia OD: leve hiperemia do disco óptico. Fundoscopia OE: normal. "
                "Visão de cores OD: 3/14 placas de Ishihara (OE: 14/14). "
                "Campo visual: escotoma central OD."
            ),
        },
        "questions": [
            {
                "question": "Qual é o diagnóstico mais provável?",
                "answer": "Neurite óptica retrobulbar direita",
                "explanation": (
                    "A tríade clássica é: (1) perda visual aguda monocular, (2) dor à movimentação ocular e "
                    "(3) DPAR. Fundoscopia normal é esperada — 2/3 das neurites ópticas são retrobulbares "
                    "(o segmento acometido é posterior ao disco). Quando o disco está inflamado, "
                    "chama-se papilite, mais comum em crianças."
                ),
            },
            {
                "question": "Qual exame complementar tem maior impacto diagnóstico e prognóstico?",
                "answer": "RNM de crânio e órbitas com gadolínio",
                "explanation": (
                    "A RNM revela realce do nervo óptico no segmento orbital na sequência T1+Gd. "
                    "Mais importante: lesões desmielinizantes cerebrais (critério de McDonald) "
                    "determinam o risco de conversão para Esclerose Múltipla — presente em "
                    "~50% na RNM inicial. Se RNM alterada → risco de 72% de EM em 15 anos (ONTT)."
                ),
            },
            {
                "question": "O que é o fenômeno de Uhthoff e qual sua importância diagnóstica?",
                "answer": "Piora dos sintomas visuais com aumento da temperatura corporal",
                "explanation": (
                    "Presente em ~30% das neurites. Ocorre porque o calor reduz a velocidade de "
                    "condução em axônios desmielinizados (o nó de Ranvier desmielinizado tem limiar "
                    "de temperatura reduzido). Altamente sugestivo de desmielinização. "
                    "Atividade física intensa, banho quente ou febre são gatilhos comuns."
                ),
            },
        ],
        "teaching_point": (
            "Neurite óptica é a manifestação inaugural de EM em ~25% dos casos. "
            "O ONTT (Optic Neuritis Treatment Trial) demonstrou que metilprednisolona EV "
            "acelera a recuperação mas não melhora o prognóstico visual a longo prazo. "
            "O interferon beta reduz o risco de conversão para EM em pacientes com RNM alterada."
        ),
    },
    {
        "id": "case_002",
        "title": "Cefaleia progressiva e perda visual lateral em mulher de meia-idade",
        "category": "Quiasma",
        "difficulty": 1,
        "related_structure": "quiasma_optico",
        "visual_field_structure": "quiasma_optico",
        "patient": {
            "age": 42,
            "sex": "F",
            "chief_complaint": (
                "Cefaleia progressiva há 4 meses, associada a dificuldade de perceber objetos "
                "nas laterais. Relata ter 'batido o carro no retrovisor' duas vezes no último mês."
            ),
            "history": (
                "Galactorreia há 6 meses. Amenorreia secundária há 8 meses. "
                "Sem uso de medicamentos. Sem história familiar de tumores."
            ),
            "examination": (
                "AV bilateral 20/20. Sem DPAR. Fundoscopia: palidez temporal bilateral dos discos ópticos (leve). "
                "Campimetria computadorizada: hemianopsia bitemporal clássica com respeito à linha vertical. "
                "Prolactina sérica: 280 ng/mL (normal < 25 ng/mL)."
            ),
        },
        "questions": [
            {
                "question": "Qual estrutura neurológica está sendo comprimida e qual o padrão de campo visual?",
                "answer": "Quiasma óptico — fibras nasais cruzadas → hemianopsia bitemporal",
                "explanation": (
                    "As fibras nasais de cada retina cruzam no quiasma para o trato óptico contralateral. "
                    "Uma lesão central no quiasma (clássico de adenoma hipofisário) interrompe essas fibras, "
                    "eliminando os campos temporais de ambos os olhos. "
                    "O paciente perde o que está nas laterais — daí o 'fenômeno do slip' no volante."
                ),
            },
            {
                "question": "Qual é a causa mais provável e quais os achados hormonais esperados?",
                "answer": "Prolactinoma (adenoma hipofisário secretor de prolactina)",
                "explanation": (
                    "Prolactinoma é o tumor hipofisário mais comum (40% dos adenomas). "
                    "Prolactina > 200 ng/mL é quase diagnóstica de prolactinoma macroscópico. "
                    "Em mulheres: amenorreia, galactorreia, infertilidade. "
                    "Em homens: disfunção erétil, ginecomastia (frequentemente diagnosticado mais tarde, "
                    "quando o tumor já é maior e causa defeito de campo)."
                ),
            },
            {
                "question": "Qual é o tratamento de primeira linha?",
                "answer": "Agonista dopaminérgico — cabergolina ou bromocriptina",
                "explanation": (
                    "Diferente de outros adenomas hipofisários, o prolactinoma responde "
                    "dramaticamente à terapia medicamentosa. Cabergolina (semanal) normaliza "
                    "a prolactina em >90% dos casos e reduz o tumor em 70-80%. "
                    "Cirurgia (via transesfenoidal) reservada para falha medicamentosa ou apoplexia pituitária. "
                    "O campo visual melhora em semanas após início do tratamento."
                ),
            },
        ],
        "teaching_point": (
            "Hemianopsia bitemporal é virtualmente patognomônica de lesão quiasmática. "
            "A palidez temporal do disco óptico (atrofia em 'gravata borboleta') é sinal tardio "
            "de compressão crônica das fibras nasais. Sempre solicitar campimetria computadorizada, "
            "não apenas confrontação, pois defeitos iniciais são sutis."
        ),
    },
    {
        "id": "case_003",
        "title": "Perda visual súbita indolor em idoso com cefaleia temporal",
        "category": "Disco Óptico",
        "difficulty": 2,
        "related_structure": "disco_optico",
        "visual_field_structure": "disco_optico",
        "patient": {
            "age": 72,
            "sex": "M",
            "chief_complaint": (
                "Perda visual súbita e completa no olho direito ao acordar esta manhã. "
                "Sem dor ocular. Relata cefaleia temporal direita há 3 semanas e dor ao mastigar."
            ),
            "history": (
                "HAS, DM2. Perda de 4kg em 2 meses. Referindo 'dor nos ombros e quadris' há 6 semanas. "
                "VSH: 112 mm/h (laboratório de urgência). PCR: 8,4 mg/dL."
            ),
            "examination": (
                "AV OD: percepção de luz. AV OE: 20/20. DPAR positivo OD. "
                "Fundoscopia OD: disco óptico pálido e edemaciado, hemorragias peripapilares. "
                "Fundoscopia OE: normal. "
                "Artéria temporal direita: endurecida, não pulsátil à palpação, sensível."
            ),
        },
        "questions": [
            {
                "question": "Qual é o diagnóstico e qual a urgência do tratamento?",
                "answer": "NOIA arterítica por arterite de células gigantes (temporal) — EMERGÊNCIA",
                "explanation": (
                    "NOIA-A é causada por vasculite granulomatosa das artérias ciliares posteriores. "
                    "O olho contralateral é ameaçado em 30-40% dos casos nas próximas 48-72h sem tratamento. "
                    "Corticoide deve ser iniciado IMEDIATAMENTE, antes da biópsia. "
                    "Não aguardar resultado da biópsia para tratar — o diagnóstico clínico já justifica o tratamento."
                ),
            },
            {
                "question": "Qual exame confirma o diagnóstico e como deve ser interpretado?",
                "answer": "Biópsia da artéria temporal — segmento ≥ 2 cm para reduzir falso-negativo por 'skip lesions'",
                "explanation": (
                    "A biópsia mostra células gigantes multinucleadas, infiltrado inflamatório na adventícia, "
                    "fragmentação da lâmina elástica interna. Sensibilidade: 85-90% para segmento longo. "
                    "VSH > 50 mm/h em > 50 anos + sintomas + biópsia positiva = diagnóstico definitivo. "
                    "Biópsia pode ser realizada até 2 semanas após início do corticoide sem perder sensibilidade."
                ),
            },
            {
                "question": "Qual padrão de campo visual é esperado na NOIA?",
                "answer": "Defeito altitudinal — superior ou inferior com borda horizontal precisa",
                "explanation": (
                    "O disco óptico tem suprimento dividido: metade superior e inferior por artérias ciliares "
                    "diferentes. Infarto de uma metade → defeito altitudinal que respeita o meridiano horizontal. "
                    "Na NOIA não-arterítica, o defeito inferior é mais comum (suprimento superior é mais vulnerável). "
                    "O defeito 'duro' (borda horizontal exata) distingue NOIA de glaucoma (bordo arqueado)."
                ),
            },
        ],
        "teaching_point": (
            "Arterite de células gigantes é a vasculite sistêmica mais comum em > 50 anos. "
            "Polimialgia reumática coexiste em 50% dos casos. "
            "Prednisona 1 mg/kg/dia — não aguardar biópsia. "
            "O olho contralateral é a tragédia evitável: cada hora sem tratamento aumenta o risco."
        ),
    },
    {
        "id": "case_004",
        "title": "Piora visual progressiva em diabético de longa data",
        "category": "Retina",
        "difficulty": 1,
        "related_structure": "retina",
        "visual_field_structure": "retina",
        "patient": {
            "age": 55,
            "sex": "M",
            "chief_complaint": "Piora visual bilateral progressiva há 6 meses. Refere 'manchas flutuantes' no OD.",
            "history": (
                "DM2 há 18 anos, controle irregular (HbA1c atual: 10,2%). "
                "HAS. Última consulta com oftalmologista há 3 anos."
            ),
            "examination": (
                "AV OD: 20/200. AV OE: 20/60. "
                "Fundoscopia OD: neovascularização do disco (NVD), hemorragia vítrea parcial, "
                "múltiplos microaneurismas, exsudatos duros maculares. "
                "Fundoscopia OE: microaneurismas difusos, exsudatos duros, edema macular clinicamente significativo."
            ),
        },
        "questions": [
            {
                "question": "Como estadiar a retinopatia diabética neste paciente?",
                "answer": "OD: Retinopatia Diabética Proliferativa (RDP) com hemorragia vítrea. OE: RDNP grave com edema macular clinicamente significativo",
                "explanation": (
                    "Estadiamento: RDNP leve (microaneurismas apenas) → moderada (+ hemorragias/exsudatos) → "
                    "grave (regra 4-2-1: hemorragias nos 4 quadrantes, ou rosário venoso em ≥2 quadrantes, "
                    "ou IRMA em ≥1 quadrante) → Proliferativa (neovascularização). "
                    "NVD = neovascularização do disco = forma mais agressiva de RDP."
                ),
            },
            {
                "question": "Qual o tratamento prioritário para o OD?",
                "answer": "Fotocoagulação panretiniana (PRP) urgente ± injeção intravítrea de anti-VEGF",
                "explanation": (
                    "PRP (fotocoagulação com laser) destrói a retina isquêmica periférica, "
                    "reduzindo o estímulo para VEGF e regressão da neovascularização. "
                    "O DRCR.net (Protocol S) mostrou que anti-VEGF intravítreo (ranibizumabe) "
                    "não é inferior ao PRP em RDP, com menos perda de campo periférico. "
                    "Para hemorragia vítrea densa → vitrectomia pars plana."
                ),
            },
            {
                "question": "Qual a fisiopatologia da neovascularização retiniana no diabetes?",
                "answer": "Isquemia retiniana → superprodução de VEGF → neovascularização patológica",
                "explanation": (
                    "Hiperglicemia crônica → dano ao endotélio de pericitos retinianos → "
                    "oclusão de capilares → isquemia retiniana → upregulation de HIF-1α → "
                    "produção excessiva de VEGF → neovascularização anômala (frágil, sem barreira). "
                    "Esses neovasos sangram facilmente (hemorragia vítrea) e provocam tração (DR tracional). "
                    "Anti-VEGF neutraliza diretamente esse mecanismo."
                ),
            },
        ],
        "teaching_point": (
            "A RDP é prevenível com controle metabólico rigoroso. "
            "O UKPDS demonstrou que cada 1% de redução de HbA1c reduz complicações microvasculares em 37%. "
            "Rastreamento recomendado: diabéticos tipo 1 → fundoscopia a partir de 5 anos de doença; "
            "tipo 2 → ao diagnóstico, anualmente se sem retinopatia."
        ),
    },
    {
        "id": "case_005",
        "title": "Cefaleia e visão de estrelas em mulher jovem obesa",
        "category": "Disco Óptico",
        "difficulty": 2,
        "related_structure": "disco_optico",
        "visual_field_structure": "disco_optico",
        "patient": {
            "age": 32,
            "sex": "F",
            "chief_complaint": (
                "Cefaleia holocraniana progressiva há 2 meses, piora ao deitar ou fazer esforço. "
                "Episódios de 'visão de estrelas' e escurecimento visual transitório de segundos (oscilações visuais)."
            ),
            "history": (
                "Obesidade (IMC: 38). Uso de anticoncepcional oral combinado há 1 ano. "
                "Acúfeno pulsátil unilateral. Sem déficits neurológicos focais."
            ),
            "examination": (
                "AV bilateral 20/20. Fundoscopia: papiledema bilateral grau 3 (Frisén), "
                "bordas do disco apagadas, hemorragias peripapilares em chama de vela, sem exsudatos. "
                "Campimetria: aumento bilateral da mancha cega, constricção periférica leve. "
                "Ausência de déficits motores ou sensitivos. RNM de crânio: normal."
            ),
        },
        "questions": [
            {
                "question": "Qual é o diagnóstico sindrômico e quais os critérios?",
                "answer": "Hipertensão Intracraniana Idiopática (HII) — pseudotumor cerebri",
                "explanation": (
                    "Critérios de Dandy modificados: (1) sintomas de HIC, (2) papiledema bilateral, "
                    "(3) neuroimagem normal (sem lesão de massa, hidrocefalia ou trombose), "
                    "(4) LCR com composição normal e pressão > 25 cmH2O, (5) sem outra causa. "
                    "Acomete predominantemente mulheres obesas em idade fértil (F:M = 9:1)."
                ),
            },
            {
                "question": "Qual exame confirma o diagnóstico e qual o valor esperado?",
                "answer": "Punção lombar com medida de pressão de abertura — esperado > 25 cmH2O (decúbito lateral)",
                "explanation": (
                    "A punção lombar é diagnóstica E terapêutica: a drenagem de LCR alivia imediatamente "
                    "a cefaleia e as oscilações visuais. Valores > 30 cmH2O são altamente sugestivos. "
                    "A composição do LCR deve ser normal (descarta meningite, carcinomatose). "
                    "Realizar sempre APÓS a neuroimagem para excluir hipertensão por massa com herniação."
                ),
            },
            {
                "question": "Quais são os pilares do tratamento e qual o risco sem tratamento?",
                "answer": "Perda de peso + acetazolamida. Risco: perda visual permanente por atrofia óptica",
                "explanation": (
                    "Acetazolamida (inibidor de anidrase carbônica) reduz produção de LCR — dose 1-4g/dia. "
                    "O IIH Treatment Trial (IIHTT) confirmou eficácia da combinação dieta + acetazolamida. "
                    "Casos refratários: shunt lomboperitoneal ou fenestração da bainha do nervo óptico. "
                    "Sem tratamento: atrofia óptica bilateral com perda visual permanente em 10-25% dos casos."
                ),
            },
        ],
        "teaching_point": (
            "Oscilações visuais (episódios de escurecimento de segundos) em papiledema bilateral "
            "são sinal de alarme — indicam isquemia transitória do nervo óptico por compressão. "
            "O anticoncepcionais orais e tetraciclinas são fatores de risco modificáveis. "
            "Monitorar campo visual seriado: é o principal desfecho funcional."
        ),
    },
    {
        "id": "case_006",
        "title": "Episódio súbito de 'zona escura' no campo visual esquerdo",
        "category": "Córtex Visual",
        "difficulty": 2,
        "related_structure": "cortex_visual",
        "visual_field_structure": "cortex_visual",
        "patient": {
            "age": 68,
            "sex": "M",
            "chief_complaint": (
                "Aparecimento súbito de uma 'sombra escura' no lado esquerdo do campo visual "
                "há 6 horas. Sem dor. Sem cefaleia. Nega perda de visão de um olho isolado."
            ),
            "history": "HAS, FA não anticoagulada. Tabagista 40 maços-ano. AIT prévio há 1 ano.",
            "examination": (
                "AV bilateral 20/30. Sem DPAR. Fundoscopia: normal bilateral. "
                "Campimetria por confrontação: hemianopsia homônima esquerda com poupamento macular. "
                "Sem déficit motor ou afasia. RNM DWI: lesão isquêmica no lobo occipital direito."
            ),
        },
        "questions": [
            {
                "question": "Por que o paciente tem hemianopsia homônima e não perda monocular?",
                "answer": "A lesão é pós-quiasmática (lobo occipital) — afeta fibras de ambos os olhos provenientes do hemicampo esquerdo",
                "explanation": (
                    "Após o quiasma, as fibras de ambos os olhos que representam o mesmo hemicampo "
                    "viajam juntas no mesmo trato óptico → CGL → radiações → córtex. "
                    "Uma lesão occipital direita afeta fibras de OD-esquerda (nasal) e OE-esquerda (temporal) "
                    "simultaneamente → hemianopsia HOMÔNIMA esquerda (mesmo lado em ambos os olhos). "
                    "Perda monocular → lesão pré-quiasmática."
                ),
            },
            {
                "question": "Por que o poupamento macular ocorre em lesões corticais e não em lesões do trato?",
                "answer": "Duplo suprimento vascular do polo occipital (ACP + ramos da ACM)",
                "explanation": (
                    "A representação macular ocupa o polo occipital (~50% do córtex V1). "
                    "Essa região recebe colaterais da artéria cerebral média (ACM) além da ACP, "
                    "tornando-a resistente à isquemia quando a ACP é ocluída proximalmente. "
                    "No trato óptico ou CGL, as fibras maculares não têm proteção especial → sem poupamento. "
                    "Poupamento macular = assinatura de lesão cortical."
                ),
            },
            {
                "question": "Qual a conduta imediata e o risco de recorrência?",
                "answer": "AVC isquêmico — trombólise EV se < 4,5h ou trombectomia mecânica se indicada; anticoagulação para FA",
                "explanation": (
                    "Território da ACP é acessível à trombectomia mecânica (basilar, P1, P2). "
                    "A FA não anticoagulada é a causa mais provável — risco de recorrência de ~12%/ano sem tratamento. "
                    "Anticoagulação com NOAC (apixabana, rivaroxabana) reduz esse risco em 65%. "
                    "Reabilitação visual: prismas de Fresnel e treinamento de varredura ocular."
                ),
            },
        ],
        "teaching_point": (
            "Hemianopsia homônima de início súbito = AVC até prova em contrário. "
            "A ausência de DPAR distingue lesão pós-quiasmática (sem DPAR) de lesão do nervo óptico (com DPAR). "
            "Congruência dos defeitos (campos OD e OE idênticos) sugere lesão mais posterior (córtex). "
            "10% dos pacientes com AVC occipital desenvolvem síndrome de Anton: negação da cegueira."
        ),
    },
    {
        "id": "case_007",
        "title": "Glaucoma crônico descompensado com campo visual em tubo",
        "category": "Disco Óptico",
        "difficulty": 3,
        "related_structure": "disco_optico",
        "visual_field_structure": "disco_optico",
        "patient": {
            "age": 65,
            "sex": "M",
            "chief_complaint": "Glaucoma crônico em acompanhamento há 12 anos. Relata dificuldade crescente à noite e ao se locomover.",
            "history": (
                "Em uso de latanoprosta + timolol (combo) OD e OE. "
                "PIO média histórica: OD 22 mmHg, OE 20 mmHg (alvo < 18). "
                "Pai com glaucoma e perda visual severa."
            ),
            "examination": (
                "AV OD: 20/40. AV OE: 20/25. PIO OD: 24 mmHg, OE: 21 mmHg (com medicação). "
                "Fundoscopia: escavação óptica OD: 0,9 com entalhe inferotemporal do anel neurorretiniano. "
                "Escavação OE: 0,8 com palidez temporal. "
                "OCT RNFL: perda > 80% de fibras nervosas OD nos setores inferior e superior. "
                "Campimetria: campo tubular OD (apenas 5° centrais preservados). OE: escotoma arqueado inferior."
            ),
        },
        "questions": [
            {
                "question": "Como estadiar o glaucoma deste paciente e qual a implicação?",
                "answer": "OD: Glaucoma avançado (campo tubular, CD 0.9, RNFL >80% perdida). OE: Glaucoma moderado",
                "explanation": (
                    "Estadiamento pelo campo visual (Hodapp-Parrish-Anderson): "
                    "Inicial: MD > -6 dB. Moderado: MD entre -6 e -12 dB. Avançado: MD < -12 dB. "
                    "Campo tubular = perda de quase todo o campo periférico, apenas visão central remanescente. "
                    "A perda de fibras é irreversível — o objetivo agora é preservar o campo central (leitura, face)."
                ),
            },
            {
                "question": "O que o OCT de RNFL acrescenta ao campo visual?",
                "answer": "Detecção estrutural precoce — perda de RNFL precede defeito de campo em 5-6 anos",
                "explanation": (
                    "Estrutura precede função: o OCT detecta perda de fibras nervosas antes que o campo "
                    "visual automatizado mostre defeito reprodutível. A correlação estrutura-função "
                    "(RNFL thickness vs. sensibilidade campimétrica) é a base do monitoramento moderno. "
                    "Em doença avançada (como este caso), o campo visual torna-se mais informativo "
                    "pois o OCT entra em 'floor effect' (não há mais fibras para medir)."
                ),
            },
            {
                "question": "Qual a próxima etapa no manejo — cirúrgico ou clínico?",
                "answer": "Trabeculectomia ou dispositivo de drenagem (tubo) para atingir PIO alvo < 12 mmHg",
                "explanation": (
                    "Com PIO fora de alvo em máxima terapia medicamentosa e perda avançada, "
                    "cirurgia filtrante é o próximo passo. Trabeculectomia com mitomicina C: "
                    "reduz PIO ~40-50%, eficácia comprovada pelo AGIS. "
                    "Dispositivos de drenagem (Ahmed, Baerveldt) são alternativas. "
                    "Cirurgia não recupera o campo perdido — apenas retarda progressão."
                ),
            },
        ],
        "teaching_point": (
            "Glaucoma avançado com CD 0.9 e campo tubular representa o fracasso do acompanhamento adequado. "
            "A regra ISNT (inferior > superior > nasal > temporal) para o anel neurorretiniano: "
            "qualquer violação, especialmente entalhe inferotemporal, é sinal de alarme. "
            "O glaucoma é a principal causa de cegueira irreversível no mundo — "
            "detectável e tratável quando diagnosticado precocemente."
        ),
    },
    {
        "id": "case_008",
        "title": "Metamorfopsia progressiva e linha torta no teste de Amsler",
        "category": "Mácula",
        "difficulty": 1,
        "related_structure": "macula",
        "visual_field_structure": "macula",
        "patient": {
            "age": 78,
            "sex": "F",
            "chief_complaint": (
                "Percepção de linhas retas como tortas ou onduladas (metamorfopsia) no OD há 3 semanas. "
                "Dificuldade progressiva para ler e reconhecer rostos."
            ),
            "history": (
                "Tabagismo prévio (parou há 10 anos). Suplementação com vitaminas C, E, zinco. "
                "Irmã com diagnóstico de DMRI. DMRI seca OE há 3 anos."
            ),
            "examination": (
                "AV OD: 20/200 (era 20/40 há 6 meses). AV OE: 20/60. "
                "Fundoscopia OD: membrana neovascular sub-retiniana (MNVSR) com fluido sub-retiniano e "
                "hemorragia macular. Drusas moles confluentes bilaterais. "
                "OCT macular OD: hiperreflectividade sub-retiniana, fluido intrarretiniano e sub-retiniano. "
                "AngiOCT OD: neovascularização coroidal (NVC) tipo 2 (clássica)."
            ),
        },
        "questions": [
            {
                "question": "Qual a diferença entre DMRI seca e DMRI úmida e qual o risco de conversão?",
                "answer": "DMRI seca: atrofia geográfica progressiva lenta. DMRI úmida: neovascularização coroidal com perda rápida. Risco conversão ~10%/ano",
                "explanation": (
                    "DMRI seca (90% dos casos): acúmulo de drusas → atrofia geográfica progressiva → "
                    "perda gradual de décadas. DMRI úmida (10% dos casos, 90% da perda visual severa): "
                    "NVC perfura a membrana de Bruch → neovascularização → fluido, hemorragia → "
                    "cicatriz disciforme. Conversão de seca para úmida: risco maior com drusas moles grandes. "
                    "AREDS2: suplementação reduz progressão de DMRI seca para úmida em 25%."
                ),
            },
            {
                "question": "Qual o tratamento de primeira linha para a DMRI úmida?",
                "answer": "Injeções intravítreas de anti-VEGF (ranibizumabe, bevacizumabe, aflibercept, faricimabe)",
                "explanation": (
                    "Anti-VEGF neutraliza o VEGF-A, principal driver da neovascularização coroidal. "
                    "Protocolo de carga: 3 injeções mensais → manutenção (treat-and-extend ou PRN). "
                    "MARINA e ANCHOR trials: ranibizumabe mensal manteve ou melhorou AV em 90% dos casos. "
                    "Faricimabe (anti-VEGF + anti-Ang2): permite intervalos de até 16 semanas. "
                    "Início precoce (< 3 meses) = melhor prognóstico visual."
                ),
            },
            {
                "question": "Como monitorar a resposta ao tratamento e quando retratar?",
                "answer": "OCT macular seriado — critério de retratamento: fluido intrarretiniano ou sub-retiniano recorrente",
                "explanation": (
                    "OCT é o padrão-ouro para monitoramento. Sinais de atividade: fluido intrarretiniano "
                    "(melhor critério de retratamento), fluido sub-retiniano, aumento da MNVSR. "
                    "O paciente deve monitorar em casa com grade de Amsler: metamorfopsia nova ou piora = "
                    "consulta de urgência. AngiOCT dispensa o uso de contraste (fluoresceína) para "
                    "detectar atividade da NVC."
                ),
            },
        ],
        "teaching_point": (
            "DMRI é a principal causa de cegueira legal em > 50 anos nos países desenvolvidos. "
            "O diagnóstico precoce com OCT transformou o prognóstico — "
            "pacientes tratados antes de 3 meses têm AV final 2 linhas melhor que tratados tardios. "
            "O gene CFH (complemento) é o principal fator de risco genético. "
            "Tabagismo duplica o risco: é o principal fator de risco modificável."
        ),
    },
]


# ── Service ───────────────────────────────────────────────────────────────────

_CASES: list[ClinicalCase] = []


def _build_cases() -> list[ClinicalCase]:
    cases = []
    for raw in _CASES_RAW:
        cases.append(ClinicalCase(
            id=raw["id"],
            title=raw["title"],
            category=raw["category"],
            difficulty=raw["difficulty"],
            related_structure=raw["related_structure"],
            visual_field_structure=raw["visual_field_structure"],
            patient=CasePatient(**raw["patient"]),
            questions=[CaseQuestion(**q) for q in raw["questions"]],
            teaching_point=raw["teaching_point"],
        ))
    return cases


def list_cases() -> list[CaseListItem]:
    """Returns lightweight case list (no questions/patient details)."""
    global _CASES
    if not _CASES:
        _CASES = _build_cases()
    return [
        CaseListItem(
            id=c.id,
            title=c.title,
            category=c.category,
            difficulty=c.difficulty,
            related_structure=c.related_structure,
        )
        for c in _CASES
    ]


def get_case(case_id: str) -> ClinicalCase | None:
    """Returns a full case by ID."""
    global _CASES
    if not _CASES:
        _CASES = _build_cases()
    for case in _CASES:
        if case.id == case_id:
            return case
    return None
