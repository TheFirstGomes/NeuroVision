"""
Neuro-ophthalmology knowledge base.
Structured literature content seeded into the RAG pipeline.
All content is based on peer-reviewed medical literature.
"""
from langchain.schema import Document


def get_knowledge_documents() -> list[Document]:
    """
    Returns structured neuro-ophthalmology knowledge as LangChain Documents.
    Sources: IMO, PubMed, Lancet Neurology, Walsh & Hoyt Clinical Neuro-Ophthalmology.
    """
    entries = [
        # ── ANATOMIA DO SISTEMA VISUAL ────────────────────────────────────────
        {
            "content": """
            O sistema visual humano começa na retina, que é tecnicamente uma extensão do sistema nervoso central (SNC).
            A retina contém neurônios fotorreceptores (bastonetes e cones) que convertem luz em sinais elétricos.
            O nervo óptico (II par craniano) transmite esses sinais ao cérebro.
            O quiasma óptico é o ponto de cruzamento das fibras nasais de cada olho.
            Após o quiasma, as fibras seguem pelos tratos ópticos até o corpo geniculado lateral (CGL) no tálamo.
            Do CGL, as radiações ópticas levam o sinal ao córtex visual primário (V1) no lobo occipital (área de Brodmann 17).
            Lesões em qualquer ponto desta via causam déficits visuais específicos e diagnosticamente úteis.
            """,
            "source": "Anatomia do Sistema Visual - Walsh & Hoyt",
            "topic": "anatomia",
            "structure": "via_visual_completa",
        },
        {
            "content": """
            A retina é a única parte do SNC visível sem cirurgia.
            Ela contém: fotorreceptores (cones e bastonetes), células bipolares, células ganglionares.
            Os axônios das células ganglionares formam o nervo óptico.
            A mácula é responsável pela visão central de alta resolução; contém principalmente cones.
            A fóvea, centro da mácula, tem a maior densidade de cones e zero bastonetes.
            O disco óptico (papila) é o ponto de saída do nervo óptico — não tem fotorreceptores (ponto cego).
            Doenças sistêmicas como diabetes e hipertensão afetam primeiramente a microvasculatura retiniana.
            """,
            "source": "Fundamentos de Neuro-Oftalmologia - IMO 2021",
            "topic": "anatomia",
            "structure": "retina",
        },
        {
            "content": """
            O nervo óptico tem 4 segmentos: intraocular (1mm), intraorbitário (25mm), intracanalicular (9mm) e intracraniano (10mm).
            É envolvido por bainha de mielina produzida por oligodendrócitos (como outros neurônios do SNC).
            Isso o diferencia dos nervos periféricos — lesão desmielinizante como na esclerose múltipla afeta diretamente o nervo óptico.
            O nervo óptico é circundado pelo espaço subaracnóideo, conectado ao espaço intracraniano.
            Por isso, aumento da pressão intracraniana causa papiledema (edema do disco óptico).
            O nervo óptico não se regenera após lesão — dano permanente é irreversível.
            """,
            "source": "Neuroftalmologia Clínica - IMO 2021",
            "topic": "anatomia",
            "structure": "nervo_optico",
        },
        {
            "content": """
            O quiasma óptico localiza-se na sela túrcica, acima da hipófise.
            Nele ocorre o cruzamento (decussação) das fibras da retina nasal (campo visual temporal).
            As fibras temporais não cruzam — seguem ipsilaterais.
            Lesão no quiasma causa hemianopsia bitemporal (perda do campo visual temporal bilateral).
            Isso é o sinal clássico de compressão por adenoma hipofisário.
            A posição do quiasma varia: pode ser pré-fixado ou pós-fixado, alterando o padrão de déficit visual com lesões hipofisárias.
            """,
            "source": "Neuroftalmologia Clínica - IMO 2021",
            "topic": "anatomia",
            "structure": "quiasma_optico",
        },
        {
            "content": """
            O córtex visual primário (V1 ou área 17 de Brodmann) localiza-se no lobo occipital, ao redor do sulco calcarino.
            Recebe projeções do corpo geniculado lateral via radiações ópticas.
            A representação topográfica (retinotopia) é preservada: o campo visual central ocupa maior área cortical.
            Lesão de V1 causa escotoma ou hemianopsia homônima contralateral.
            V2, V3, V4, V5/MT processam forma, cor, profundidade e movimento respectivamente.
            AVC occipital é a causa mais comum de hemianopsia homônima adquirida em adultos.
            """,
            "source": "Princípios de Neurologia - Adams & Victor",
            "topic": "anatomia",
            "structure": "cortex_visual",
        },

        # ── PATOLOGIAS NEURO-OFTALMOLÓGICAS ──────────────────────────────────
        {
            "content": """
            Neurite óptica é a inflamação do nervo óptico.
            Apresentação clássica: perda visual unilateral subaguda, dor à movimentação ocular, defeito pupilar aferente relativo (DPAR).
            Em 25% dos casos é a manifestação inicial de esclerose múltipla (EM).
            Após neurite óptica, o risco de EM em 15 anos é de 50% se houver lesões na RM.
            O Optic Neuritis Treatment Trial (ONTT) demonstrou que corticoterapia IV acelera recuperação mas não muda prognóstico final.
            A OCT mostra afinamento da camada de fibras nervosas da retina (CFNR) como marcador de dano axonal.
            """,
            "source": "ONTT Study / Lancet Neurology 2008",
            "topic": "patologia",
            "structure": "nervo_optico",
        },
        {
            "content": """
            Papiledema é o edema bilateral do disco óptico por hipertensão intracraniana (HIC).
            Causas de HIC: tumor cerebral, hidrocefalia, trombose de seio venoso, hipertensão intracraniana idiopática (pseudotumor cerebri).
            Sintomas: cefaleia, náuseas, visão turva, diplopia por paralisia do VI nervo craniano.
            Fundo de olho: disco hiperêmico, bordas apagadas, ausência de pulso venoso espontâneo.
            Diagnóstico: RM + punção lombar com medida da pressão de abertura.
            Papiledema crônico leva a perda visual permanente por atrofia óptica secundária.
            Diferenciar de pseudopapiledema (drusas do disco) e papilite (inflamação unilateral).
            """,
            "source": "Fundamentos de Neuro-Oftalmologia - IMO 2021",
            "topic": "patologia",
            "structure": "disco_optico",
        },
        {
            "content": """
            Neuropatia óptica isquêmica anterior (NOIA) é a causa mais comum de perda visual aguda em maiores de 50 anos.
            NOIA não-arterítica (NOIA-NA): associada a disco de risco (cup/disc ratio pequeno), HAS, DM, apneia do sono.
            NOIA arterítica (NOIA-A): causada por arterite de células gigantes (Horton) — emergência médica.
            NOIA-A: eritrossedimentação elevada, PCR alta, claudicação de mandíbula, cefaleia temporal.
            Tratamento NOIA-A: corticoterapia IV imediata para prevenir perda do segundo olho.
            Biópsia da artéria temporal confirma diagnóstico de arterite de Horton.
            """,
            "source": "Neuroftalmologia Clínica - IMO 2021",
            "topic": "patologia",
            "structure": "nervo_optico",
        },
        {
            "content": """
            Glaucoma é a principal causa de cegueira irreversível mundial.
            É uma neuropatia óptica progressiva com perda característica de células ganglionares da retina.
            O dano ocorre primariamente no nervo óptico e na camada de fibras nervosas da retina (CFNR).
            Fator de risco principal: pressão intraocular (PIO) elevada — mas glaucoma normotensivo existe.
            Campo visual: perda em arcada (escotoma de Bjerrum), degrau nasal, perda tubular avançada.
            OCT: essencial para detecção precoce de afinamento da CFNR antes da perda de campo visual.
            Conexão neurológica: genes do glaucoma (OPTN, TBK1) envolvidos em neuroinflamação.
            """,
            "source": "European Glaucoma Society Guidelines 2020",
            "topic": "patologia",
            "structure": "nervo_optico",
        },
        {
            "content": """
            Retinopatia diabética é a manifestação ocular da neuropatia diabética sistêmica.
            Fisiopatologia: hiperglicemia crônica → dano à microvasculatura retiniana → isquemia → neovascularização.
            Classificação: não-proliferativa (leve, moderada, grave) e proliferativa.
            Edema macular diabético (EMD) é a principal causa de perda visual na RD.
            Neuropatia óptica diabética: ocorre independentemente da RD; causa afinamento da CFNR.
            Tratamento: controle glicêmico, injeções intravítreas de anti-VEGF, fotocoagulação, cirurgia.
            Rastreamento: todo diabético deve ter exame de fundo de olho anual.
            """,
            "source": "ETDRS / Diabetic Retinopathy Clinical Research Network",
            "topic": "patologia",
            "structure": "retina",
        },
        {
            "content": """
            Degeneração macular relacionada à idade (DMRI) afeta a mácula e é a principal causa de cegueira em > 65 anos.
            DMRI seca (atrófica): acúmulo de drusas subretinianas, atrofia geográfica progressiva. Sem tratamento eficaz.
            DMRI úmida (exsudativa/neovascular): neovascularização coroidal → hemorragia → perda visual súbita.
            Anti-VEGF (ranibizumab, bevacizumab, aflibercept) revolucionaram tratamento da DMRI úmida.
            OCT é exame essencial para diagnóstico e monitoramento de DMRI.
            Fatores de risco: tabagismo, história familiar, idade, luz solar intensa.
            Pesquisas recentes ligam DMRI a mecanismos neuroinflamatórios similares ao Alzheimer.
            """,
            "source": "Age-Related Eye Disease Study (AREDS2)",
            "topic": "patologia",
            "structure": "macula",
        },

        # ── SÍNDROMES NEURO-OFTALMOLÓGICAS ────────────────────────────────────
        {
            "content": """
            Síndrome de Horner: ptose, miose, anidrose ipsilateral.
            Causada por interrupção da via simpática oculossimpática (3 neurônios).
            1° neurônio: hipotálamo → medula cervical (lesão: AVC, tumor de tronco)
            2° neurônio: medula → gânglio cervical superior (lesão: tumor de Pancoast, dissecção carotídea)
            3° neurônio: gânglio → olho (lesão: dissecção da artéria carótida interna, síndrome da artéria carótida)
            Teste farmacológico: cocaína 4% confirma Horner; hidroxianfetamina localiza o neurônio afetado.
            Horner doloroso = emergência: descartar dissecção carotídea.
            """,
            "source": "Neuroftalmologia Clínica - IMO 2021",
            "topic": "sindrome",
            "structure": "via_simpatica",
        },
        {
            "content": """
            Paralisia do III nervo craniano (oculomotor): ptose, midríase, olho em posição 'down and out'.
            Causa compressiva (aneurisma de comunicante posterior): midríase presente — EMERGÊNCIA.
            Causa isquêmica (diabética, hipertensiva): midríase ausente (poupamento pupilar).
            Regra clínica: III nervo com comprometimento pupilar = angiografia/angio-TC para descartar aneurisma.
            III nervo isquêmico resolve em 3 meses; compressivo requer intervenção neurocirúrgica.
            """,
            "source": "Princípios de Neurologia - Adams & Victor",
            "topic": "sindrome",
            "structure": "nervo_oculomotor",
        },
        {
            "content": """
            Hemianopsia homônima: perda de metade do campo visual no mesmo lado em ambos os olhos.
            Causas por localização:
            - Trato óptico: hemianopsia incongruente (lesão retroquiasmática anterior)
            - Radiações ópticas temporais: quadrantanopsia superior homônima (lesão temporal — 'pie in the sky')
            - Radiações ópticas parietais: quadrantanopsia inferior homônima
            - Córtex occipital: hemianopsia congruente com poupamento macular (AVC occipital)
            A congruência aumenta quanto mais posterior for a lesão.
            Causa mais comum em adultos: AVC da artéria cerebral posterior.
            """,
            "source": "Neuroftalmologia Clínica - IMO 2021",
            "topic": "sindrome",
            "structure": "via_visual_completa",
        },
        {
            "content": """
            Nistagmo: movimento ocular rítmico e involuntário.
            Nistagmo pendular: velocidades iguais nas duas fases — geralmente congênito ou desmielinização.
            Nistagmo em ressalto (jerk nystagmus): fase lenta e fase rápida.
            Nistagmo horizontal: lesão de tronco encefálico ou cerebelo.
            Nistagmo vertical para baixo (downbeat): lesão de junção craniovertebral (Chiari, esclerose múltipla).
            Nistagmo vertical para cima (upbeat): lesão de tronco encefálico inferior.
            Nistagmo de convergência-retração: lesão de mesencéfalo dorsal (síndrome de Parinaud).
            Síndrome de Parinaud: paralisia do olhar para cima, nistagmo de convergência, dissociação luz-perto.
            """,
            "source": "Princípios de Neurologia - Adams & Victor",
            "topic": "sindrome",
            "structure": "tronco_encefalico",
        },

        # ── EXAMES DIAGNÓSTICOS ────────────────────────────────────────────────
        {
            "content": """
            Tomografia de coerência óptica (OCT): exame não invasivo de alta resolução da retina e nervo óptico.
            Mede espessura da camada de fibras nervosas da retina (CFNR) — marcador de dano axonal.
            OCT-A (angiografia): visualiza circulação retiniana sem contraste.
            Aplicações: glaucoma, DMRI, edema macular, neurite óptica, papiledema.
            Na neurite óptica e EM: afinamento da CFNR correlaciona com déficit visual e cognitivo.
            OCT tornou-se biomarcador de neurodegeneração — estudos correlacionam CFNR com Alzheimer e Parkinson.
            """,
            "source": "Journal of Neuro-Ophthalmology 2020",
            "topic": "diagnostico",
            "structure": "retina",
        },
        {
            "content": """
            Campimetria (campo visual): mapa quantitativo da função visual por localização.
            Perimetria automatizada (Humphrey): padrão-ouro para glaucoma e doenças neurológicas.
            Padrões típicos:
            - Glaucoma: escotoma arqueado, degrau nasal, perda em ilha central
            - Neuropatia óptica: defeito altitudinal (NOIA), escotoma central (neurite óptica)
            - Quiasma: hemianopsia bitemporal (adenoma hipofisário)
            - Trato óptico/córtex: hemianopsia homônima
            Frequência de duplicação (FDT): detecta perda precoce de células ganglionares.
            """,
            "source": "Fundamentos de Neuro-Oftalmologia - IMO 2021",
            "topic": "diagnostico",
            "structure": "via_visual_completa",
        },
        {
            "content": """
            Potencial evocado visual (PEV): avalia integridade da via visual do olho ao córtex occipital.
            Latência da onda P100: retardo indica desmielinização (neurite óptica, esclerose múltipla).
            Amplitude: redução indica perda axonal.
            PEV é objetivo — não depende da cooperação do paciente (útil em crianças e simuladores).
            Pode detectar neurite óptica subclínica (olho aparentemente normal com latência aumentada).
            Indicações: suspeita de EM, neurite óptica, ambliopia, avaliação de nervo óptico.
            """,
            "source": "Neuroftalmologia Clínica - IMO 2021",
            "topic": "diagnostico",
            "structure": "nervo_optico",
        },

        # ── ESCLEROSE MÚLTIPLA E OLHO ─────────────────────────────────────────
        {
            "content": """
            Esclerose múltipla (EM) e olho: manifestações oftalmológicas são frequentes e diagnósticamente importantes.
            Neurite óptica: manifestação inicial em 20-25% dos casos de EM.
            Oftalmoplegia internuclear (OIN): lesão do fascículo longitudinal medial — clássica da EM em adultos jovens.
            OIN: exotropia, incapacidade de adução no olho ipsilateral, nistagmo no olho abduzido.
            Nistagmo: múltiplos tipos possíveis na EM.
            OCT da CFNR: biomarcador de progressão da EM — correlaciona com volume cerebral e cognição.
            Uveíte: ocorre em ~1% dos pacientes com EM.
            """,
            "source": "Multiple Sclerosis Journal 2019 / Lancet Neurology",
            "topic": "patologia",
            "structure": "nervo_optico",
        },

        # ── TUMORES E COMPRESSÃO ──────────────────────────────────────────────
        {
            "content": """
            Adenoma hipofisário: tumor mais comum a comprimir o quiasma óptico.
            Apresentação ocular: hemianopsia bitemporal (perda dos campos temporais bilaterais).
            Campo visual começa a falhar nos quadrantes superiores temporais.
            Macroadenoma: > 10mm, causa compressão por efeito de massa.
            Apoplexia hipofisária: hemorragia/infarto súbito do adenoma — emergência com perda visual aguda.
            Tratamento: cirurgia transesfenoidal, radioterapia, agonistas dopaminérgicos (prolactinoma).
            Monitoramento pós-tratamento: campimetria e OCT seriados.
            """,
            "source": "Neuroftalmologia Clínica - IMO 2021",
            "topic": "patologia",
            "structure": "quiasma_optico",
        },
        {
            "content": """
            Meningioma da bainha do nervo óptico: tumor benigno que envolve o nervo óptico.
            Tríade clássica: perda visual progressiva, atrofia óptica, shunt optociliar (vasos colaterais no disco).
            Mais comum em mulheres de meia-idade.
            RM com gadolínio: sinal em 'trilho de trem' (realce ao redor do nervo).
            Tratamento: radioterapia estereotáxica fracionada é primeira linha.
            Cirurgia reservada para casos selecionados (risco de cegueira).
            """,
            "source": "Journal of Neuro-Ophthalmology 2018",
            "topic": "patologia",
            "structure": "nervo_optico",
        },
    ]

    documents = []
    for entry in entries:
        doc = Document(
            page_content=entry["content"].strip(),
            metadata={
                "source": entry["source"],
                "topic": entry["topic"],
                "structure": entry["structure"],
            },
        )
        documents.append(doc)

    return documents
