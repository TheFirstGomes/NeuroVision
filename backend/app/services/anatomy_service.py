"""
Anatomy service: returns structured data about neuro-ophthalmic structures.
Used by the 3D viewer to populate info panels on click.
"""
from app.domain.models import AnatomyStructure, AnatomyResponse

ANATOMY_DATA: dict[str, AnatomyStructure] = {
    "cornea": AnatomyStructure(
        id="cornea",
        name="Córnea",
        description=(
            "Tecido transparente avascular que cobre a parte anterior do olho. "
            "Responsável por aproximadamente 2/3 do poder refrativo total do olho. "
            "Possui cinco camadas: epitélio, camada de Bowman, estroma, membrana de Descemet e endotélio."
        ),
        neurological_connections=["Nervo trigêmeo (V1 — ramo oftálmico)", "Reflexo córneo-palpebral"],
        associated_pathologies=[
            "Ceratocone",
            "Úlcera de córnea",
            "Ceratite herpética (HSV)",
            "Distrofias corneanas",
            "Anestesia corneana (lesão do V par)",
        ],
        clinical_relevance=(
            "A córnea é o tecido mais densamente inervado do corpo — fibras do nervo trigêmeo (V1). "
            "Anestesia corneana indica lesão do ramo oftálmico do trigêmeo ou nervo ciliar longo. "
            "O reflexo córneo-palpebral testa a integridade dos pares V e VII."
        ),
    ),
    "retina": AnatomyStructure(
        id="retina",
        name="Retina",
        description=(
            "Tecido neural que reveste a parte interna do olho. "
            "É uma extensão direta do sistema nervoso central e contém "
            "fotorreceptores (cones e bastonetes), células bipolares e células ganglionares. "
            "Os axônios das células ganglionares formam o nervo óptico."
        ),
        neurological_connections=["Nervo óptico", "Corpo geniculado lateral", "Córtex visual V1"],
        associated_pathologies=[
            "Retinopatia diabética",
            "Degeneração macular relacionada à idade (DMRI)",
            "Oclusão de artéria/veia retiniana",
            "Descolamento de retina",
        ],
        clinical_relevance=(
            "A retina é a única parte do SNC visível sem cirurgia. "
            "Mudanças na microvasculatura retiniana refletem doenças sistêmicas "
            "como diabetes, hipertensão e aterosclerose."
        ),
    ),
    "nervo_optico": AnatomyStructure(
        id="nervo_optico",
        name="Nervo Óptico (II Par Craniano)",
        description=(
            "Feixe de ~1,2 milhão de axônios de células ganglionares da retina. "
            "Possui bainha de mielina produzida por oligodendrócitos — como outros neurônios do SNC. "
            "Percorre 4 segmentos: intraocular, intraorbitário, intracanalicular e intracraniano."
        ),
        neurological_connections=["Retina", "Quiasma óptico", "Trato óptico"],
        associated_pathologies=[
            "Neurite óptica (Esclerose Múltipla)",
            "Neuropatia óptica isquêmica (NOIA)",
            "Glaucoma",
            "Papiledema",
            "Meningioma da bainha do nervo óptico",
        ],
        clinical_relevance=(
            "Não se regenera após lesão. Dano ao nervo óptico causa perda visual irreversível. "
            "É o alvo principal em glaucoma e doenças desmielinizantes como a Esclerose Múltipla."
        ),
    ),
    "quiasma_optico": AnatomyStructure(
        id="quiasma_optico",
        name="Quiasma Óptico",
        description=(
            "Ponto de cruzamento (decussação) das fibras nervosas nasais de cada retina. "
            "Localiza-se na sela túrcica, acima da hipófise. "
            "As fibras temporais não cruzam — seguem ipsilaterais."
        ),
        neurological_connections=["Nervo óptico", "Trato óptico", "Hipófise"],
        associated_pathologies=[
            "Adenoma hipofisário (hemianopsia bitemporal)",
            "Craniofaringioma",
            "Meningioma paraselar",
            "Glioma do quiasma",
        ],
        clinical_relevance=(
            "Lesão do quiasma causa hemianopsia bitemporal — perda dos campos visuais temporais bilaterais. "
            "Sinal clássico de compressão por adenoma hipofisário. "
            "Relação anatômica com a hipófise torna este ponto crítico em neuroendocrinologia."
        ),
    ),
    "trato_optico": AnatomyStructure(
        id="trato_optico",
        name="Trato Óptico",
        description=(
            "Via retroquiasmática que conecta o quiasma óptico ao corpo geniculado lateral. "
            "Transporta informação visual do hemicampo visual contralateral."
        ),
        neurological_connections=["Quiasma óptico", "Corpo geniculado lateral", "Colículo superior"],
        associated_pathologies=[
            "Hemianopsia homônima incongruente",
            "Tumores do lobo temporal",
        ],
        clinical_relevance=(
            "Lesão do trato óptico causa hemianopsia homônima contralateral incongruente. "
            "A incongruência (campos visuais assimétricos) é característica de lesões anteriores "
            "na via retroquiasmática."
        ),
    ),
    "corpo_geniculado_lateral": AnatomyStructure(
        id="corpo_geniculado_lateral",
        name="Corpo Geniculado Lateral (CGL)",
        description=(
            "Estação de retransmissão talâmica da via visual. "
            "Recebe projeções do trato óptico e projeta para o córtex visual primário via radiações ópticas. "
            "Possui 6 camadas com organização retinotópica precisa."
        ),
        neurological_connections=["Trato óptico", "Radiações ópticas", "Tálamo"],
        associated_pathologies=[
            "Lesões talâmicas vasculares",
            "Hemianopsia homônima com poupamento macular",
        ],
        clinical_relevance=(
            "Lesão isolada do CGL é rara. Geralmente afetado em AVCs talâmicos. "
            "Causa hemianopsia homônima com padrão típico 'em cunha' no campo visual."
        ),
    ),
    "radiacoes_opticas": AnatomyStructure(
        id="radiacoes_opticas",
        name="Radiações Ópticas",
        description=(
            "Fibras que conectam o CGL ao córtex visual primário. "
            "Alça de Meyer (temporal): fibras inferiores que representam campo superior. "
            "Alça parietal: fibras superiores que representam campo inferior."
        ),
        neurological_connections=["Corpo geniculado lateral", "Córtex visual V1", "Lobo temporal", "Lobo parietal"],
        associated_pathologies=[
            "Quadrantanopsia superior homônima (lesão temporal — 'pie in the sky')",
            "Quadrantanopsia inferior homônima (lesão parietal)",
        ],
        clinical_relevance=(
            "A alça de Meyer passa pelo lobo temporal anterior — ressecção temporal (epilepsia) "
            "pode causar quadrantanopsia superior homônima. "
            "Localização da lesão pode ser deduzida pelo padrão de perda visual."
        ),
    ),
    "cortex_visual": AnatomyStructure(
        id="cortex_visual",
        name="Córtex Visual Primário (V1 / Área 17)",
        description=(
            "Localiza-se no lobo occipital, ao redor do sulco calcarino. "
            "Recebe e processa informação visual com organização retinotópica precisa. "
            "O campo visual central tem representação cortical desproporcional (magnificação central)."
        ),
        neurological_connections=["Radiações ópticas", "V2/V3/V4/V5 (áreas de associação visual)"],
        associated_pathologies=[
            "AVC da artéria cerebral posterior (hemianopsia homônima com poupamento macular)",
            "Migrânea com aura visual",
            "Escotoma central por lesão occipital",
        ],
        clinical_relevance=(
            "AVC occipital é a causa mais comum de hemianopsia homônima adquirida em adultos. "
            "Poupamento macular (visão central preservada) é característico de lesões occipitais "
            "devido à dupla irrigação da área macular representada no córtex."
        ),
    ),
    "disco_optico": AnatomyStructure(
        id="disco_optico",
        name="Disco Óptico (Papila)",
        description=(
            "Ponto de saída do nervo óptico. Visível ao fundo de olho como área oval de cor alaranjada. "
            "Não contém fotorreceptores — corresponde ao ponto cego fisiológico. "
            "A escavação central (cup) e a relação cup/disc são parâmetros diagnósticos importantes."
        ),
        neurological_connections=["Nervo óptico", "Espaço subaracnóideo intracraniano"],
        associated_pathologies=[
            "Papiledema (edema por hipertensão intracraniana)",
            "Glaucoma (escavação aumentada)",
            "Papilite (inflamação — neurite óptica anterior)",
            "Pseudopapiledema (drusas do disco)",
        ],
        clinical_relevance=(
            "O disco óptico reflete a pressão intracraniana — papiledema bilateral indica HIC. "
            "A relação cup/disc é o principal parâmetro de monitoramento do glaucoma. "
            "Shunt optociliar no disco sugere meningioma da bainha do nervo óptico."
        ),
    ),
    "macula": AnatomyStructure(
        id="macula",
        name="Mácula / Fóvea",
        description=(
            "Região central da retina responsável pela visão de alta resolução e cores. "
            "A fóvea, centro da mácula, tem a maior densidade de cones e zero bastonetes. "
            "Diâmetro da mácula: ~5.5mm. Fóvea: ~1.5mm."
        ),
        neurological_connections=["Córtex visual occipital (representação ampliada)", "Via ventral V4 (cor/forma)"],
        associated_pathologies=[
            "DMRI (Degeneração Macular Relacionada à Idade)",
            "Edema macular diabético",
            "Buraco macular",
            "Membrana epirretiniana",
        ],
        clinical_relevance=(
            "Lesão macular causa escotoma central — perda da visão de leitura e reconhecimento facial. "
            "A mácula tem representação amplificada no córtex visual — 'magnificação cortical central'. "
            "OCT é o exame padrão-ouro para avaliação da morfologia macular."
        ),
    ),
}


def get_anatomy_structure(structure_id: str) -> AnatomyResponse | None:
    """
    Returns anatomical structure data for the 3D viewer.
    Returns None if structure not found.
    """
    structure = ANATOMY_DATA.get(structure_id.lower())
    if not structure:
        return None

    colors = {
        "cornea": "#a8d8ea",
        "retina": "#ff6b6b",
        "nervo_optico": "#4ecdc4",
        "quiasma_optico": "#ffe66d",
        "trato_optico": "#a8e6cf",
        "corpo_geniculado_lateral": "#ff8b94",
        "radiacoes_opticas": "#dda0dd",
        "cortex_visual": "#98ddca",
        "disco_optico": "#f7dc6f",
        "macula": "#f0a500",
    }

    return AnatomyResponse(
        structure=structure,
        highlight_color=colors.get(structure_id.lower(), "#00ff88"),
    )


def list_structures() -> list[dict]:
    """Returns all available structure IDs and names."""
    return [
        {"id": k, "name": v.name}
        for k, v in ANATOMY_DATA.items()
    ]
