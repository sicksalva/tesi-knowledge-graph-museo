#!/usr/bin/env python3
"""
Script per generare knowledge graph RDF COMPLETO usando mappings dinamici.
Include TUTTE le righe e TUTTE le colonne possibili da museo.csv e mappings.csv.
"""

import pandas as pd
import os
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD
import re
from urllib.parse import unquote

# Definizione dei namespace
EX = Namespace("http://example.org/")
SCHEMA = Namespace("http://schema.org/")

def clean_value(value):
    """Pulisce e normalizza un valore dal CSV."""
    if pd.isna(value):
        return None
    
    value = str(value).strip()
    if value == "" or value.lower() in ["nan", "n/a", "#n/a", "null"]:
        return None
    
    return value

def create_vehicle_uri(inventario, row_index):
    """Crea URI per un veicolo. Se manca inventario, usa index della riga."""
    if inventario and inventario.strip():
        # Pulisce il numero di inventario per l'URI
        clean_inv = re.sub(r'[^a-zA-Z0-9_-]', '_', inventario.strip())
        return EX[f"vehicle/{clean_inv}"]
    else:
        # Se non c'è inventario, usa l'indice della riga
        return EX[f"vehicle/row_{row_index}"]

def decode_source_column(encoded_source):
    """Decodifica il nome della colonna dal Source URL-encoded."""
    try:
        # Estrae la parte dopo 'data/' e decodifica
        if 'data/' in encoded_source:
            encoded_part = encoded_source.split('data/')[-1]
            decoded = unquote(encoded_part)
            return decoded
        return None
    except:
        return None

def load_mappings(mappings_file):
    """Carica DINAMICAMENTE TUTTI i mappings validi dal file CSV."""
    if not os.path.exists(mappings_file):
        print(f"Errore: File mappings {mappings_file} non trovato!")
        return None
    
    try:
        df_mappings = pd.read_csv(mappings_file)
        print(f"Mappings caricati: {len(df_mappings)} righe")
        
        mappings_dict = {}
        
        for _, row in df_mappings.iterrows():
            source = clean_value(row.get('Source'))
            schema_org = clean_value(row.get('Schema.org'))
            
            if not source or not schema_org:
                continue
            
            # Filtra predicati invalidi (esempi di dati invece di proprietà)
            if any(word in schema_org.lower() for word in ['differenziali', 'comando', 'giri', 'cv', 'km/h', 'cilindri']):
                continue
                
            # Decodifica il nome della colonna dal Source
            column_name = decode_source_column(source)
            if not column_name:
                continue
                
            # Normalizza il nome colonna per matching
            normalized_column = column_name.replace('%20', ' ').replace('%2520', ' ')
            
            # Determina il namespace del predicato - più rigoroso
            if schema_org.startswith('https://schema.org/') or schema_org.startswith('http://schema.org/'):
                predicate_uri = URIRef(schema_org)
            elif schema_org.startswith('http://') or schema_org.startswith('https://'):
                # Altri namespace validi
                predicate_uri = URIRef(schema_org)
            elif '://' not in schema_org and len(schema_org.split()) == 1:
                # Single word properties - assume Schema.org
                predicate_uri = SCHEMA[schema_org]
            else:
                # Skip invalid predicates
                print(f"  SKIP: Invalid predicate '{schema_org}' for column '{normalized_column}'")
                continue
            
            # Determina il datatype
            if 'anno' in normalized_column.lower() or 'year' in schema_org.lower() or normalized_column.lower() == 'anno':
                datatype = XSD.gYear
            else:
                datatype = XSD.string
                
            mappings_dict[normalized_column] = {
                'predicate': predicate_uri,
                'datatype': datatype,
                'source': source
            }
            
            print(f"  Mapping: '{normalized_column}' → {predicate_uri}")
            
        return mappings_dict
        
    except Exception as e:
        print(f"Errore nel caricamento mappings: {str(e)}")
        return None

