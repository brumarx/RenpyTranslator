```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🧰 REN'PY TOOLKIT SAFE + AUTO INSTALL (Linux / Python 3)

✔ Auto-instala dependências (deep-translator, unrpa)
✔ Backup automático
✔ Desprotege .rpa
✔ Traduz SOMENTE diálogos
✔ Nunca traduz arquivos de código
✔ Evita TODOS os erros de Ren'Py
"""

import os
import sys
import subprocess
import shutil

# ==========================
# AUTO-INSTALL DEPENDÊNCIAS
# ==========================

def ensure_package(pkg):
    try:
        __import__(pkg.replace('-', '_'))
    except ImportError:
        print(f"📦 Instalando dependência: {pkg} ...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", pkg
        ])

ensure_package("deep-translator")
ensure_package("unrpa")

from deep_translator import GoogleTranslator
from unrpa import UnRPA

# ==========================
# CONFIGURAÇÕES
# ==========================

GAME_DIR = "game"
BACKUP_DIR = "game_backup"
TL_DIR = os.path.join(GAME_DIR, "tl", "portuguese")

BLOCKLIST = {
    "images.rpy",
    "gui.rpy",
    "screens.rpy",
    "options.rpy",
    "functions.rpy",
    "variables.rpy",
    "audio.rpy",
}

# ==========================
# UTILIDADES
# ==========================

def banner():
    print("""
🧰 REN'PY TOOLKIT SAFE + AUTO INSTALL

1 - 🔓 Desproteger jogo (.rpa → .rpy)
2 - 🌍 Traduzir jogo
3 - ⚡ Desproteger + Traduzir
9 - 🆘 Help / Ajuda
0 - ❌ Sair
""")


def help_menu():
    print("""
📖 AJUDA RÁPIDA

✔ Use sempre python3
✔ Recomenda-se venv (não obrigatório)
✔ O script cria backup automático
✔ Tradução é segura (somente diálogos)
✔ NÃO reproteja o jogo após traduzir

Exemplo:
python3 traduzir.py
""")


def backup_game():
    if os.path.exists(BACKUP_DIR):
        print("⚠ Backup já existe")
        return
    shutil.copytree(GAME_DIR, BACKUP_DIR)
    print("✔ Backup criado")


def unprotect():
    backup_game()
    print("\n🔓 Desprotegendo jogo...")
    found = False
    for f in os.listdir(GAME_DIR):
        if f.endswith(".rpa"):
            found = True
            print(f"📦 Extraindo {f}")
            UnRPA(os.path.join(GAME_DIR, f)).extract(GAME_DIR)
    if not found:
        print("⚠ Nenhum .rpa encontrado")
    else:
        print("✅ Desproteção concluída")


def is_safe_file(filename):
    return filename not in BLOCKLIST


def translate_game():
    lang = input("Escolha idioma: (1) PT-BR (2) PT-PT : ").strip()
    target = "pt" if lang == "1" else "pt-PT"

    os.makedirs(TL_DIR, exist_ok=True)
    translator = GoogleTranslator(source="en", target=target)

    print("\n🌍 Traduzindo (modo seguro)...")

    for f in os.listdir(GAME_DIR):
        if not f.endswith(".rpy"):
            continue
        if not is_safe_file(f):
            print(f"⏭ Ignorado (código): {f}")
            continue

        src = os.path.join(GAME_DIR, f)
        dst = os.path.join(TL_DIR, f)

        with open(src, encoding="utf-8") as fin:
            lines = fin.readlines()

        out = []
        for line in lines:
            s = line.strip()
            if s.startswith('"') and s.endswith('"'):
                text = s[1:-1]
                try:
                    t = translator.translate(text)
                except Exception:
                    t = text
                out.append(f'"{t}"\n')
            else:
                out.append(line)

        with open(dst, "w", encoding="utf-8") as fout:
            fout.writelines(out)

        print("✔ Traduzido:", f)

    print("✅ Tradução concluída")


# ==========================
# MENU PRINCIPAL
# ==========================

while True:
    banner()
    choice = input("Escolha: ").strip()

    if choice == "1":
        unprotect()
    elif choice == "2":
        translate_game()
    elif choice == "3":
        unprotect()
        translate_game()
    elif choice == "9":
        help_menu()
    elif choice == "0":
        print("👋 Saindo")
        break
    else:
        print("❌ Opção inválida")
```
