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

def intelligent_translate_line(line, translator):
    """
    Decide se a linha deve ser traduzida ou mantida.
    Mantém comandos Ren'Py, mas traduz qualquer string/dialog.
    """
    stripped = line.strip()
    if not stripped:
        return line  # linha vazia
    # Ignorar linhas de comentário
    if stripped.startswith("#"):
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
    # Tentar traduzir linhas de label, jump, menu, choice? (opcional)
    # Por enquanto mantemos o resto intacto
    return line

def translate_file(src, dst, lang="pt"):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
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
    with open(dst, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"✔ Traduzido com segurança: {os.path.relpath(dst, GAME_DIR)}")

def safe_translate(lang="pt"):
    print(f"🌍 Traduzindo (modo seguro) para {lang}...")
    for root, _, files in os.walk(GAME_DIR):
        for f in files:
            if f.endswith(".rpy"):
                src = os.path.join(root, f)
                # Se o jogo não tiver suporte a idiomas, grava sobre original
                if "tl" in root.lower():
                    dst = src
                else:
                    rel_path = os.path.relpath(src, GAME_DIR)
                    dst = os.path.join(TL_DIR, rel_path)
                translate_file(src, dst, lang)
    # Forçar PT-BR no options.rpy
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
- Backup é criado automaticamente na primeira execução.
- Tradução cria tl/portuguese/ se não existir.
- Sistema traduz apenas strings/dialog de forma inteligente, mantendo comandos Ren'Py.
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
        if c == '2': backup(); safe_translate("pt")
        if c == '3': backup(); unprotect(); safe_translate("pt")
        if c == '4': restore_backup()

# ---------------- EXECUÇÃO ---------------- #
if __name__ == '__main__':
    menu()
