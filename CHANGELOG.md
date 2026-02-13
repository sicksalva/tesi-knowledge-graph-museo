# Changelog

## [2.0.0] - 2026-02-12 - Sistema Production-Ready con Validazione Ontologica

### 🎯 Major Refactoring: CSV-to-RDF Architecture

#### Added
- **museum_mappings.py**: Hub centralizzato per tutta la logica di business
  - 27 mappings Wikidata properties
  - 90+ regole literal-only properties
  - 15+ regole IRI-target properties
  - Entity type mappings per validazione
  - Helper functions: is_year_value(), is_donation(), is_long_description()
- **Validazione ontologica P31 (instance of)**: Sistema pre-scoring validation
  - Set incompatible types: Q215380 (music band), Q482994 (album), Q7366 (song), etc.
  - Validazione tipi attesi per predicato (es. Q786820 per manufacturer)
  - Regole speciali per acronimi corti (≤3 caratteri)
- **Doppia interoperabilità**: Supporto simultaneo Wikidata + Schema.org
  - HTTPS enforcement per tutti i predicati Schema.org
  - 27 properties Wikidata + 44 properties Schema.org
- **Gestione donazioni speciale**: P1028 (donated by) + schema:sponsor
- **Cache management migliorato**: Spostata in caches/ directory

#### Changed
- **integrated_semantic_enricher.py**: Refactored da RDF-processor a CSV-generator
  - Lettura diretta da museo.csv (header riga 2)
  - Caricamento mappings da museum_column_mapping.csv
  - Integrazione mappings Schema.org da mappings.csv
  - Generazione RDF da zero invece di post-processing
- **robust_wikidata_linker.py**: Validazione ontologica integrata
  - Metodo _validate_ontology() PRIMA del calcolo score
  - Confidence threshold aumentato: 0.4 → 0.6
- **Strategia custom IRI**: Rimossi completamente (design choice)
  - Solo vehicle URIs mantengono IRI personalizzati
  - Valori tecnici sempre literal (potenza, velocità, cilindrata)
  - Brand senza match Wikidata → literal invece di custom IRI

#### Fixed
- **Q1789258 False Positive**: Music band "OM" erroneamente linkato come manufacturer
  - Root cause: Nessuna validazione P31 prima del linking
  - Fix: Validazione ontologica rigorosa implementata
  - Risultato: Q1789258 rejected, "OM" mantenuto come literal
- **Variable scope bug**: label usato prima della definizione in _validate_ontology()


#### Metriche Finali
- **5,162 triple** generate (1,798 literals + 1,566 IRIs)
- **160 veicoli** processati (97.5% completezza)
- **293 entità Wikidata** linkate (0 false positives)
- **79 entries** in cache persistente

### 🧪 Test LLM Framework (Fase 10 - 2026-02-05)

#### Added
- **Framework comparativo oneshot vs zeroshot**
  - Directory structure: zeroshot/, oneshot/, compare_modes.py
  - Test su 99 veicoli del dataset museo
- **Configurazione GPU ottimizzata**
  - Modello: Qwen/Qwen3-0.6B (600M parametri)
  - Hardware: NVIDIA RTX 4050 Laptop (6.44 GB)
  - FP16 precision, temperature 0.2, max_tokens 300
- **Debug framework progressivo**
  - Timing dettagliato per tokenization/generation/decode
  - Memory tracking GPU
  - ETA calculation per batch processing
- **Config YAML modulare**
  - Parametri modello commentati
  - System/user prompts separati
  - Example input/output per oneshot

#### Results
- **Oneshot**: 65/99 successi (65.7%)
- **Zeroshot**: 6/99 successi (6.1%)
- **Improvement**: +59.6% con esempi di guida
- **Best entities** (oneshot): MARCA, PAESE, DESIGNER (>60%)
- **Worst entities**: PILOTA, GARA (~47-50%)

---

## [1.5.0] - 2026-02-03 - Sistema Integrato di Arricchimento Semantico

### Added
- **integrated_semantic_enricher.py**: Sistema unificato CSV→RDF
  - Entity linking con robust_wikidata_linker.py
  - Normalizzazione valori tecnici (potenza CV/HP, cilindrata cc/litri)
  - IRI personalizzati per pattern frequenti
  - Esclusioni museo-specifiche
- **robust_wikidata_linker.py**: Core entity linking
  - API Wikidata ufficiale con multi-lingua
  - Database statico 50+ automotive brands
  - Fuzzy matching + confidence scoring
  - Cache persistente production_cache.pkl

### Changed
- **Strategia literals → IRI**: 4 approcci implementati
  1. Normalizzazione tecnica: "68 HP" → 68.9452 CV
  2. Entity linking automotive: Ferrari → Q27586
  3. Esclusioni museo: Piano, Sezione (rimangono literal)
  4. IRI custom: ex:year_1925, ex:power_155cv

