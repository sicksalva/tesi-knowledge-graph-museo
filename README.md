# Knowledge Graph per Museo Automobilistico

Progetto di tesi per la creazione di knowledge graph a partire da dati del museo utilizzando tecnologie del web semantico e integrazione con Wikidata.

## 🎯 Obiettivi

- Trasformazione di dati CSV in knowledge graph RDF con massima interoperabilità
- Implementazione di tre approcci: SPARQL Anything, Python con Schema.org, Python con Wikidata
- Sistema a tre livelli di proprietà semantiche per copertura totale
- Integrazione con Linked Open Data (Wikidata) per connettività globale
- Creazione di un grafo semantico enterprise-ready per triplestore

## 📁 Struttura del Progetto

```
├── data/                          # Dataset e risorse semantiche
│   ├── museo.csv                 # Dataset originale (163 veicoli, 29 colonne)
│   ├── mappings.csv              # Mappature Schema.org legacy
│   ├── mappings_kg.csv           # Mappature KG intermedie
│   ├── Wikidata_P.csv            # 291 proprietà Wikidata per automotive
│   └── cleaned_csvs/
│       └── museo_cleaned.csv     # Dataset pulito legacy
├── scripts/                      # Script attivo
│   └── generate_kg_wikidata.py   # ⭐ Generatore finale con Wikidata
├── queries/                      # Query attive (vuoto - non più necessario)
├── output/                       # Knowledge graph finale
│   └── output_wikidata.nt       # ⭐ 2.368 triple con interoperabilità LOD
├── old/                          # 🗄️ Archivio sviluppo storico
│   ├── scripts/
│   │   ├── clean_museo_data.py   # Approccio SPARQL Anything
│   │   ├── generate_kg.py        # Prima implementazione Python
│   │   └── generate_kg_complete.py # Implementazione Schema.org completa
│   ├── queries/
│   │   └── mappings.sparql      # Query SPARQL Anything legacy
│   └── output/
│       ├── output.nt            # Output SPARQL Anything (1.579 triple)
│       └── output_complete.nt   # Output Schema.org completo (2.368 triple)
├── .venv/                        # Ambiente virtuale Python
├── sparql-anything-1.2.0-NIGHTLY-SNAPSHOT.jar  # Tool legacy
└── notes/
    └── md/
        └── progetto_log.md       # Documentazione completa (1.199 righe)
```

## 🚀 Quick Start

### Generazione Knowledge Graph (Approccio Finale)

#### 1. Setup Ambiente
```bash
# Creazione ambiente virtuale
python -m venv .venv
.venv\Scripts\activate

# Installazione dipendenze
pip install pandas>=1.3.0 rdflib>=6.0.0
```

#### 2. Generazione Knowledge Graph
```bash
cd c:\Users\salva\Desktop\Tesi
python scripts/generate_kg_wikidata.py
```

**Output**: `output/output_wikidata.nt` (2.368 triple con interoperabilità Wikidata)

### 🗄️ Approcci Legacy (in /old/)

Gli approcci precedenti sono stati archiviati per riferimento storico:

- **SPARQL Anything**: `old/queries/mappings.sparql` + `old/scripts/clean_museo_data.py`
- **Python Schema.org**: `old/scripts/generate_kg_complete.py`  
- **Prima implementazione**: `old/scripts/generate_kg.py`

Per testare gli approcci legacy, i file sono disponibili nella cartella `/old/` con i rispettivi output.

## 📊 Risultati

### Knowledge Graph Finale
- **163 veicoli** trasformati con interoperabilità Linked Open Data  
- **29 proprietà semantiche** mappate su tre livelli
- **2.368 triple RDF** generate (`output/output_wikidata.nt`)
- **100% copertura dati**: Tutte le righe e colonne processate  
- **Copertura temporale**: 1891-2000 (109 anni di storia automobilistica)

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

| Versione | Triple | Copertura | Semantica | Archiviato |
|----------|--------|-----------|-----------|------------|
| SPARQL Anything | 1.579 | 11/29 colonne | Schema.org | ✅ `old/output/output.nt` |
| Python Schema.org | 2.368 | 29/29 colonne | Schema.org | ✅ `old/output/output_complete.nt` |
| **Python Wikidata** | **2.368** | **29/29 colonne** | **Wikidata+Schema.org** | **🚀 Attivo** |

## 🔧 Tecnologie Utilizzate

### Core Technologies
- **Python 3.x**: Elaborazione principale con pandas e rdflib
- **Wikidata**: 291 proprietà automotive per interoperabilità LOD
- **Schema.org**: Ontologie standard web
- **N-Triples**: Formato output RDF enterprise
- **SPARQL Anything**: Tool legacy per trasformazione CSV → RDF

### Dipendenze Python
```python
pandas>=1.3.0     # Manipolazione CSV e analisi dati
rdflib>=6.0.0     # Generazione RDF e serializzazione N-Triples
urllib.parse      # Encoding URI (standard library)
```

