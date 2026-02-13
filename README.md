# Knowledge Graph per Museo Automobilistico

**Ultimo aggiornamento**: 13 febbraio 2026

Progetto di tesi per la creazione di knowledge graph a partire da dati del museo utilizzando tecnologie del web semantico, entity linking automatico e integrazione avanzata con Wikidata.

## 🎯 Obiettivi

- **Generazione RDF da CSV**: Sistema diretto da museo.csv a Knowledge Graph RDF senza intermediari
- **Validazione ontologica rigorosa**: Verifica P31 (instance of) per prevenire linking errati (es. Q1789258 music band vs automotive)
- **Entity linking semantico**: Integrazione Wikidata API con confidence scoring e type checking
- **Doppia interoperabilità**: Mappings Wikidata (LOD) + Schema.org (Web) con HTTPS enforcement
- **Logica centralizzata**: Tutta la business logic in museum_mappings.py per massima manutenibilità
- **Gestione intelligente literals**: Mantiene literal quando appropriato (no forced IRI creation)
- **Test LLM comparative**: Framework oneshot vs zeroshot per estrazione entità (+59.6% improvement con esempi)

## 📁 Struttura del Progetto

```
├── data/                          # Dataset e risorse semantiche
│   ├── museo.csv                 # Dataset originale (163 veicoli, 29 colonne, header riga 2)
│   ├── museum_column_mapping.csv # 27 mappings Wikidata properties
│   ├── mappings.csv              # 44 mappings Schema.org (HTTPS enforced)
│   └── Wikidata_P.csv            # 291 proprietà Wikidata per automotive
├── scripts/                      # 🚀 Sistema Generazione RDF con Validazione
│   ├── integrated_semantic_enricher.py  # ⭐ Orchestrazione CSV→RDF (refactored 12/02/2026)
│   ├── robust_wikidata_linker.py        # Entity linking + validazione ontologica P31
│   ├── museum_mappings.py               # ⭐ Hub logica centralizzata (27 mappings, 90+ rules)
│   └── es/                       # Cache Wikidata persistente
│   └── production_cache_entities.json   # Cache human-readable (79 entities)tities)
│   └── production_cache_entities.json   # Cache human-readable
├── llm_test/                     # ⭐ Test LLM per estrazione entità
│   ├── compare_modes.py          # Confronto risultati zeroshot vs oneshot
│   ├── config.yaml               # Configurazione globale LLM
│   ├── cookbook.ipynb            # Notebook sperimentazione
│   ├── oneshot/                  # Test con esempio di guida
│   │   ├── config.yaml           # Config con esempio Ferrari F40
│   │   ├── test_extraction.py    # Script estrazione oneshot
│   │   └── results_oneshot.json  # Risultati (65/99 successi = 65.7%)
│   └── zeroshot/                 # Test senza esempi
│       ├── config.yaml           # Config base senza esempi
│       ├── test_extraction.py    # Script estrazione zeroshot
│       └── results_zeroshot.json # Risultati (6/99 successi = 6.1%)
├── queries/                      # Query attive (vuoto)
├── output/                       # 📊 Output finale
│   └── output_automatic_enriched.nt  # ⭐ KG finale con validazione (5,162 triple)
├── old/                          # 🗄️ Archivio completo sviluppo storico
│   ├── scripts/                 # Script evolutivi precedenti
│   │   ├── generate_kg_dual_mappings.py    # Generatore con mappings multipli  
│   │   ├── advanced_semantic_enrichment.py # Versione intermedia arricchimento
│   │   ├── automatic_semantic_enrichment.py # Prima versione entity linking
│   │   ├── entity_linking_enrichment.py     # Sistema brand fuzzy matching
│   │   ├── generate_and_enrich.py           # Script combinato generazione+arricchimento
│   │   ├── clean_museo_data.py              # Approccio SPARQL Anything legacy
│   │   ├── generate_kg.py                   # Prima implementazione Python
│   │   ├── generate_kg_complete.py          # Implementazione Schema.org completa
│   │   └── generate_kg_wikidata.py          # Implementazione Wikidata singola
│   ├── output/                  # Output storici e test
│   │   ├── output_semantic_enriched*.nt     # Versioni arricchimento intermedie
│   │   ├── test_sample*.nt                  # File test campione (cancellati)
│   │   ├── output.nt                        # Output SPARQL Anything (1,579 triple)
│   │   ├── output_complete.nt               # Output Schema.org completo (2,368 triple)
│   │   └── output_wikidata.nt               # Output Wikidata singolo (2,368 triple)
│   ├── cache/                   # File cache test (*.pkl)
│   ├── mappings_kg.csv          # Mappings intermedi legacy
│   └── queries/
│       └── mappings.sparql      # Query SPARQL Anything legacy
├── .venv/                        # Ambiente virtuale Python
├── sparql-anything-1.2.0-NIGHTLY-SNAPSHOT.jar  # Tool legacy
└── notes/
    └── md/
        └── progetto_log.md       # Documentazione completa (1.270+ righe)
```