### Results
- **Test 100 righe**: 174 triple (+74% arricchimento)
  - 18 brand/luoghi linkati
  - 9 valori tecnici normalizzati
  - 31 IRI personalizzati
  - 98 metadati RDF aggiunti

---

## [1.4.0] - 2026-02-03 - Dual Mappings Implementation

### Added
- **generate_kg_dual_mappings.py**: Doppio mapping Schema.org + Wikidata
  - 25 colonne mappate da mappings.csv
  - 15 colonne con mappings doppi
  - 40 predicati totali: 23 Schema.org + 17 Wikidata

### Changed
- **Output finale**: 3,332 triple (+40% vs versione singola)
  - Doppia interoperabilità massimizzata
  - Compatibilità web (Schema.org) + LOD (Wikidata)

### Removed
- Spostato in old/: generate_kg_wikidata.py e output_wikidata.nt

---

## [1.3.0] - 2026-02-01 - Wikidata Integration

### Added
- **Wikidata_P.csv**: 291 proprietà Wikidata automotive
- **generate_kg_wikidata.py**: Sistema tri-livello predicati
  - 10 proprietà Wikidata (P217, P1716, P495, P2754, P1002, P8628, P2109, P2052, P2073, P166)
  - 9 proprietà Schema.org (model, modelDate, description, etc.)
  - 10 proprietà custom (floor, section, engineDescription, etc.)

### Changed
- **Copertura totale**: 163/163 veicoli processati (100%)
  - Include veicoli senza inventario (row_N fallback)
- **Output**: 2,368 triple (+50% vs fase precedente)

### Benefits
- **Interoperabilità globale**: Linked Open Data compliance
- **Semantica precisa**: P8628 (engine displacement) vs generico "cilindrata"
- **Query federata**: SPARQL su knowledge graph distribuiti

---

## [1.2.0] - 2026-01-31 - Mappings Dinamici

### Added
- Sistema mappings-driven con separazione dati/mappature/logica
- Lettura mappature da file esterno (mappings.csv)

### Changed
- Mappings hardcoded → Mappings dinamici
- Manutenzione: Tecnica → Non-tecnica
- Scalabilità: Limitata → Eccellente

### Results
- **Triple**: 1,579 (architettura migliorata)
- **Manutenibilità**: Separazione responsabilità ottenuta

---

## [1.1.0] - 2026-01-31 - Python RDFLib Native

### Added
- **generate_kg.py**: Script Python con RDFLib + pandas
- Mappings hardcoded nel codice
- Tipizzazione XSD automatica (gYear per anni)

### Benefits
- Processo unico vs pipeline multi-step
- Performance RDFLib superiori
- Controllo totale valori vuoti

### Results
- **Triple**: 1,579
- **Veicoli**: 160/163
- **Schema.org compliance**: 100%

---

## [1.0.0] - 2026-01-31 - Initial SPARQL Anything Approach

### Added
- Initial project structure for museum knowledge graph
- **clean_museo_data.py**: CSV data cleaning script
- **mappings.sparql**: SPARQL transformation query
- Post-processing filter for empty values
- Comprehensive documentation and project log

### Features
- **Data Processing**: Clean 163 vehicles from 29 to 11 semantic columns
- **RDF Generation**: Transform CSV to N-Triples format (~2,500 triple)
- **Quality Control**: Zero empty values in final knowledge graph
- **Rich Semantics**: 11 properties per vehicle

### Technical Details
- **Input**: museo.csv (164 rows × 29 columns)
- **Intermediate**: museo_cleaned.csv (163 rows × 11 columns)
- **Output**: output.nt (~1,500 triple)
- **Completeness**: Optimized from 0.6% (carrozzeria) to 75-80% (technical data)

### Limitations
- Pipeline in due fasi (cleaning + transformation)
- Dipendenza da SPARQL Anything tool esterno
- Post-processing manuale per valori vuoti

---

## Evolution Summary

| Versione | Data | Approach | Triple | Veicoli | Key Innovation |
|----------|------|----------|--------|---------|----------------|
| **2.0.0** | 12/02/26 | **CSV→RDF Validated** | **5,162** | **160** | **Validazione ontologica P31** |
| 1.5.0 | 03/02/26 | Arricchimento semantico | 4,000+ | 160 | Entity linking + normalizzazione |
| 1.4.0 | 03/02/26 | Dual mappings | 3,332 | 163 | Doppia interoperabilità |
| 1.3.0 | 01/02/26 | Wikidata integration | 2,368 | 163 | Proprietà automotive-specific |
| 1.2.0 | 31/01/26 | Mappings dinamici | 1,579 | 160 | Separazione dati/logica |
| 1.1.0 | 31/01/26 | Python RDFLib | 1,579 | 160 | Script nativo Python |
| 1.0.0 | 31/01/26 | SPARQL Anything | ~1,500 | 160 | Pipeline semi-automatica |

---

*Per documentazione dettagliata, vedere [progetto_log.md](notes/md/progetto_log.md)*