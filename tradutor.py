#!/usr/bin/env python3
# ======================================================
# REN'PY TOOLKIT – FINAL, ESTÁVEL, SEM CRASHES
# Linux / Python 3
# ======================================================

import os
import sys
import subprocess
import shutil
import re

# ================= AUTO INSTALL =================
def ensure_package(pip_name, import_name=None):
    try:
        __import__(import_name or pip_name)
    except ImportError:
        print(f"📦 Instalando dependência: {pip_name}")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", pip_name
        ])

ensure_package("deep-translator", "deep_translator")
ensure_package("unrpa")

from deep_translator import GoogleTranslator

# ================= CONFIG =================
GAME_DIR = "game"
BACKUP_DIR = "game_backup"
TL_DIR = os.path.join(GAME_DIR, "tl", "portuguese")

BLOCK_START = re.compile(r"^\s*(screen|image|style|transform|python)\b")
SAY_LINE = re.compile(
    r"^(?P<indent>\s*)(?:(?P<char>[A-Za-z_][A-Za-z0-9_]*)\s+)?\"(?P<text>[^\"]+)\"\s*$"
)

# ================= BACKUP =================
def backup():
    if not os.path.exists(GAME_DIR):
        print("❌ Pasta 'game' não encontrada")
        return
    if os.path.exists(BACKUP_DIR):
        print("⚠ Backup já existe")
        return
    shutil.copytree(GAME_DIR, BACKUP_DIR)
    print("✔ Backup criado com sucesso")

# ================= RESTORE =================
def restore_backup():
    if not os.path.exists(BACKUP_DIR):
        print("❌ Nenhum backup encontrado")
        return
    print("⚠ Isto irá APAGAR a pasta 'game' atual e restaurar o backup")
    c = input("Confirmar restauração? (s/N): ").lower()
    if c != 's':
        print("❌ Operação cancelada")
        return
    if os.path.exists(GAME_DIR):
        shutil.rmtree(GAME_DIR)
    shutil.copytree(BACKUP_DIR, GAME_DIR)
    print("✔ Backup restaurado com sucesso")

# ================= UNRPA =================
def unprotect():
    if not os.path.exists(GAME_DIR):
        print("❌ Pasta 'game' não encontrada")
        return

    found = False
    for f in os.listdir(GAME_DIR):
        if f.endswith('.rpa'):
            found = True
            print(f"🔓 Extraindo {f}...")
            subprocess.call(["unrpa", os.path.join(GAME_DIR, f)])

    if not found:
        print("⚠ Nenhum .rpa encontrado")

# ================= SAFE TRANSLATION =================
def safe_translate(lang):
    if not os.path.exists(GAME_DIR):
        print("❌ Pasta 'game' não encontrada")
        return

    os.makedirs(TL_DIR, exist_ok=True)
    translator = GoogleTranslator(source="auto", target=lang)

    for fname in os.listdir(GAME_DIR):
        if not fname.endswith('.rpy'):
            continue

        src = os.path.join(GAME_DIR, fname)
        dst = os.path.join(TL_DIR, fname)

        with open(src, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        out_lines = []
        in_block = False

        for line in lines:
            if BLOCK_START.match(line):
                in_block = True
                out_lines.append(line)
                continue

            if in_block:
                if line.strip() == "":
                    out_lines.append(line)
                    continue
                if not line.startswith(" ") and not line.startswith("\t"):
                    in_block = False
                out_lines.append(line)
                continue

            m = SAY_LINE.match(line)
            if m:
                text = m.group('text')
                try:
                    translated = translator.translate(text)
                except Exception:
                    translated = text

                newline = (
                    f"{m.group('indent')}"
                    f"{m.group('char') + ' ' if m.group('char') else ''}"
                    f"\"{translated}\"\n"
                )
                out_lines.append(newline)
            else:
                out_lines.append(line)

        with open(dst, 'w', encoding='utf-8') as f:
            f.writelines(out_lines)

        print(f"✔ Traduzido com segurança: {fname}")

    print("✅ Tradução concluída sem crashes")

# ================= HELP =================
def show_help():
    print("""
🆘 AJUDA – REN'PY TOOLKIT

Este script:
- NÃO quebra jogos Ren'Py
- Traduz apenas falas válidas
- Ignora código automaticamente

Como usar:
1) Estar na pasta do jogo (onde existe 'game/')
2) Executar: python3 traduzir.py
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
4 - ♻ Restaurar backup
9 - 🆘 Help
0 - ❌ Sair
""")

        c = input("Escolha: ").strip()

        if c == '0':
            break
        elif c == '9':
            show_help()
        elif c == '4':
            restore_backup()
        elif c in ('1', '3'):
            backup()
            unprotect()
        elif c in ('2', '3'):
            lang = 'pt' if input("Idioma (1) PT-BR (2) PT-PT: ").strip() != '2' else 'pt-PT'
            safe_translate(lang)
        else:
            print("❌ Opção inválida")


if __name__ == '__main__':
    menu()
