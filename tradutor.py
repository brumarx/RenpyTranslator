#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
import re

# ---------------- AUTO-INSTALL ---------------- #
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

# ---------------- CONFIGURAÇÕES ---------------- #
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

# ---------------- TRADUÇÃO INTELIGENTE ---------------- #
def intelligent_translate_line(line, translator):
    """
    Traduz apenas strings/dialog de forma segura.
    Ignora:
    - Linhas de código Python ou Ren'Py complexas
    - f-strings e renpy.notify(f"...")
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return line

    # Ignorar linhas que parecem código Python/Ren'Py complexo
    ignore_keywords = ["init", "define", "label", "class", "def", "store", "persistent", 
                       "config.", "renpy.", "build.", "return", "import", "from", "screen", "menu"]
    if any(stripped.startswith(k) for k in ignore_keywords):
        return line

    # Ignorar f-strings
    if 'f"' in line or "f'" in line:
        return line

    # Regex para detectar strings entre aspas
    text_match = re.findall(r'"(.*?)"|\'(.*?)\'', line)
    if text_match:
        new_line = line
        for m in text_match:
            original_text = m[0] or m[1]
            if original_text.strip():
                try:
                    translated_text = translator.translate(original_text)
                except Exception:
                    translated_text = original_text
                new_line = new_line.replace(f'"{original_text}"', f'"{translated_text}"')
                new_line = new_line.replace(f"'{original_text}'", f"'{translated_text}'")
        return new_line

    return line

def translate_file(src, lang="pt", overwrite_original=False):
    os.makedirs(TL_DIR, exist_ok=True)
    dst_lang = os.path.join(TL_DIR, os.path.relpath(src, GAME_DIR))
    dst_original = src if overwrite_original else None

    with open(src, "r", encoding="utf-8") as f:
        lines = f.readlines()

    translator = GoogleTranslator(source='auto', target=lang)
    new_lines = []
    for line in lines:
        try:
            new_lines.append(intelligent_translate_line(line, translator))
        except Exception as e:
            print(f"⚠ Erro na linha: {line.strip()} | {e}")
            new_lines.append(line)

    # Salva sobre original se necessário
    if overwrite_original:
        with open(dst_original, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"✔ Traduzido sobre original: {os.path.relpath(dst_original, GAME_DIR)}")

    # Salva na pasta de idioma
    os.makedirs(os.path.dirname(dst_lang), exist_ok=True)
    with open(dst_lang, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✔ Traduzido na pasta de idioma: {os.path.relpath(dst_lang, GAME_DIR)}")

def safe_translate(lang="pt", overwrite_original=False):
    print(f"🌍 Traduzindo (modo seguro) para {lang}...")
    for root, _, files in os.walk(GAME_DIR):
        for f in files:
            if f.endswith(".rpy"):
                src = os.path.join(root, f)
                translate_file(src, lang, overwrite_original)
    print("✅ Tradução concluída sem crashes")

# ---------------- MENU ---------------- #
def help():
    print("""
🆘 HELP / AJUDA
- 1: Desproteger .rpa → .rpy
- 2: Traduzir jogo direto para PT-BR (cria tl/portuguese/)
- 3: Desproteger + Traduzir (cria tl/portuguese/)
- 4: SOBREESCREVER os arquivos originais (bom para jogos que não aceitam tradução)
- 0: Sair
Notas:
- Backup é criado automaticamente na primeira execução.
- Tradução substitui arquivos originais se escolher opção 4.
- Sistema traduz apenas strings/dialog, ignorando código crítico e f-strings.
""")

def menu():
    while True:
        print("""
🧰 REN'PY TOOLKIT FINAL

1 - 🔓 Desproteger (.rpa)
2 - 🌍 Traduzir (cria tl/portuguese/)
3 - ⚡ Desproteger + Traduzir
4 - ⚡ SOBREESCREVER arquivos originais
9 - 🆘 Help
0 - ❌ Sair
""")
        c = input("Escolha: ").strip()
        if c == '0': break
        if c == '9': help()
        if c == '1': backup(); unprotect()
        if c == '2': backup(); safe_translate("pt", overwrite_original=False)
        if c == '3': backup(); unprotect(); safe_translate("pt", overwrite_original=False)
        if c == '4': backup(); safe_translate("pt", overwrite_original=True)

# ---------------- EXECUÇÃO ---------------- #
if __name__ == '__main__':
    menu()
