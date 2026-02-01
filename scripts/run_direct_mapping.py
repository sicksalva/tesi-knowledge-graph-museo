#!/usr/bin/env python3
"""
Script per eseguire il mapping diretto da museo.csv usando SPARQL-Anything
"""

import subprocess
import os

def run_direct_mapping():
    """
    Esegue il mapping diretto usando sparql-anything e la query SPARQL.
    """
    
    # File di input e output
    sparql_query = "queries/mappings_direct.sparql"
    output_file = "output/output_direct.nt"
    
    if not os.path.exists(sparql_query):
        print(f"Errore: File query SPARQL {sparql_query} non trovato!")
        return False
    
    try:
        # Comando per eseguire sparql-anything
        cmd = [
            "java", "-jar", "sparql-anything-1.2.0-NIGHTLY-SNAPSHOT.jar",
            "-q", sparql_query,
            "-f", "nt",
            "-o", output_file
        ]
        
        print("Eseguendo mapping diretto con sparql-anything...")
        print(f"Query: {sparql_query}")
        print(f"Output: {output_file}")
        
        # Esegui il comando
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Mapping completato con successo!")
            print(f"File di output: {output_file}")
            
            # Mostra qualche statistica se il file esiste
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                print(f"Triple generate: {len(lines)}")
            
            return True
        else:
            print("❌ Errore durante l'esecuzione:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Errore: sparql-anything-1.2.0-NIGHTLY-SNAPSHOT.jar non trovato!")
        print("Assicurati di avere sparql-anything-1.2.0-NIGHTLY-SNAPSHOT.jar nella directory del progetto.")
        return False
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== MAPPING DIRETTO DA MUSEO.CSV ===")
    run_direct_mapping()