# Costruzione di Knowledge Graph in ambito culturale: strumenti e applicazioni a confronto

**Tesi di Laurea Triennale** — Università degli Studi di Torino, Corso di Laurea in Informatica  
**Candidato**: Antonio Salvatore | **Relatore**: prof.ssa Rossana Damiano | **Correlatore**: prof. Marco Antonio Stranisci  
**Anno Accademico**: 2025/2026

Progetto di tesi per la costruzione di un Knowledge Graph semantico a partire dai dati del Museo Nazionale dell'Automobile di Torino (MAUTO), tramite entity linking automatico su Wikidata, dual mapping Schema.org, e sperimentazione comparativa con modelli linguistici (LLM) per l'estrazione di informazioni strutturate da testi descrittivi.

## Obiettivi

- Trasformazione del dataset CSV del MAUTO (163 veicoli, 29 colonne) in un Knowledge Graph RDF
- Entity linking automatico verso Wikidata con validazione ontologica whitelist-only (P31)
- Dual mapping Wikidata (LOD) + Schema.org (Web) per massima interoperabilità
- Architettura dichiarativa con logica centralizzata in `museum_mappings.py`
- Sperimentazione comparativa tra strategie di prompting (Zeroshot / Oneshot) su modelli LLM per l'estrazione di entità da testi narrativi

## Risultati principali

### Knowledge Graph finale (v2.0)
- **163 veicoli** processati, 100% con IRI univoco
- **5.931 triple RDF** uniche (`output/output_automatic_enriched_v2.nt`)
- **105 entità Wikidata** univoche referenziate → **749 triple** con oggetto IRI esterno
- **51 predicati distinti** (22 Schema.org + 17 Wikidata nativi)
- **0 falsi positivi** su 293 entità collegate (validazione whitelist P31)
- Evoluzione: v1.0 (1.579 triple) → v1.4 (3.332) → v1.5 (5.331) → **v2.0 (5.931)**

### Esperimento LLM (estrazione entità da testi narrativi)
- **Modello**: Qwen3-0.6B e Qwen3-1.7B su 99 record con testo descrittivo
- **Configurazioni**: 3 versioni × 2 modalità (Zeroshot / Oneshot) + confronto scaling (V4)
- **Miglior success rate**: V2 Zeroshot = **85.9%** (output prefix + greedy decoding)
- **Miglior copertura media**: V1 Oneshot = **90.8%** (SR 73.7%, quasi tutti i campi valorizzati)
- **Finding principale**: il design del prompt supera la dimensione del modello — V2 ZS 0.6B (85.9%) batte tutte le configurazioni del modello 1.7B

## Quick Start

### Prerequisiti
```bash
python -m venv .venv
.venv\Scripts\activate
pip install pandas>=1.3.0 rdflib>=6.0.0 requests
```

### Generazione del Knowledge Graph
```bash
python scripts/integrated_semantic_enricher.py
# Output: output/output_automatic_enriched_v2.nt
```

### Esperimento LLM
```bash
pip install torch transformers accelerate pyyaml

# Zeroshot
python llm_test/zeroshot/run_experiment.py

# Oneshot
python llm_test/oneshot/run_experiment.py
```

## Struttura del progetto

```
├── data/
│   ├── museo.csv                        # Dataset originale (163 veicoli, 29 colonne)
│   ├── museum_column_mapping.csv        # Mappings colonne → predicati ontologici
│   └── wikidata_ontology_config.json    # Whitelist P31 per validazione ontologica
├── scripts/
│   ├── integrated_semantic_enricher.py  # Orchestratore pipeline CSV → RDF
│   ├── robust_wikidata_linker.py        # Entity linking + scoring multi-livello
│   ├── museum_mappings.py               # Hub dichiarativo (logica centralizzata)
│   └── extract_wikidata_attributes.py   # Analisi output e statistiche
├── llm_test/
│   ├── zeroshot/                        # Configurazioni e risultati Zeroshot (V1–V4)
│   └── oneshot/                         # Configurazioni e risultati Oneshot (V1–V4)
├── caches/
│   └── production_cache_entities.json   # Cache persistente entità Wikidata
├── output/
│   └── output_automatic_enriched_v2.nt  # Knowledge Graph finale (5.931 triple)
└── old/                                 # Versioni storiche archiviate
```

## Tecnologie

- **Python 3.x** con `pandas` e `rdflib`
- **Wikidata** — entity linking tramite API `wbsearchentities`
- **Schema.org** — ontologia standard per il web semantico
- **RDF / N-Triples** — formato di serializzazione del grafo
- **Hugging Face Transformers** — inferenza LLM (Qwen3-0.6B, Qwen3-1.7B)

## Licenza

MIT
