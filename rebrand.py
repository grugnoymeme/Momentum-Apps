#!/usr/bin/env python3
"""
Script di rebranding da Momentum a NoName
Versione Python - più robusta e cross-platform
"""

import os
import sys
import subprocess
import re
from pathlib import Path

# Mappatura delle sostituzioni (ordine importante)
REPLACEMENTS = [
    ('MOMENTUM', 'NONAME'),
    ('Momentum', 'NoName'),
    ('momentum', 'noname'),
    ('MNTM', 'NNM'),
    ('Mntm', 'Nnm'),
    ('mntm', 'nnm'),
]

# Estensioni di file da escludere (binari)
BINARY_EXTENSIONS = {
    '.pyc', '.so', '.a', '.o', '.bin', '.elf', '.hex',
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.bmp',
    '.dfu', '.pdf', '.zip', '.tar', '.gz', '.tgz'
}

# Directory da escludere
EXCLUDE_DIRS = {
    '.git', 'build', 'dist', '__pycache__', 'node_modules',
    '.venv', 'venv', '.idea', '.vscode'
}

def is_git_repo():
    """Verifica se siamo in una repository git"""
    return os.path.isdir('.git')

def get_current_branch():
    """Ottiene il branch corrente"""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return None

def should_process_file(filepath):
    """Determina se un file deve essere processato"""
    path = Path(filepath)
    
    # Escludi per estensione
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return False
    
    # Escludi per directory
    for parent in path.parents:
        if parent.name in EXCLUDE_DIRS:
            return False
    
    # Escludi questo script stesso
    if path.name in ['rebrand.sh', 'rebrand_python.py', 'tree.txt']:
        return False
    
    return True

def is_binary_file(filepath):
    """Controlla se un file è binario"""
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            # Se ci sono molti byte null, è probabilmente binario
            if b'\x00' in chunk:
                return True
        return False
    except:
        return True

def replace_in_file(filepath):
    """Sostituisce il contenuto in un file"""
    try:
        # Leggi il file
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Controlla se contiene qualche riferimento
        if not any(old.lower() in content.lower() for old, _ in REPLACEMENTS):
            return False
        
        original_content = content
        
        # Applica le sostituzioni
        for old, new in REPLACEMENTS:
            content = content.replace(old, new)
        
        # Se è cambiato qualcosa, scrivi il file
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"  ⚠ Errore con {filepath}: {e}")
        return False

def apply_replacements_to_string(text):
    """Applica le sostituzioni a una stringa (per i nomi di file/directory)"""
    result = text
    for old, new in REPLACEMENTS:
        result = result.replace(old, new)
    return result

def rename_files_and_dirs(root_dir='.'):
    """Rinomina file e directory"""
    renamed = []
    
    # Prima raccogli tutti i path da rinominare (dal più profondo)
    items_to_rename = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        # Salta directory escluse
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        # File
        for filename in filenames:
            old_path = os.path.join(dirpath, filename)
            new_filename = apply_replacements_to_string(filename)
            
            if new_filename != filename:
                new_path = os.path.join(dirpath, new_filename)
                items_to_rename.append(('file', old_path, new_path))
        
        # Directory
        dirname = os.path.basename(dirpath)
        new_dirname = apply_replacements_to_string(dirname)
        
        if new_dirname != dirname and dirname not in EXCLUDE_DIRS:
            parent = os.path.dirname(dirpath)
            new_path = os.path.join(parent, new_dirname)
            items_to_rename.append(('dir', dirpath, new_path))
    
    # Ora rinomina tutto
    for item_type, old_path, new_path in items_to_rename:
        if os.path.exists(old_path) and not os.path.exists(new_path):
            try:
                print(f"Rinominando {item_type}: {old_path} -> {new_path}")
                
                # Prova con git mv prima
                result = subprocess.run(
                    ['git', 'mv', old_path, new_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    # Se git mv fallisce, usa mv normale
                    os.rename(old_path, new_path)
                
                renamed.append((old_path, new_path))
            except Exception as e:
                print(f"  ⚠ Errore rinominando {old_path}: {e}")
    
    return renamed

def find_remaining_references():
    """Cerca riferimenti rimanenti a momentum"""
    count = 0
    examples = []
    
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            
            if not should_process_file(filepath) or is_binary_file(filepath):
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if re.search(r'momentum|mntm', line, re.IGNORECASE):
                            count += 1
                            if len(examples) < 10:
                                examples.append(f"{filepath}:{line_num}: {line.strip()[:100]}")
            except:
                pass
    
    return count, examples

def main():
    print("=" * 50)
    print("NoName Firmware Rebranding Script (Python)")
    print("=" * 50)
    print()
    
    # Verifica git repo
    if not is_git_repo():
        print("❌ ERRORE: Questa non sembra essere una repository git!")
        print("Esegui questo script dalla root del progetto NoName-Firmware")
        return 1
    
    # Mostra branch corrente
    branch = get_current_branch()
    print(f"Branch corrente: {branch}")
    print()
    
    # Conferma
    response = input("Vuoi continuare con il rebranding? (y/n): ").strip().lower()
    if response != 'y':
        print("Operazione annullata.")
        return 0
    
    print()
    print("FASE 1: Backup - Creazione di un commit prima delle modifiche...")
    subprocess.run(['git', 'add', '-A'], check=False)
    subprocess.run(
        ['git', 'commit', '-m', 'Pre-rebranding backup', '--allow-empty'],
        capture_output=True
    )
    print("✓ Backup completato")
    print()
    
    print("FASE 2: Sostituzione del contenuto nei file...")
    print("Cercando file da modificare...")
    
    # Raccogli tutti i file da processare
    files_to_process = []
    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if should_process_file(filepath) and not is_binary_file(filepath):
                files_to_process.append(filepath)
    
    print(f"Trovati {len(files_to_process)} file da processare")
    print()
    
    modified_count = 0
    for i, filepath in enumerate(files_to_process, 1):
        if replace_in_file(filepath):
            print(f"[{i}/{len(files_to_process)}] Modificato: {filepath}")
            modified_count += 1
        
        # Mostra progresso ogni 1000 file
        if i % 1000 == 0:
            print(f"  Progresso: {i}/{len(files_to_process)} file controllati...")
    
    print()
    print(f"✓ Modificati {modified_count} file")
    print()
    
    print("FASE 3: Rinominazione di file e directory...")
    renamed = rename_files_and_dirs()
    print()
    print(f"✓ Rinominati {len(renamed)} elementi")
    print()
    
    print("FASE 4: Verifica finale...")
    print("Cercando eventuali riferimenti rimasti a 'momentum'...")
    remaining_count, examples = find_remaining_references()
    
    if remaining_count > 0:
        print(f"⚠ Trovati ancora {remaining_count} riferimenti a momentum/mntm")
        if examples:
            print("\nEsempi:")
            for example in examples:
                print(f"  {example}")
    else:
        print("✓ Nessun riferimento a momentum trovato!")
    
    print()
    print("=" * 50)
    print("REBRANDING COMPLETATO!")
    print("=" * 50)
    print()
    print("Prossimi passi:")
    print("1. Verifica le modifiche con: git status")
    print("2. Controlla i file modificati con: git diff")
    print("3. Se tutto è ok, fai commit:")
    print("   git add -A && git commit -m 'Rebranding: Momentum -> NoName'")
    print("4. Compila il firmware per verificare che tutto funzioni")
    print()
    print("Se qualcosa è andato storto, puoi tornare indietro con:")
    print("git reset --hard HEAD~1")
    print()
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nOperazione interrotta dall'utente.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERRORE INASPETTATO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
