#!/usr/bin/env python3
"""
Test di estrazione entità con modalità oneshot (con esempio).
"""

import yaml
import json
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
from datetime import datetime
import time
import sys

def load_config():
    """Carica configurazione oneshot."""
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def setup_model(config):
    """Inizializza modello su GPU."""
    model_name = config['model']['name']              # Nome modello (Qwen/Qwen3-0.6B = 600M parametri)
    print(f"Caricando modello {model_name}...")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,                   # Usa FP16 per risparmiare memoria GPU
        device_map="auto"                            # Caricamento automatico su GPU disponibile
    )
    
    print(f"Modello caricato su: {model.device}")
    return tokenizer, model

def generate_response(tokenizer, model, prompt, config):
    """Genera risposta dal modello."""
    # Parametri di generazione dal config
    max_tokens = config['model']['max_tokens']        # Numero massimo token da generare (~200-250 parole)
    temperature = config['model']['temperature']      # Controllo creatività: 0.0=deterministico, 1.0=creativo
    
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,           # Limite output (300 token)
            temperature=temperature,             # Controllo casualità (0.2 = poco creativo, ideale per JSON)
            do_sample=True,                      # Abilita campionamento probabilistico (usa temperature)
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.1               # Penalizza ripetizioni (1.0=nessuna, 1.1=leggera)
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Rimuovi il prompt originale dalla risposta
    prompt_text = tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)
    model_output = response[len(prompt_text):].strip()
    
    return model_output

def extract_json_from_response(response_text):
    """Estrae JSON dalla risposta del modello."""
    try:
        # Cerca il JSON nella risposta
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    return None

def build_oneshot_prompt(config, description):
    """Costruisce prompt con esempio per modalità oneshot."""
    system_prompt = config['system_prompt']
    example_input = config['example_input']
    example_output = config['example_output']
    user_prompt = config['user_prompt'].format(description=description)
    
    full_prompt = f"""{system_prompt}

Ecco un esempio di come analizzare:

{example_input}

{example_output}

Ora analizza questo nuovo veicolo:

{user_prompt}"""
    
    return full_prompt

def process_museum_data(config, max_samples=None):
    """Processa dati del museo con modalità oneshot."""
    print("\n=== PROCESSING MUSEUM DATA (ONESHOT) ===")
    
    # Carica dati museo
    museo_file = config['museum']['file_name']
    df = pd.read_csv(museo_file, skiprows=1)
    
    id_col = config['museum']['id_column_name']
    text_col = config['museum']['text_column_name']
    
    print(f"Dataset caricato: {len(df)} veicoli")
    if max_samples is None:
        print("Processando TUTTO il dataset...")
    else:
        print(f"Processando primi {max_samples} veicoli...")
    
    # Setup modello
    tokenizer, model = setup_model(config)
    
    results = []
    processed = 0
    skipped = 0
    
    print(f"Dataset caricato: {len(df)} veicoli")
    
    for idx, row in df.iterrows():
        if max_samples is not None and processed >= max_samples:
            break
            
        vehicle_id = row.get(id_col)
        description = row.get(text_col)
        
        if pd.isna(description) or not str(description).strip():
            skipped += 1
            print(f"Riga {idx} saltata: ID={vehicle_id}, descrizione vuota")
            continue
        
        print(f"Processando veicolo {processed+1} (ID: {vehicle_id})")
        
        # Crea prompt oneshot
        full_prompt = build_oneshot_prompt(config, description)
        
        # Genera risposta
        response = generate_response(tokenizer, model, full_prompt, config)
        
        # Estrai JSON
        extracted_data = extract_json_from_response(response)
        
        result = {
            'vehicle_id': vehicle_id,
            'description': description[:200] + "...",
            'raw_response': response,
            'extracted_entities': extracted_data,
            'success': extracted_data is not None
        }
        
        results.append(result)
        processed += 1
        
        if extracted_data:
            print(f"Veicolo processato {processed} - Successo")
        else:
            print(f"Veicolo processato {processed} - Fallito")
    
    print(f"\nProcessamento completato: {processed} veicoli processati, {skipped} saltati")
    return results

def save_results(results, config):
    """Salva risultati in JSON."""
    output_file = config['output']['file_name']
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'mode': 'oneshot',
        'total_processed': len(results),
        'successful_extractions': sum(1 for r in results if r['success']),
        'success_rate': sum(1 for r in results if r['success']) / len(results) if results else 0,
        'results': results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"\nRisultati salvati in: {output_file}")
    print(f"Successo: {summary['successful_extractions']}/{summary['total_processed']} "
          f"({summary['success_rate']:.1%})")

def main():
    """Funzione principale."""
    print("=== TEST ESTRAZIONE ENTITÀ - ONESHOT ===")
    
    # Verifica GPU
    if not torch.cuda.is_available():
        print("ERRORE: CUDA non disponibile! Installa PyTorch con supporto CUDA.")
        return
    
    print(f"GPU disponibile: {torch.cuda.get_device_name()}")
    
    # Carica config
    config = load_config()
    
    # Processa dati
    results = process_museum_data(config, max_samples=None)
    
    # Salva risultati
    save_results(results, config)

if __name__ == "__main__":
    main()