### Infrastructure
- **Git**: Controllo versione con .gitignore per Python
- **Virtual Environment**: Isolamento dipendenze (.venv/)
- **SPARQL Anything JAR**: Tool esterno per approccio alternativo

## 📈 Esempi di Dati

### Veicolo con Proprietà Wikidata (Alfa Romeo 8C 2300)
```turtle
<http://example.org/vehicle/V%20016> a schema:Vehicle ;
    wdt:P217 "V 016" ;              # inventory number
    wdt:P1716 wd:Q26151 ;           # brand → Alfa Romeo (Q26151)
    schema:model "8C 2300" ;
    wdt:P2754 "1934"^^xsd:gYear ;   # production date  
    ex:productionYears "1931-1934" ;
    wdt:P495 wd:Q38 ;               # country of origin → Italy (Q38)
    wdt:P1002 "combustione interna" ; # engine configuration
    wdt:P8628 "2336"^^xsd:decimal ; # engine displacement (cc)
    wdt:P2109 "155 CV a 5200 giri/min." ; # nominal power output
    wdt:P2052 "180"^^xsd:decimal .   # speed (km/h)
```

### Esempio Proprietà Multi-Livello
```turtle
<http://example.org/vehicle/V%20042> a schema:Vehicle ;
    # Livello Wikidata (LOD)
    wdt:P217 "V 042" ;
    wdt:P1716 "Ferrari" ;
    wdt:P495 "Italia" ;
    
    # Livello Schema.org (Web Standard)  
    schema:model "250 GT" ;
    schema:modelDate "1962" ;
    schema:fuelType "Benzina" ;
    
    # Livello Custom (Museo-Specific)
    ex:floor "Piano terra" ;
    ex:section "Sezione sportive" ;
    ex:acquisitionYear "1995"^^xsd:gYear .
```

## 🎓 Contributi Accademici

### Innovazioni Metodologiche
- **Sistema Multi-Livello**: Integrazione Wikidata + Schema.org + Custom properties
- **Interoperabilità Massima**: Collegamento a Linked Open Data ecosystem
- **Mappatura Semantica Avanzata**: 291 proprietà Wikidata per dominio automotive
- **Gestione Completezza**: Trasformazione 100% righe/colonne vs approccio selettivo

### Risultati Tecnici
- **Zero Data Loss**: Mantenimento di tutto il contenuto informativo originale
- **Triple Optimization**: Riduzione da 4.500+ a 2.368 triple mantenendo completezza
- **Enterprise Ready**: Formato compatibile con Blazegraph, GraphDB, Apache Jena
- **SPARQL Federato**: Possibilità di query distribuite su knowledge base multiple

### Best Practices Implementate
- **Open World Assumption**: Gestione principio semantico per dati mancanti
- **URI Encoding**: Sicurezza caratteri speciali negli identificatori
- **XSD Datatypes**: Tipizzazione forte per date, numeri, testi
- **Namespace Management**: Separazione clara tra standard e proprietà custom

## 📚 Documentazione

Vedi [progetto_log.md](notes/md/progetto_log.md) per la documentazione completa del processo di sviluppo.

## 🏁 Status e Roadmap

### ✅ **Completato**
- [x] Trasformazione CSV → Knowledge Graph (3 approcci sviluppati)
- [x] Integrazione Wikidata per interoperabilità LOD  
- [x] Sistema proprietà multi-livello (Wikidata + Schema.org + Custom)
- [x] Generazione 2.368 triple con 100% copertura dati
- [x] Documentazione completa processo (1.199 righe log)
- [x] **Archiviazione storico**: Approcci legacy in `/old/` per riferimento

### 🔄 **In Corso**  
- Import in triplestore enterprise (GraphDB/Blazegraph)
- Testing query SPARQL avanzate
- Validazione qualità con SHACL constraints

### 📋 **Roadmap Futura**
- **Entity Linking**: Mapping valori a Q-codes Wikidata specifici
- **Qualificatori Temporali**: Estensione con P585, P580, P582  
- **Query Federate**: Integrazione con altri knowledge graph automotive
- **Visualizzazione**: Dashboard interattive per esplorazione dati
- **API SPARQL**: Endpoint pubblico per ricerca semantica

### 🎯 **Obiettivi Raggiunti**
- **Interoperabilità**: Knowledge graph compatibile con ecosystem LOD globale
- **Scalabilità**: Architettura pronta per dataset più grandi  
- **Manutenibilità**: Codice modulare e documentato
- **Standards Compliance**: Rispetto best practices W3C e comunità semantica

---

**Data progetto**: Gennaio-Febbraio 2026  
**Ambito**: Tesi di laurea - Web Semantico e Knowledge Graph  
**Keywords**: Wikidata, Schema.org, RDF, N-Triples, SPARQL, LOD, Python, Automotive Domain