def apply_datatype(value, datatype):
    """Applica il datatype appropriato al valore."""
    if datatype == XSD.gYear:
        # Estrae solo l'anno se il valore contiene altre informazioni
        year_match = re.search(r'\b(18|19|20)\d{2}\b', value)
        if year_match:
            return Literal(year_match.group(), datatype=XSD.gYear)
        else:
            return Literal(value, datatype=XSD.string)
    else:
        return Literal(value, datatype=XSD.string)

def generate_complete_knowledge_graph():
    """
    Funzione principale per generare il knowledge graph COMPLETO.
    Include TUTTE le righe e TUTTI i mappings possibili.
    """
    
    # File di input e output
    museo_file = "data/museo.csv"
    mappings_file = "data/mappings.csv"
    output_file = "output/output_complete.nt"
    
    print("=== GENERATORE KNOWLEDGE GRAPH COMPLETO ===")
    print(f"File dati: {museo_file}")
    print(f"File mappings: {mappings_file}")
    print(f"Output: {output_file}")
    print()
    
    # Verifica file di input
    if not os.path.exists(museo_file):
        print(f"Errore: File {museo_file} non trovato!")
        return False
    
    # Carica mappings dinamicamente
    mappings = load_mappings(mappings_file)
    if not mappings or len(mappings) < 5:
        print("ATTENZIONE: Mapping dinamici insufficienti, usando mappings estesi")
        # Mappings estesi basati su mappings.csv e struttura del CSV
        mappings = {
            # Colonne principali con mapping Schema.org
            'N. inventario': {'predicate': EX['inventario'], 'datatype': XSD.string},
            'Marca': {'predicate': SCHEMA.brand, 'datatype': XSD.string},
            'Modello': {'predicate': SCHEMA.model, 'datatype': XSD.string},
            'Anno': {'predicate': SCHEMA.modelDate, 'datatype': XSD.gYear},
            'Anni di produzione': {'predicate': EX['productionYears'], 'datatype': XSD.string},
            'Paese': {'predicate': SCHEMA.countryOfOrigin, 'datatype': XSD.string},
            'TESTO': {'predicate': SCHEMA.description, 'datatype': XSD.string},
            'Piano': {'predicate': EX['floor'], 'datatype': XSD.string},
            'Sezione': {'predicate': EX['section'], 'datatype': XSD.string},
            'Acquisizione': {'predicate': SCHEMA.purchaseDate, 'datatype': XSD.string},
            'Tipo di motore': {'predicate': EX['engineType'], 'datatype': XSD.string},
            'Motore': {'predicate': EX['engineConfiguration'], 'datatype': XSD.string},
            'Alimentazione': {'predicate': SCHEMA.fuelType, 'datatype': XSD.string},
            'Cilindrata': {'predicate': SCHEMA.engineDisplacement, 'datatype': XSD.string},
            'Potenza': {'predicate': EX['power'], 'datatype': XSD.string},
            'Cambio': {'predicate': SCHEMA.numberOfForwardGears, 'datatype': XSD.string},
            'Trasmissione': {'predicate': EX['transmission'], 'datatype': XSD.string},
            'Trazione': {'predicate': EX['drivetrain'], 'datatype': XSD.string},
            'Autonomia': {'predicate': EX['range'], 'datatype': XSD.string},
            'Velocità': {'predicate': SCHEMA.speed, 'datatype': XSD.string},
            'Consumo': {'predicate': SCHEMA.fuelConsumption, 'datatype': XSD.string},
            'Telaio': {'predicate': EX['chassis'], 'datatype': XSD.string},
            'Batterie': {'predicate': EX['battery'], 'datatype': XSD.string},
            'Carrozzeria': {'predicate': SCHEMA.bodyType, 'datatype': XSD.string},
            'Piloti': {'predicate': EX['drivers'], 'datatype': XSD.string},
            'Corse ': {'predicate': EX['races'], 'datatype': XSD.string},
            'Carrozzeria/Designer': {'predicate': SCHEMA.manufacturer, 'datatype': XSD.string},
            # Anno duplicati
            'Anno.1': {'predicate': EX['acquisitionYear'], 'datatype': XSD.gYear},
            'Anno.2': {'predicate': EX['designYear'], 'datatype': XSD.gYear}
        }
    
    print("Mappings disponibili:")
    for col, mapping in mappings.items():
        print(f"  {col} → {mapping['predicate']}")
    print()
    
    try:
        # Leggi il CSV originale saltando la prima riga (header categoria)
        print(f"Leggendo {museo_file}...")
        df_raw = pd.read_csv(museo_file, skiprows=1)
        
        print(f"Dataset caricato: {df_raw.shape[0]} righe, {df_raw.shape[1]} colonne")
        print(f"Colonne disponibili: {list(df_raw.columns)}")
        print()
        
        # Crea il grafo RDF
        g = Graph()
        g.bind("ex", EX)
        g.bind("schema", SCHEMA)
        
        # Contatori
        total_rows = len(df_raw)
        processed_count = 0
        total_triples = 0
        
        # Processa OGNI riga (anche senza inventario)
        for idx, row in df_raw.iterrows():
            
            # Crea URI del veicolo (sempre, anche senza inventario)
            inventario = clean_value(row.get('N. inventario'))
            vehicle_uri = create_vehicle_uri(inventario, idx)
            
            # Aggiungi sempre il tipo veicolo
            g.add((vehicle_uri, RDF.type, SCHEMA.Vehicle))
            row_triples = 1
            
            # Processa TUTTE le colonne del CSV
            for column in df_raw.columns:
                value = clean_value(row.get(column))
                if not value:
                    continue
                    
                # Cerca mapping per questa colonna
                mapping = None
                
                # Cerca match diretto
                if column in mappings:
                    mapping = mappings[column]
                else:
                    # Cerca match approssimativo (ignora case e spazi)
                    for mapped_col, mapped_info in mappings.items():
                        if mapped_col.lower().replace(' ', '') == column.lower().replace(' ', ''):
                            mapping = mapped_info
                            break
                
                if mapping:
                    # Mapping trovato - crea tripla semantica
                    predicate = mapping['predicate']
                    datatype = mapping['datatype']
                    literal_value = apply_datatype(value, datatype)
                    g.add((vehicle_uri, predicate, literal_value))
                    row_triples += 1
                else:
                    # Nessun mapping - crea tripla generica con nome colonna
                    predicate = EX[re.sub(r'[^a-zA-Z0-9_]', '_', column)]
                    literal_value = Literal(value, datatype=XSD.string)
                    g.add((vehicle_uri, predicate, literal_value))
                    row_triples += 1
            
            processed_count += 1
            total_triples += row_triples
            
            if processed_count % 50 == 0:
                print(f"Processate {processed_count}/{total_rows} righe...")
        
        # Salva il grafo
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        g.serialize(destination=output_file, format='nt', encoding='utf-8')
        
        # Risultati
        print(f"\n=== RISULTATI COMPLETI ===")
        print(f"Righe processate: {processed_count}/{total_rows} (100%)")
        print(f"Triple generate: {len(g)}")
        print(f"Media triple per veicolo: {len(g) / processed_count:.1f}")
        print(f"File salvato in: {output_file}")
        
        # Statistiche per colonna
        print(f"\n=== COPERTURA COLONNE ===")
        for column in df_raw.columns[:15]:  # Prime 15 colonne
            non_empty = df_raw[column].notna().sum() - (df_raw[column] == '').sum()
            coverage = (non_empty / total_rows) * 100
            mapped = "✅ MAPPATA" if column in mappings else "🔶 GENERICA"
            print(f"{column}: {non_empty}/{total_rows} valori ({coverage:.1f}%) {mapped}")
        
        return True
        
    except Exception as e:
        print(f"Errore durante la generazione: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_complete_knowledge_graph()