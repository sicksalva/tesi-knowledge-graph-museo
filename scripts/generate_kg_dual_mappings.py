#!/usr/bin/env python3
"""
Script per generare knowledge graph RDF usando ENTRAMBE le opzioni di mappings.
Include sia Schema.org (Option 1) che Wikidata (Option 1) per massimizzare i mappings.
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
WD = Namespace("http://www.wikidata.org/prop/direct/")

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

def create_wikidata_predicate(wikidata_value):
    """Crea un predicato Wikidata valido dal valore della colonna."""
    if not wikidata_value:
        return None
    
    # Estrae il codice della proprietà (es. "P2073" da "vehicle range (P2073)")
    property_match = re.search(r'\b(P\d+)\b', wikidata_value)
    if property_match:
        property_code = property_match.group(1)
        return WD[property_code]
    
    return None

def load_dual_mappings(mappings_file):
    """Carica mappings con ENTRAMBE le opzioni: Schema.org e Wikidata."""
    if not os.path.exists(mappings_file):
        print(f"Errore: File mappings {mappings_file} non trovato!")
        return None
    
    try:
        df_mappings = pd.read_csv(mappings_file)
        print(f"Mappings caricati: {len(df_mappings)} righe")
        
        dual_mappings = {}
        
        for _, row in df_mappings.iterrows():
            source = clean_value(row.get('Source'))
            schema_org_option1 = clean_value(row.get('Option 1'))  # Schema.org
            wikidata_option1 = clean_value(row.get('Option 1.1'))  # Wikidata
            
            if not source:
                continue
            
            # Decodifica il nome della colonna dal Source
            column_name = decode_source_column(source)
            if not column_name:
                continue
                
            # Normalizza il nome colonna per matching
            normalized_column = column_name.replace('%20', ' ').replace('%2520', ' ')
            
            mappings_list = []
            
            # Aggiungi mapping Schema.org se presente
            if schema_org_option1:
                if schema_org_option1.startswith('https://schema.org/') or schema_org_option1.startswith('http://schema.org/'):
                    predicate_uri = URIRef(schema_org_option1)
                elif '://' not in schema_org_option1 and len(schema_org_option1.split()) == 1:
                    # Single word properties - assume Schema.org
                    predicate_uri = SCHEMA[schema_org_option1]
                else:
                    predicate_uri = None
                
                if predicate_uri:
                    # Determina il datatype
                    if 'anno' in normalized_column.lower() or 'year' in schema_org_option1.lower():
                        datatype = XSD.gYear
                    else:
                        datatype = XSD.string
                    
                    mappings_list.append({
                        'predicate': predicate_uri,
                        'datatype': datatype,
                        'source': 'Schema.org'
                    })
            
            # Aggiungi mapping Wikidata se presente
            if wikidata_option1:
                wikidata_predicate = create_wikidata_predicate(wikidata_option1)
                if wikidata_predicate:
                    mappings_list.append({
                        'predicate': wikidata_predicate,
                        'datatype': XSD.string,  # Wikidata properties sono generalmente string
                        'source': 'Wikidata'
                    })
            
            # Salva i mappings per questa colonna
            if mappings_list:
                dual_mappings[normalized_column] = mappings_list
                mapping_sources = [m['source'] for m in mappings_list]
                print(f"  Mapping: '{normalized_column}' → {len(mappings_list)} predicati ({', '.join(mapping_sources)})")
        
        return dual_mappings
        
    except Exception as e:
        print(f"Errore nel caricamento mappings: {str(e)}")
        import traceback
        traceback.print_exc()
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

def generate_dual_mappings_kg():
    """
    Genera knowledge graph usando ENTRAMBE le opzioni di mappings quando disponibili.
    """
    
    # File di input e output
    museo_file = "data/museo.csv"
    mappings_file = "data/mappings.csv"
    output_file = "output/output_dual_mappings.nt"
    
    print("=== GENERATORE KG CON MAPPINGS MULTIPLI ===")
    print(f"File dati: {museo_file}")
    print(f"File mappings: {mappings_file}")
    print(f"Output: {output_file}")
    print()
    
    # Verifica file di input
    if not os.path.exists(museo_file):
        print(f"Errore: File {museo_file} non trovato!")
        return False
    
    # Carica dual mappings
    dual_mappings = load_dual_mappings(mappings_file)
    if not dual_mappings:
        print("Errore: Impossibile caricare i mappings!")
        return False
    
    print(f"\nMappings totali caricati: {len(dual_mappings)} colonne")
    total_predicates = sum(len(mapping_list) for mapping_list in dual_mappings.values())
    print(f"Predicati totali: {total_predicates}")
    print()
    
    try:
        # Leggi il CSV originale saltando la prima riga
        print(f"Leggendo {museo_file}...")
        df_raw = pd.read_csv(museo_file, skiprows=1)
        
        print(f"Dataset caricato: {df_raw.shape[0]} righe, {df_raw.shape[1]} colonne")
        print()
        
        # Crea il grafo RDF
        g = Graph()
        g.bind("ex", EX)
        g.bind("schema", SCHEMA)
        g.bind("wdt", WD)
        
        # Contatori
        total_rows = len(df_raw)
        processed_count = 0
        total_triples = 0
        dual_mapped_count = 0
        
        # Processa ogni riga
        for idx, row in df_raw.iterrows():
            
            # Crea URI del veicolo
            inventario = clean_value(row.get('N. inventario'))
            vehicle_uri = create_vehicle_uri(inventario, idx)
            
            # Aggiungi tipo veicolo
            g.add((vehicle_uri, RDF.type, SCHEMA.Vehicle))
            row_triples = 1
            
            # Processa tutte le colonne
            for column in df_raw.columns:
                value = clean_value(row.get(column))
                if not value:
                    continue
                
                if column in dual_mappings:
                    # Mapping multiplo trovato - aggiungi TUTTE le opzioni
                    mapping_list = dual_mappings[column]
                    for mapping in mapping_list:
                        predicate = mapping['predicate']
                        datatype = mapping['datatype']
                        literal_value = apply_datatype(value, datatype)
                        g.add((vehicle_uri, predicate, literal_value))
                        row_triples += 1
                    
                    # Conta se ha mapping multipli
                    if len(mapping_list) > 1:
                        dual_mapped_count += 1
                else:
                    # Colonna non mappata - crea predicato generico
                    safe_column = re.sub(r'[^a-zA-Z0-9_]', '_', column)
                    predicate = EX[safe_column]
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
        print(f"\n=== RISULTATI MAPPINGS MULTIPLI ===")
        print(f"Righe processate: {processed_count}/{total_rows}")
        print(f"Triple generate: {len(g)}")
        print(f"Media triple per veicolo: {len(g) / processed_count:.1f}")
        print(f"File salvato in: {output_file}")
        
        # Statistiche mappings
        schema_count = sum(1 for mapping_list in dual_mappings.values() 
                          for mapping in mapping_list if mapping['source'] == 'Schema.org')
        wikidata_count = sum(1 for mapping_list in dual_mappings.values() 
                            for mapping in mapping_list if mapping['source'] == 'Wikidata')
        
        print(f"\n=== STATISTICHE MAPPINGS ===")
        print(f"Colonne con mappings multipli: {sum(1 for ml in dual_mappings.values() if len(ml) > 1)}")
        print(f"Predicati Schema.org: {schema_count}")
        print(f"Predicati Wikidata: {wikidata_count}")
        print(f"Totale predicati semantici: {schema_count + wikidata_count}")
        
        return True
        
    except Exception as e:
        print(f"Errore durante la generazione: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_dual_mappings_kg()