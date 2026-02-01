#!/usr/bin/env python3
"""
Script per generare knowledge graph RDF usando mappings Wikidata + Schema.org.
Include TUTTE le righe e colonne da museo.csv con predicati semantici da Wikidata.
"""

import pandas as pd
import os
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD
import re
from urllib.parse import quote

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

def load_wikidata_properties(wikidata_file):
    """Carica le proprietà Wikidata da usare come predicati."""
    wikidata_props = {}
    
    if os.path.exists(wikidata_file):
        try:
            df_wd = pd.read_csv(wikidata_file)
            print(f"Proprietà Wikidata caricate: {len(df_wd)} proprietà")
            
            for _, row in df_wd.iterrows():
                claim = clean_value(row.get('claim'))
                label = clean_value(row.get('label'))
                description = clean_value(row.get('description'))
                
                if claim and label:
                    wikidata_props[claim] = {
                        'label': label,
                        'description': description,
                        'uri': WD[claim]
                    }
                    
        except Exception as e:
            print(f"Errore caricamento Wikidata: {str(e)}")
    
    return wikidata_props

def create_enhanced_mappings(wikidata_props):
    """Crea mappings usando proprietà Wikidata + Schema.org."""
    
    mappings = {
        # Identifiers
        'N. inventario': {
            'predicate': WD.P217,  # inventory number
            'datatype': XSD.string,
            'label': 'inventory number'
        },
        
        # Basic vehicle info (Schema.org preferred for general properties)
        'Marca': {
            'predicate': WD.P1716,  # brand
            'datatype': XSD.string,
            'label': 'brand'
        },
        'Modello': {
            'predicate': SCHEMA.model,
            'datatype': XSD.string,
            'label': 'model'
        },
        'Anno': {
            'predicate': SCHEMA.modelDate,
            'datatype': XSD.gYear,
            'label': 'model date'
        },
        'Anni di produzione': {
            'predicate': WD.P2754,  # production date
            'datatype': XSD.string,
            'label': 'production date'
        },
        'Paese': {
            'predicate': WD.P495,  # country of origin
            'datatype': XSD.string,
            'label': 'country of origin'
        },
        
        # Technical specifications (Wikidata automotive properties)
        'Tipo di motore': {
            'predicate': WD.P1002,  # engine configuration
            'datatype': XSD.string,
            'label': 'engine configuration'
        },
        'Cilindrata': {
            'predicate': WD.P8628,  # engine displacement
            'datatype': XSD.string,
            'label': 'engine displacement'
        },
        'Potenza': {
            'predicate': WD.P2109,  # nominal power output
            'datatype': XSD.string,
            'label': 'power output'
        },
        'Velocità': {
            'predicate': WD.P2052,  # speed
            'datatype': XSD.string,
            'label': 'maximum speed'
        },
        'Autonomia': {
            'predicate': WD.P2073,  # vehicle range
            'datatype': XSD.string,
            'label': 'vehicle range'
        },
        
        # Museum-specific properties
        'TESTO': {
            'predicate': SCHEMA.description,
            'datatype': XSD.string,
            'label': 'description'
        },
        'Piano': {
            'predicate': EX.floor,
            'datatype': XSD.string,
            'label': 'museum floor'
        },
        'Sezione': {
            'predicate': EX.section,
            'datatype': XSD.string,
            'label': 'museum section'
        },
        'Acquisizione': {
            'predicate': SCHEMA.purchaseDate,
            'datatype': XSD.string,
            'label': 'acquisition info'
        },
        
        # Additional technical specs
        'Motore': {
            'predicate': EX.engineDescription,
            'datatype': XSD.string,
            'label': 'engine description'
        },
        'Alimentazione': {
            'predicate': SCHEMA.fuelType,
            'datatype': XSD.string,
            'label': 'fuel type'
        },
        'Cambio': {
            'predicate': SCHEMA.numberOfForwardGears,
            'datatype': XSD.string,
            'label': 'transmission'
        },
        'Trasmissione': {
            'predicate': EX.transmission,
            'datatype': XSD.string,
            'label': 'drivetrain'
        },
        'Trazione': {
            'predicate': EX.drivetrain,
            'datatype': XSD.string,
            'label': 'drive type'
        },
        'Consumo': {
            'predicate': SCHEMA.fuelConsumption,
            'datatype': XSD.string,
            'label': 'fuel consumption'
        },
        'Telaio': {
            'predicate': EX.chassis,
            'datatype': XSD.string,
            'label': 'chassis'
        },
        'Batterie': {
            'predicate': EX.battery,
            'datatype': XSD.string,
            'label': 'battery'
        },
        'Carrozzeria': {
            'predicate': SCHEMA.bodyType,
            'datatype': XSD.string,
            'label': 'body type'
        },
        'Carrozzeria/Designer': {
            'predicate': SCHEMA.manufacturer,
            'datatype': XSD.string,
            'label': 'coachbuilder/designer'
        },
        
        # Racing and history
        'Piloti': {
            'predicate': EX.drivers,
            'datatype': XSD.string,
            'label': 'drivers'
        },
        'Corse ': {
            'predicate': WD.P166,  # award received
            'datatype': XSD.string,
            'label': 'racing achievements'
        },
        
        # Multiple year columns
        'Anno.1': {
            'predicate': EX.acquisitionYear,
            'datatype': XSD.gYear,
            'label': 'acquisition year'
        },
        'Anno.2': {
            'predicate': EX.designYear,
            'datatype': XSD.gYear,
            'label': 'design year'
        }
    }
    
    return mappings

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

