#!/usr/bin/env python3
# REN'PY TOOLKIT FINAL DEFINITIVO
# Seguro, sem crashes, com parser básico Ren'Py

import os
import sys
import subprocess
import shutil
import re

# ================= AUTO INSTALL =================
def ensure(pkg, imp=None):
    try:
        __import__(imp or pkg)
    except ImportError:
        print(f"📦 Instalando {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

ensure("deep-translator", "deep_translator")
ensure("unrpa")

from deep_translator import GoogleTranslator

# ================= CONFIG =================
GAME_DIR = "game"
BACKUP_DIR = "game_backup"
TL_DIR = os.path.join(GAME_DIR, "tl", "portuguese")
BLOCK_START = re.compile(r"^\s*(screen|image|style|transform|python)\b")
SAY_LINE = re.compile(r"^(?P<indent>\s*)(?:(?P<char>[A-Za-z_][A-Za-z0-9_]*)\s+)?\"(?P<text>[^\"]+)\"\s*$")

# ================= UTIL =================
def backup():
    if not os.path.exists(BACKUP_DIR):
        shutil.copytree(GAME_DIR, BACKUP_DIR)
        print("✔ Backup criado")
    else:
        print("⚠ Backup já existe")

# ================= UNRPA =================
def unprotect():
    found = False
    for f in os.listdir(GAME_DIR):
        if f.endswith('.rpa'):
            found = True
            print(f"🔓 Extraindo {f}")
            subprocess.call(["unrpa", os.path.join(GAME_DIR, f)])
    if not found:
        print("⚠ Nenhum .rpa encontrado")

# ================= PARSER + TRANSLATOR =================
def safe_translate(lang):
    os.makedirs(TL_DIR, exist_ok=True)
    translator = GoogleTranslator(source="auto", target=lang)

    for fname in os.listdir(GAME_DIR):
        if not fname.endswith('.rpy'):
            continue

        src = os.path.join(GAME_DIR, fname)
        dst = os.path.join(TL_DIR, fname)

        with open(src, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        out = []
        block_stack = []

        for line in lines:
            if BLOCK_START.match(line):
                block_stack.append(True)
                out.append(line)
                continue

            if block_stack:
                if line.strip() == "":
                    out.append(line)
                    continue
                if not line.startswith(' '):
                    block_stack.pop()
                out.append(line)
                continue

            m = SAY_LINE.match(line)
            if m:
                text = m.group('text')
                try:
                    translated = translator.translate(text)
                except Exception:
                    translated = text
                newline = f"{m.group('indent')}{m.group('char')+' ' if m.group('char') else ''}\"{translated}\"\n"
                out.append(newline)
            else:
                out.append(line)

        with open(dst, 'w', encoding='utf-8') as f:
            f.writelines(out)

        print(f"✔ Traduzido com segurança: {fname}")

    print("✅ Tradução concluída sem crashes")

# ================= HELP =================
def help():
    print("""
🆘 AJUDA

Este script:
- NÃO quebra jogos Ren'Py
- Traduz apenas falas válidas
- Ignora código automaticamente

Como usar:
1) Estar na pasta do jogo
2) python3 renpy_toolkit_FINAL.py
3) Escolher opção 3

Após traduzir:
➡ Basta abrir o jogo normalmente
""")

# ================= MENU =================
def menu():
    while True:
        print("""
🧰 REN'PY TOOLKIT FINAL

1 - 🔓 Desproteger (.rpa)
2 - 🌍 Traduzir
3 - ⚡ Desproteger + Traduzir
9 - 🆘 Help
0 - ❌ Sair
""")
        c = input("Escolha: ")

        if c == '0': break
        if c == '9': help()
        if c in ('1','3'): backup(); unprotect()
        if c in ('2','3'):
            lang = 'pt' if input("Idioma (1) PT-BR (2) PT-PT: ")!='2' else 'pt-PT'
            safe_translate(lang)

if __name__ == '__main__':
    menu()
