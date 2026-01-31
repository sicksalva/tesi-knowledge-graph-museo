# Scelte Implementative - Tesi

Questo documento raccoglie le principali scelte implementative adottate per ogni file del progetto.

## Tabella delle Scelte Implementative

| File | Tipo | Descrizione | Scelte Implementative | Note |
|------|------|-------------|----------------------|------|
| `data/mappings.csv` | Dataset | Mappature generali | | |
| `data/museo.csv` | Dataset | Dati originali del museo | | |
| `data/mappings_kg.csv` | Dataset Modificato | Mappature del knowledge graph |  |  |
| `data/cleaned_csvs/museo_cleaned.csv` | Dataset modificato | Pulizia dei dati dal file mappings |attributi "minimi" descrittivi di una macchina | |
| `output/output.nt` | Output | File RDF in formato N-Triples | | |
| `queries/mappings.sparql` | Query | Query SPARQL per le mappature | | |

## Sezioni Dettagliate

| Colonna | Predicato RDF scelto | Motivazione |
|---------|---------------------|-------------|
| Inventario | `http://example.org/inventario` | Serve come ID univoco dell'oggetto, non c'è schema standard quindi usiamo namespace locale. |
| Marca | `http://schema.org/brand` | Proprietà standard per la marca di un veicolo. |
| Modello | `http://schema.org/model` | Proprietà standard per il modello. |
| Anno | `http://schema.org/modelDate` | Data associata al modello, coerente con gYear. |
| Paese | `http://schema.org/countryOfOrigin` | Origine culturale / geografica. |
| Acquisizione | `http://schema.org/purchaseDate` | Evento storico museale. |
| Carrozzeria | `http://schema.org/bodyType` | Descrizione distintiva della carrozzeria. |

### Preprocessing dei Dati

| Aspetto | Scelta Implementativa | Motivazione |
|---------|----------------------|-------------|
| Pulizia dati | | |
| Formato di output | | |
| Codifica caratteri | | |

### Mappature e Trasformazioni

| Aspetto | Scelta Implementativa | Motivazione |
|---------|----------------------|-------------|
| Schema RDF | | |
| Ontologie utilizzate | | |
| Gestione URI | | |

### Query e Validazione

| Aspetto | Scelta Implementativa | Motivazione |
|---------|----------------------|-------------|
| Linguaggio query | SPARQL | |
| Strategia di validazione | | |
| Gestione errori | | |

## Note Generali

- **Data di creazione**: 31 gennaio 2026
- **Versione**: 1.0
- **Autore**: 

---

*Aggiorna questo documento ogni volta che apporti modifiche significative ai file o alle strategie implementative.*