def generate_wikidata_knowledge_graph():
    """
    Genera knowledge graph completo usando proprietà Wikidata + Schema.org.
    """
    
    # File di input e output
    museo_file = "data/museo.csv"
    wikidata_file = "data/Wikidata_P.csv"
    output_file = "output/output_wikidata.nt"
    
    print("=== GENERATORE KNOWLEDGE GRAPH CON WIKIDATA ===")
    print(f"File dati: {museo_file}")
    print(f"File Wikidata: {wikidata_file}")
    print(f"Output: {output_file}")
    print()
    
    # Verifica file di input
    if not os.path.exists(museo_file):
        print(f"Errore: File {museo_file} non trovato!")
        return False
    
    # Carica proprietà Wikidata
    wikidata_props = load_wikidata_properties(wikidata_file)
    
    # Crea mappings con Wikidata + Schema.org
    mappings = create_enhanced_mappings(wikidata_props)
    
    print("=== MAPPINGS SEMANTICI ===")
    for col, mapping in mappings.items():
        predicate = mapping['predicate']
        label = mapping.get('label', '')
        if 'wikidata.org' in str(predicate):
            source = "Wikidata"
        elif 'schema.org' in str(predicate):
            source = "Schema.org"
        else:
            source = "Custom"
        print(f"  {col} → {predicate} ({source}: {label})")
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
        
        # Processa OGNI riga
        for idx, row in df_raw.iterrows():
            
            # Crea URI del veicolo (sempre)
            inventario = clean_value(row.get('N. inventario'))
            vehicle_uri = create_vehicle_uri(inventario, idx)
            
            # Aggiungi tipo veicolo (usa Wikidata Q1420 = motor vehicle)
            g.add((vehicle_uri, RDF.type, SCHEMA.Vehicle))
            row_triples = 1
            
            # Processa TUTTE le colonne mappate
            for column in df_raw.columns:
                value = clean_value(row.get(column))
                if not value:
                    continue
                    
                if column in mappings:
                    # Mapping semantico trovato
                    mapping = mappings[column]
                    predicate = mapping['predicate']
                    datatype = mapping['datatype']
                    literal_value = apply_datatype(value, datatype)
                    g.add((vehicle_uri, predicate, literal_value))
                    row_triples += 1
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
        print(f"\n=== RISULTATI KNOWLEDGE GRAPH WIKIDATA ===")
        print(f"Righe processate: {processed_count}/{total_rows} (100%)")
        print(f"Triple generate: {len(g)}")
        print(f"Media triple per veicolo: {len(g) / processed_count:.1f}")
        print(f"File salvato in: {output_file}")
        
        # Statistiche mappings
        mapped_columns = sum(1 for col in df_raw.columns if col in mappings)
        total_columns = len(df_raw.columns)
        
        print(f"\n=== STATISTICHE MAPPINGS ===")
        print(f"Colonne mappate semanticamente: {mapped_columns}/{total_columns}")
        print(f"Proprietà Wikidata usate: {sum(1 for m in mappings.values() if 'wikidata.org' in str(m['predicate']))}")
        print(f"Proprietà Schema.org usate: {sum(1 for m in mappings.values() if 'schema.org' in str(m['predicate']))}")
        print(f"Proprietà custom: {sum(1 for m in mappings.values() if 'example.org' in str(m['predicate']))}")
        
        return True
        
    except Exception as e:
        print(f"Errore durante la generazione: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    generate_wikidata_knowledge_graph()