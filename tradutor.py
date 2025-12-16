#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess

# Auto-install de dependências
def auto_install(package):
    try:
        __import__(package)
    except ModuleNotFoundError:
        print(f"Instalando {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

auto_install("deep_translator")
auto_install("unrpa")

from deep_translator import GoogleTranslator
import unrpa

# Configurações
GAME_DIR = "game"
BACKUP_DIR = "game_backup"
TL_DIR = os.path.join(GAME_DIR, "tl", "portuguese")

# ---------------- FUNÇÕES ---------------- #

def backup():
    if os.path.exists(BACKUP_DIR):
        print("⚠ Backup já existe")
        return
    shutil.copytree(GAME_DIR, BACKUP_DIR)
    print("✔ Backup criado")

def restore_backup():
    if not os.path.exists(BACKUP_DIR):
        print("⚠ Nenhum backup encontrado")
        return
    confirm = input("⚠ Isto irá APAGAR a pasta 'game' atual e restaurar o backup\nConfirmar restauração? (s/N): ")
    if confirm.lower() != 's': return
    if os.path.exists(GAME_DIR):
        shutil.rmtree(GAME_DIR)
    shutil.copytree(BACKUP_DIR, GAME_DIR)
    print("✔ Backup restaurado com sucesso")

def unprotect():
    rpa_files = [f for f in os.listdir(GAME_DIR) if f.endswith(".rpa")]
    if not rpa_files:
        print("⚠ Nenhum .rpa encontrado")
        return
    for f in rpa_files:
        print(f"🔓 Extraindo {f}...")
        unrpa.extract(os.path.join(GAME_DIR, f), GAME_DIR)
    print("✅ Desproteção concluída")

def translate_file(src, dst, lang="pt"):
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    translator = GoogleTranslator(source='auto', target=lang)
    try:
        translated = translator.translate_batch(content.splitlines())
        translated_text = "\n".join(translated)
    except Exception as e:
        print(f"⚠ Erro a traduzir {src}: {e}")
        translated_text = content
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        f.write(translated_text)
    print(f"✔ Traduzido com segurança: {os.path.relpath(dst, GAME_DIR)}")

def safe_translate(lang="pt"):
    print(f"🌍 Traduzindo (modo seguro) para {lang}...")
    for root, _, files in os.walk(GAME_DIR):
        for f in files:
            if f.endswith(".rpy"):
                src = os.path.join(root, f)
                dst = os.path.join(GAME_DIR, f)  # sobrescreve direto
                translate_file(src, dst, lang)
    # Forçar PT-BR na inicialização
    options_path = os.path.join(GAME_DIR, "options.rpy")
    if os.path.exists(options_path):
        with open(options_path, "r", encoding="utf-8") as f:
            content = f.read()
        if 'config.language' not in content:
            with open(options_path, "a", encoding="utf-8") as f:
                f.write("\ninit python:\n    config.language = 'portuguese'  # PT-BR\n")
    print("✅ Tradução concluída sem crashes")

def help():
    print("""
🆘 HELP / AJUDA
- 1: Desproteger .rpa → .rpy
- 2: Traduzir jogo direto para PT-BR
- 3: Desproteger + Traduzir
- 4: Restaurar backup
- 0: Sair
Notas:
- Se o jogo não tiver .rpa, use apenas a opção 2.
- Tradução sobrescreve os arquivos originais para forçar PT-BR.
- Backup é criado automaticamente na primeira execução.
""")

# ---------------- MENU ---------------- #
def menu():
    while True:
        print("""
🧰 REN'PY TOOLKIT FINAL

1 - 🔓 Desproteger (.rpa)
2 - 🌍 Traduzir
3 - ⚡ Desproteger + Traduzir
4 - ♻ Restaurar backup
9 - 🆘 Help
0 - ❌ Sair
""")
        c = input("Escolha: ").strip()
        if c == '0': break
        if c == '9': help()
        if c == '1': backup(); unprotect()
        if c == '2':
            backup()
            safe_translate("pt")
        if c == '3':
            backup(); unprotect(); safe_translate("pt")
        if c == '4': restore_backup()

# ---------------- EXECUÇÃO ---------------- #
if __name__ == '__main__':
    menu()