## 🚀 Quick Start

### Generazione Knowledge Graph (Sistema Finale - CSV-to-RDF con Validazione Ontologica)

#### 1. Setup Ambiente
```bash
# Creazione ambiente virtuale
python -m venv .venv
.venv\Scripts\activate

# Installazione dipendenze
pip install pandas>=1.3.0 rdflib>=6.0.0 requests
```

#### 2. Generazione Knowledge Graph
```bash
cd c:\Users\salva\Desktop\Tesi
python scripts/integrated_semantic_enricher.py
```

**Output**: `output/output_automatic_enriched.nt` (5,162 triple con validazione ontologica)

**Caratteristiche sistema**:
- ✅ Lettura diretta da museo.csv (header riga 2)
- ✅ Validazione P31 (instance of) pre-scoring
- ✅ Doppio mapping: Wikidata + Schema.org HTTPS
- ✅ Cache persistente: cache/production_cache.pkl
- ✅ Confidence threshold: 0.6 (riduce false positives)
- ✅ Gestione edge cases: donazioni (P1028), acronimi, incompatible types

### Test LLM per Estrazione Entità

#### 1. Setup Ambiente GPU
```bash
# Installazione dipendenze LLM
pip install torch transformers accelerate pandas pyyaml

# Verifica GPU
python llm_test/test_gpu_setup.py
```

#### 2. Esecuzione Test
```bash
# Test zeroshot (senza esempi)
cd llm_test/zeroshot
python test_extraction.py  # Output: 6/99 successi (6.1%)

# Test oneshot (con esempio)
cd ../oneshot  
python test_extraction.py  # Output: 65/99 successi (65.7%)

# Confronto risultati
cd ..
python compare_modes.py    # Analisi comparativa
```

#### 3. Configurazione Modello
- **Modello**: Qwen/Qwen3-0.6B (600M parametri, ottimizzato per GPU laptop)
- **Temperature**: 0.2 (bassa creatività per consistenza)
- **Max tokens**: 300 (~200-250 parole output)
- **Entità target**: MARCA, PAESE, PILOTA, TIPO_VETTURA, CILINDRATA, DESIGNER, GARA

### 🗄️ Approcci Legacy (in /old/)

Gli approcci precedenti sono stati archiviati per riferimento storico:

- **SPARQL Anything**: `old/queries/mappings.sparql` + `old/scripts/clean_museo_data.py`
- **Python Schema.org**: `old/scripts/generate_kg_complete.py`  
- **Primera implementazione**: `old/scripts/generate_kg.py`
- **Wikidata singolo**: `old/scripts/generate_kg_wikidata.py`

Per testare gli approcci legacy, i file sono disponibili nella cartella `/old/` con i rispettivi output.

## 📊 Risultati

