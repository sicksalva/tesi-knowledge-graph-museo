#!/usr/bin/env python3
"""
Script per processare il file museo.csv e creare museo_cleaned.csv 
con solo le colonne necessarie per la trasformazione RDF.
"""

import pandas as pd
import os

def clean_museo_csv():
    """
    Legge museo.csv e crea museo_cleaned.csv con le colonne selezionate.
    """
    
    # Percorsi dei file
    input_file = "../data/museo.csv"
    output_file = "../data/cleaned_csvs/museo_cleaned.csv"
    
    # Verifica che il file di input esista
    if not os.path.exists(input_file):
        print(f"Errore: File {input_file} non trovato!")
        return
    
    try:
        # Leggi il CSV originale saltando la prima riga (header di raggruppamento)
        print(f"Leggendo {input_file}...")
        df = pd.read_csv(input_file, skiprows=1)
        
        # Stampa info sul dataset originale
        print(f"Dataset originale: {df.shape[0]} righe, {df.shape[1]} colonne")
        print(f"Colonne disponibili: {list(df.columns)}")
        
        # Analizza la completezza delle colonne
        print("\n=== ANALISI COMPLETEZZA COLONNE ===")
        for col in df.columns:
            non_empty = df[col].notna().sum()
            non_empty_non_blank = df[col].fillna('').astype(str).str.strip().ne('').sum()
            percentage = (non_empty_non_blank / len(df)) * 100
            print(f"{col:25}: {non_empty_non_blank:3}/{len(df)} ({percentage:5.1f}%)")
        
        print("\n=== COLONNE PIÙ COMPLETE (>50%) ===")
        complete_cols = []
        for col in df.columns:
            non_empty_non_blank = df[col].fillna('').astype(str).str.strip().ne('').sum()
            percentage = (non_empty_non_blank / len(df)) * 100
            if percentage > 50:
                complete_cols.append((col, percentage))
                print(f"{col:25}: {percentage:5.1f}%")
        
        # Mappa le colonne dal file originale a quelle pulite
        # Aggiorniamo per includere colonne più complete
        column_mapping = {
            'N. inventario': 'Inventario',
            'Marca': 'Marca', 
            'Modello': 'Modello',
            'Anno': 'Anno',
            'Anni di produzione': 'AnniProduzione',
            'Paese': 'Paese',
            'Acquisizione': 'Acquisizione',
            'Tipo di motore': 'TipoMotore',
            'Cilindrata': 'Cilindrata',
            'Potenza': 'Potenza',
            'Velocità': 'Velocita'
        }
        
        # Seleziona solo le colonne che ci interessano
        selected_columns = []
        missing_columns = []
        
        for original_col, clean_col in column_mapping.items():
            if original_col in df.columns:
                selected_columns.append(original_col)
            else:
                missing_columns.append(original_col)
                print(f"Attenzione: Colonna '{original_col}' non trovata!")
        
        if not selected_columns:
            print("Errore: Nessuna colonna valida trovata!")
            return
            
        # Crea il dataframe pulito
        df_cleaned = df[selected_columns].copy()
        
        # Rinomina le colonne
        rename_dict = {orig: clean for orig, clean in column_mapping.items() if orig in selected_columns}
        df_cleaned = df_cleaned.rename(columns=rename_dict)
        
        # Rimuovi righe completamente vuote
        df_cleaned = df_cleaned.dropna(how='all')
        
        # Crea la directory di output se non esiste
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Salva il CSV pulito
        df_cleaned.to_csv(output_file, index=False)
        
        print(f"Dataset pulito salvato: {df_cleaned.shape[0]} righe, {df_cleaned.shape[1]} colonne")
        print(f"File salvato in: {output_file}")
        
        # Mostra un'anteprima dei dati
        print("\nAnteprima dei primi 3 record:")
        print(df_cleaned.head(3).to_string())
        
    except Exception as e:
        print(f"Errore durante il processamento: {str(e)}")

if __name__ == "__main__":
    clean_museo_csv()