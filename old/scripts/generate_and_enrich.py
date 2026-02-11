#!/usr/bin/env python3
"""
Script per generare il knowledge graph completo dal museo.csv aggiornato
e applicare l'arricchimento semantico automatico.
"""

import os
import sys
import subprocess

def run_kg_generation():
    """Esegue la generazione del knowledge graph di base."""
    print("=== STEP 1: GENERAZIONE KNOWLEDGE GRAPH ===")
    
    kg_script = "scripts/generate_kg_dual_mappings.py"
    
    if not os.path.exists(kg_script):
        print(f"Errore: Script {kg_script} non trovato!")
        return False
    
    try:
        # Esegui lo script di generazione KG
        result = subprocess.run([sys.executable, kg_script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Knowledge graph generato con successo!")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"Errore nella generazione KG: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Errore nell'esecuzione: {e}")
        return False

def run_automatic_enrichment():
    """Esegue l'arricchimento semantico automatico."""
    print("\n=== STEP 2: ARRICCHIMENTO SEMANTICO AUTOMATICO ===")
    
    enrichment_script = "scripts/automatic_semantic_enrichment.py"
    
    if not os.path.exists(enrichment_script):
        print(f"Errore: Script {enrichment_script} non trovato!")
        return False
    
    try:
        # Esegui lo script di arricchimento automatico
        result = subprocess.run([sys.executable, enrichment_script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Arricchimento semantico automatico completato!")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"Errore nell'arricchimento: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Errore nell'esecuzione: {e}")
        return False

def verify_input_files():
    """Verifica che i file necessari esistano."""
    required_files = [
        "data/museo.csv",
        "scripts/generate_kg_dual_mappings.py",
        "scripts/automatic_semantic_enrichment.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("Errore: File mancanti:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    return True

def main():
    """Processo principale."""
    print("=== GENERAZIONE KG + ARRICCHIMENTO SEMANTICO AUTOMATICO ===")
    print()
    
    # Verifica file necessari
    if not verify_input_files():
        return False
    
    # Controlla che esistano i dati aggiornati
    museo_file = "data/museo.csv"
    try:
        import pandas as pd
        df = pd.read_csv(museo_file)
        print(f"Trovato museo.csv con {len(df)} righe")
    except Exception as e:
        print(f"Errore nella lettura di {museo_file}: {e}")
        return False
    
    # Step 1: Genera knowledge graph base
    if not run_kg_generation():
        print("Fallimento nello Step 1, interrompo il processo.")
        return False
    
    # Step 2: Arricchimento semantico automatico
    if not run_automatic_enrichment():
        print("Fallimento nello Step 2, interrompo il processo.")
        return False
    
    # Riepilogo finale
    print("\n=== PROCESSO COMPLETATO ===")
    print("File generati:")
    
    output_files = [
        "output/output_dual_mappings.nt",
        "output/output_semantic_enriched_auto.nt"
    ]
    
    for file_path in output_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {file_path} ({size:,} bytes)")
        else:
            print(f"  ✗ {file_path} (non trovato)")
    
    print()
    print("Il knowledge graph è stato generato e arricchito semanticamente")
    print("usando le API di Wikidata per il linking automatico delle entità!")
    
    return True

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 Processo completato con successo!")
        sys.exit(0)
    else:
        print("\n❌ Processo fallito!")
        sys.exit(1)