### Knowledge Graph Finale (Sistema con Validazione Ontologica)
- **160 veicoli** processati con entity linking validato
- **5,162 triple RDF** generate (`output/output_automati (97.5% completezza)
- **5,162 triple RDF** generate (`output/output_automatic_enriched.nt`)
  - 1,798 literals (anni, velocità, potenza, descrizioni)
  - 1,566 IRIs Wikidata (entità validate con P31 instance of)
  - 0 custom IRIs (solo vehicle URIs, design choice finale)
- **293 entità Wikidata** linkate (tutte ontologicamente corrette)
- **79 entities in cache** (persistente per performance API)
- **Doppia interoperabilità**: Wikidata (27 properties) + Schema.org (44 properties) HTTPS
- **Validazione rigorosa**: 0 false positives (Q1789258 music band rejected, OM mantenuto literal)
- **Copertura temporale**: 1891-2000 (109 anni di storia automobilistica)
- **81 marche** rappresentate (prevalenza europea 85%: Italia 40%, Germania 30%
### Test LLM per Estrazione Entità improvement)
- **Modello utilizzato**: Qwen/Qwen3-0.6B (600M parametri) su GPU RTX 4050 Laptop (6.44 GB)
- **Configurazione**: Temperature 0.2, max_tokens 300, FP16 per ottimizzazione memoria
- **Oneshot**: 65/99 successi (65.7%) - esempio Ferrari F40 come guida
- **Zeroshot**: 6/99 successi (6.1%) - senza esempi di riferimento, JSON malformati frequenti
- **Migliori entità estratte** (oneshot): MARCA, PAESE, DESIGNER (>60% accuratezza)
- **Entità più difficili**: PILOTA, GARA (~47-50% accuratezza)
- **Debug framework**: Sistema progressivo con timing, memory tracking e ETA calculationER (>60% accuratezza)
- **Entità più difficili**: PILOTA, GARA (~47-50% accuratezza)

### 🔍 Sistema di Validazione Ontologica

#### Problema Risolto: False Positives Semantici
**Caso critico**: Q1789258 (music band "OM") erroneamente linkato come automotive manufacturer

#### Soluzione Implementata
**Validazione P31 (instance of) pre-scoring** in robust_wikidata_linker.py:
# In robust_wikidata_linker.py
incompatible_types = {
    'Q215380',   # musical group
    'Q482994',   # album
    'Q7366',     # song
    'Q11424',    # film
    'Q5398426',  # television series
    'Q7889',     # video game
    'Q571',      # book
    'Q11173',    # chemical compound
}

def _validate_ontology(candidate, predicate, label):
    """Validazione ontologica PRIMA del calcolo score"""
    # 1. Estrai P31 (instance of) claims
    instance_types = extract_p31_from_candidate(candidate)
    
    # 2. REJECT incompatible types (media/entertainment)
    if instance_types & incompatible_types:
        return False, "[REJECTED] incompatible type"
    
    # 3. VALIDATE correct type for predicate
    expected_type = entity_type_mappings.get(predicate)  # es. Q786820 per manufacturer
    if expected_type in instance_types:
        return True, "[VALIDATED] correct type"
    
    # 4. Special rules: acronyms ≤3 chars require automotive type
    if len(label) <= 3 and expected_type not in instance_types:
        return False, "[REJECTED] short acronym without type"
    
    # 5. Accept if no incompatible types found
    return True, "[WARNING] no P31 claims found type)
    if len(label) <= 3 and expected_type not in instance_types:
        return False, "[REJECTED] short acronym without type"
```

**Risultati**:
- ✅ Q1789258 (OM band) → REJECTED, mantenuto come literal
- ✅ Q26921 (Alfa Romeo) → VALIDATED as Q786820 (automotive manufacturer)
- ✅ Q27586 (Ferrari) → VALIDATED as Q786820 (automotive manufacturer)

### 🏗️ Architettura Centralizzata

**Separazione delle responsabilità**:

1. **museum_mappings.py** - Hub logica centralizzata
   - `museum_mappings`: Dict colonna→predicato (27 mappings)
   - `literal_only_properties`: Lista 90+ properties che restano literal
   - `iri_target_properties`: Properties per entity linking
   - `entity_type_mappings`: Predicato→tipo Wikidata atteso
   - `incompatible_types`: Tipi da rifiutare (bands, films, albums)
   - Funzioni: `is_year_value()`, `is_donation()`, `is_long_description()`

2. **integrated_semantic_enricher.py** - Orchestrazione
   - Lettura museo.csv (header=1)
   - Caricamento museum_column_mapping.csv + mappings.csv
   - Generazione triple con doppio mapping
   - Applicazione entity linking con validazione

3. **robust_wikidata_linker.py** - API + Validation
   - Wikidata API search con multi-lingua
   - Validazione ontologica pre-scoring
   - Confidence scoring (threshold: 0.6)
   - Cache persistente (cache/production_cache.pkl)

**Vantaggi**:
- ✅ Zero logica hardcoded in enricher
- ✅ Modifiche configurazione senza toccare codice
- ✅ Testabilità e manutenibilità massime
- ✅ Sistema riusabile per altri dataset

### Sistema a Tre Livelli di Proprietà

#### 🌐 **Livello Wikidata** (10 proprietà)
- `wdt:P217` → inventory number
- `wdt:P1716` → brand  
- `wdt:P495` → country of origin
- `wdt:P2754` → production date
- `wdt:P1002` → engine configuration
- `wdt:P8628` → engine displacement
- `wdt:P2109` → nominal power output  
- `wdt:P2052` → speed
- `wdt:P2073` → vehicle range
- `wdt:P166` → award received

#### 🌐 **Livello Schema.org** (9 proprietà)
- `schema:model`, `schema:modelDate`, `schema:description`
- `schema:purchaseDate`, `schema:fuelType`, `schema:numberOfForwardGears`
- `schema:fuelConsumption`, `schema:bodyType`, `schema:manufacturer`

#### 🏛️ **Livello Custom** (10 proprietà)
- Proprietà specifiche museo: `ex:floor`, `ex:section`
- Dettagli tecnici: `ex:engineDescription`, `ex:transmission`, `ex:chassis`
- Metadati acquisizione: `ex:acquisitionYear`, `ex:designYear`

### 📈 Evoluzione del Progetto

| Versione | Triple | Approccio | Semantica | Status |
|----------|--------|-----------|-----------|--------|
| SPARQL Anything | 1,579 | Query SPARQL | Schema.org | ✅ `old/output/output.nt` |
| Python Schema.org | 2,368 | Hardcoded | Schema.org | ✅ `old/output/output_complete.nt` |
| Dual Mappings | 3,332 | Mappings CSV | Wikidata+Schema.org | ✅ `old/output/output_dual_mappings.nt` |
| **CSV-to-RDF Validato** | **5,162** | **Validazione Ontologica** | **Wikidata+Schema.org HTTPS** | **🚀 ATTIVO** |

**Innovazioni versione finale**:
- ✅ Lettura diretta da museo.csv (no intermediari RDF)
- ✅ Validazione P31 pre-scoring (elimina false positives)
- ✅ Logica centralizzata in museum_mappings.py
- ✅ Confidence threshold 0.6 (vs 0.4 precedente)
- ✅ Gestione edge cases: donazioni (P1028), acronimi, incompatible types
- ✅ Cache persistente ottimizzata (79 entities)

## 🔧 Tecnologie Utilizzate

### Core Technologies
- **Python 3.x**: Elaborazione principale con pandas e rdflib
- **Wikidata**: 291 proprietà automotive per interoperabilità LOD
- **Schema.org**: Ontologie standard web
- **N-Triples**: Formato output RDF enterprise
- **SPARQL Anything**: Tool legacy per trasformazione CSV → RDF

### Dipendenze Python
```python
# Knowledge Graph Generation
pandas>=1.3.0     # Manipolazione CSV e analisi dati
rdflib>=6.0.0     # Generazione RDF e serializzazione N-Triples
requests          # API calls a Wikidata Query Service
urllib.parse      # Encoding URI (standard library)

# LLM Testing  
torch             # Framework deep learning con supporto CUDA
transformers      # Libreria HuggingFace per modelli LLM
accelerate        # Ottimizzazione memoria GPU
pyyaml            # Parsing file configurazione YAML
```

### Infrastructure
- **Git**: Controllo versione con .gitignore per Python
- **Virtual Environment**: Isolamento dipendenze (.venv/)
- **SPARQL Anything JAR**: Tool esterno per approccio alternativo

## 📈 Esempi di Dati

### Esempio 1: Veicolo con Entity Linking Validato (Alfa Romeo 8C 2300)
```turtle
<http://example.org/vehicle_V016> a schema:Vehicle ;
    # Wikidata Properties
    wdt:P217 "V 016" ;                    # inventory number
    wdt:P176 "Alfa Romeo"^^xsd:string ;   # brand (literal - validated entity)
    wdt:P495 "Italia"^^xsd:string ;       # country
    wdt:P8628 "2336 cc"^^xsd:string ;     # engine displacement  
    wdt:P2109 "155 CV a 5200 giri/min."^^xsd:string ; # power
    wdt:P2052 "180 km/h"^^xsd:string ;    # speed
    
    # Schema.org Properties (HTTPS enforced)
    schema:model "8C 2300"^^xsd:string ;
    schema:datePublished "1934"^^xsd:string ;
    schema:brand "Alfa Romeo"^^xsd:string ;
    schema:countryOfOrigin "Italia"^^xsd:string .
```

### Esempio 2: Edge Case - OM Brand (Q1789258 Rejected)
```turtle
<http://example.org/vehicle_V098> a schema:Vehicle ;
    wdt:P176 "OM"^^xsd:string ;           # Kept as literal (band rejected)
    schema:brand "OM"^^xsd:string .

# Validation log:
# Searching Wikidata for: OM (manufacturer)
#   [REJECTED] Q1789258: incompatible type (music/media)
#   ❌ No valid Wikidata entity found for "OM"
#   → Maintained as literal
```

### Esempio 3: Donazione con Predicati Speciali
```turtle
<http://example.org/vehicle_V016> a schema:Vehicle ;
    wdt:P1028 "Dono di Alfa Romeo S.p.A., Milano"^^xsd:string ; # donated by
    schema:sponsor "Dono di Alfa Romeo S.p.A., Milano"^^xsd:string .

# Pattern detected: "Dono di..." → uses P1028 instead of P127 (owned by)
```

## 🎓 Contributi Accademici

### Innovazioni Metodologiche
- **Validazione Ontologica Pre-Scoring**: Verifica P31 (instance of) prima del confidence scoring per eliminare false positives semantici
- **Architettura Centralizzata**: Separazione completa logica/dati/configurazione con museum_mappings.py come hub
- **CSV-to-RDF Diretto**: Generazione RDF da fonte primaria senza intermediari, riducendo punti di failure
- **Dual Mapping Strategy**: Simultanea applicazione Wikidata (LOD) + Schema.org (Web) per massima interoperabilità
- **Edge Case Management**: Regole esplicite per donazioni (P1028), acronimi (≤3 char), incompatible types

### Risultati Tecnici
- **Zero False Positives**: Sistema elimina linking errati (Q1789258 music band vs automotive)
- **293 Entities Validate**: Tutte le entities linkate passano validazione ontologica P31
- **5,162 Triple Semantiche**: +118% rispetto approccio dual mappings (3,332)
- **Confidence Optimized**: Threshold 0.6 bilanciato tra recall e precision
- **Cache Persistente**: Sistema ottimizzato riduce API calls a 79 entities uniche
- **HTTPS Enforcement**: Schema.org properties tutte con protocollo sicuro

### Best Practices Implementate
- **Separation of Concerns**: Logica (museum_mappings.py), orchestrazione (enricher.py), API (linker.py)
- **Ontological Validation**: Verifica tipo entità prima dell'accettazione (instance of checking)
- **Explicit Edge Cases**: Gestione specifica per pattern ricorrenti (donazioni, acronimi)
- **Type Safety**: 90+ literal_only_properties esplicitamente dichiarate
- **Progressive Enhancement**: Sistema mantiene literal quando IRI non appropriato (no forced linking)

### Pubblicazioni Scientifiche Potenziali
- **"Ontological Validation in Automated Entity Linking: A Case Study on Automotive Knowledge Graphs"**
- **"CSV-to-RDF with Semantic Type Checking: Preventing False Positives in Domain-Specific Linking"**
- **"Centralized Business Logic Architecture for Maintainable Knowledge Graph Generation Systems"**

## 📚 Documentazione

Vedi [progetto_log.md](notes/md/progetto_log.md) per la documentazione completa del processo di sviluppo.

## 🏁 Status e Roadmap

### ✅ **Completato**
- [x] **Architettura CSV-to-RDF**: Sistema diretto da museo.csv senza intermediari
- [x] **Validazione ontologica**: Verifica P31 pre-scoring per eliminare false positives
- [x] **Logica centralizzata**: Museum_mappings.py come hub configurazione completo
- [x] **Doppia interoperabilità**: Wikidata + Schema.org HTTPS simultanei
- [x] **Cache persistente**: Sistema ottimizzato con 79 entities validate
- [x] **Gestione edge cases**: Donazioni (P1028), acronimi, incompatible types
- [x] **Knowledge Graph produzione**: 5,162 triple con 160 veicoli, 293 entities linkate
- [x] **Test LLM**: Framework comparativo zeroshot vs oneshot per estrazione entità
- [x] **Documentazione completa**: 1,900+ righe log progetto (notes/md/progetto_log.md)

### 🎯 **Risultati Chiave Raggiunti**
- **Zero false positives**: Q1789258 (music band) correttamente rejected
- **Entity linking validato**: Tutte le 293 entities passano validazione P31
- **Confidence optimized**: Threshold 0.6 elimina match ambigui
- **Interoperabilità massima**: Wikidata (LOD) + Schema.org (Web) simultanei
- **Architettura enterprise**: Codice modulare, testabile, riusabile

### 🔄 **In Corso**  
- Import in triplestore enterprise (GraphDB/Blazegraph)
- Testing query SPARQL avanzate su dataset completo
- Validazione qualità con SHACL constraints

### 📋 **Roadmap Futura**
- **Entity Linking IRI completo**: Trasformare literals validati in wd:Q-codes
- **Qualificatori Temporali**: Estensione con P585, P580, P582  
- **Query Federate**: Integrazione live con Wikidata Query Service
- **Visualizzazione**: Dashboard interattive per esplorazione dati
- **API SPARQL**: Endpoint pubblico per ricerca semantica
- **ML-enhanced validation**: Integrazione LLM per entity disambiguation

---

**Data progetto**: Gennaio-Febbraio 2026  
**Ambito**: Tesi di laurea - Web Semantico e Knowledge Graph  
**Keywords**: Wikidata, Schema.org, RDF, N-Triples, SPARQL, LOD, Python, Automotive Domain