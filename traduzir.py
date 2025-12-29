#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tradutor Ren'Py v3.0 - Versão Corrigida
Corrige o problema de concatenação incorreta de strings
"""

import os
import sys
import shutil
import subprocess
import stat
import re

# ---------------- AUTO-INSTALL ---------------- #
def auto_install(pkg):
    try:
        __import__(pkg)
    except ImportError:
        print(f"📦 Instalando {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

auto_install("deep_translator")
auto_install("unrpa")

from deep_translator import GoogleTranslator
import unrpa

# ---------------- CONFIG ---------------- #
ROOT = os.getcwd()
GAME_DIR = os.path.join(ROOT, "game")
BACKUP_DIR = os.path.join(ROOT, "game_backup")
TL_DIR = os.path.join(GAME_DIR, "tl", "portuguese")

# ---------------- BACKUP ---------------- #
def create_backup():
    if os.path.exists(BACKUP_DIR):
        print("⚠ Backup já existe")
        return
    print("📦 Criando backup...")
    shutil.copytree(GAME_DIR, BACKUP_DIR)
    print("✅ Backup criado")

def _force_remove(func, path, _):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def restore_backup():
    if not os.path.exists(BACKUP_DIR):
        print("⚠ Nenhum backup encontrado")
        return
    
    confirm = input("⚠ Restaurar backup? (s/N): ")
    if confirm.lower() != "s":
        return
    
    if os.path.exists(GAME_DIR):
        shutil.rmtree(GAME_DIR, onerror=_force_remove)
    
    shutil.copytree(BACKUP_DIR, GAME_DIR)
    print("♻ Backup restaurado")

# ---------------- UNPROTECT ---------------- #
def unprotect():
    rpas = [f for f in os.listdir(GAME_DIR) if f.endswith(".rpa")]
    if not rpas:
        print("⚠ Nenhum .rpa encontrado")
        return
    
    for rpa in rpas:
        print(f"🔓 Extraindo {rpa}...")
        unrpa.extract(os.path.join(GAME_DIR, rpa), GAME_DIR)
    
    print("✅ Desprotegido")
    
    delete = input("\n🗑️ Deletar arquivos .rpa? (s/N): ")
    if delete.lower() == "s":
        delete_rpa_files()

def delete_rpa_files():
    deleted = []
    for f in os.listdir(GAME_DIR):
        if f.endswith(".rpa"):
            path = os.path.join(GAME_DIR, f)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            os.remove(path)
            deleted.append((f, size_mb))
            print(f"  ✓ {f} ({size_mb:.1f} MB)")
    
    if deleted:
        total = sum(size for _, size in deleted)
        print(f"✅ {len(deleted)} arquivos deletados ({total:.1f} MB)")

# ---------------- TRANSLATION ---------------- #
def translate_line(line, translator):
    """Traduz uma linha preservando a estrutura Ren'Py"""
    stripped = line.strip()
    
    # Ignora linhas de código
    if not stripped or stripped.startswith(("#", "label", "scene", "show", "hide", 
                                           "init", "define", "menu", "screen", 
                                           "python", "image", "return", "if", 
                                           "else", "elif", "with", "play", "stop")):
        return line
    
    # Padrão para encontrar strings com aspas
    # Captura: "texto" ou 'texto', incluindo escapes
    pattern = r'"([^"\\]*(?:\\.[^"\\]*)*)"|\'([^\'\\]*(?:\\.[^\'\\]*)*)\''
    
    def translate_match(match):
        # Pega o texto (grupo 1 = aspas duplas, grupo 2 = aspas simples)
        text = match.group(1) if match.group(1) is not None else match.group(2)
        quote = '"' if match.group(1) is not None else "'"
        
        # Não traduz se vazio ou muito curto
        if not text or len(text.strip()) < 3:
            return match.group(0)
        
        # Não traduz código Ren'Py (variáveis, expressões)
        if "[" in text or "{" in text or text.startswith("\\"):
            return match.group(0)
        
        try:
            translated = translator.translate(text)
            if translated and translated != text:
                # Remove aspas extras que o Google Translate às vezes adiciona
                translated = translated.strip('"\'')
                return f'{quote}{translated}{quote}'
        except Exception as e:
            print(f"  ⚠ Erro: {text[:30]}... -> {e}")
        
        return match.group(0)
    
    # Substitui todas as strings
    return re.sub(pattern, translate_match, line)

def translate_all():
    print("🌍 Traduzindo...")
    translator = GoogleTranslator(source="auto", target="pt")
    
    count = 0
    for root, _, files in os.walk(GAME_DIR):
        if "/tl/" in root or "\\tl\\" in root:
            continue
        
        for f in files:
            if f.endswith(".rpy"):
                src = os.path.join(root, f)
                rel = os.path.relpath(src, GAME_DIR)
                dst = os.path.join(TL_DIR, rel)
                
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                
                print(f"📄 {rel}")
                
                try:
                    with open(src, "r", encoding="utf-8") as fin:
                        lines = fin.readlines()
                    
                    translated = [translate_line(l, translator) for l in lines]
                    
                    with open(dst, "w", encoding="utf-8") as fout:
                        fout.writelines(translated)
                    
                    count += 1
                    print(f"  ✓ OK")
                except Exception as e:
                    print(f"  ✗ Erro: {e}")
    
    print(f"\n✅ {count} arquivos traduzidos")

# ---------------- FIX ERRORS ---------------- #
def fix_translation_errors():
    """Corrige erros de sintaxe nos arquivos traduzidos"""
    if not os.path.exists(TL_DIR):
        print("⚠ Pasta tl/portuguese não existe")
        return
    
    print("🔧 Corrigindo erros...")
    fixed = 0
    
    for root, _, files in os.walk(TL_DIR):
        for f in files:
            if f.endswith(".rpy"):
                path = os.path.join(root, f)
                
                try:
                    with open(path, "r", encoding="utf-8") as fin:
                        content = fin.read()
                    
                    original = content
                    
                    # CRÍTICO: Remove strings concatenadas incorretamente
                    # Padrão: "texto1""texto2" -> "texto1 texto2"
                    content = re.sub(r'("(?:[^"\\]|\\.)*")("(?:[^"\\]|\\.)*")', 
                                   lambda m: m.group(1)[:-1] + ' ' + m.group(2)[1:], 
                                   content)
                    
                    # Remove "None"
                    content = re.sub(r'"None"', '""', content)
                    
                    # Corrige strings vazias soltas
                    content = re.sub(r'^\s*"\s*$', '    ""', content, flags=re.MULTILINE)
                    
                    # Remove aspas soltas
                    lines = content.split('\n')
                    clean_lines = []
                    for line in lines:
                        if line.strip() in ('"', "'"):
                            clean_lines.append(line.replace(line.strip(), '""'))
                        else:
                            clean_lines.append(line)
                    content = '\n'.join(clean_lines)
                    
                    if content != original:
                        with open(path, "w", encoding="utf-8") as fout:
                            fout.write(content)
                        fixed += 1
                        print(f"  ✓ {os.path.relpath(path, TL_DIR)}")
                
                except Exception as e:
                    print(f"  ✗ Erro: {e}")
    
    print(f"✅ {fixed} arquivos corrigidos")

# ---------------- DEEP FIX ---------------- #
def deep_fix():
    """Correção profunda para casos extremos"""
    if not os.path.exists(TL_DIR):
        print("⚠ Pasta tl/portuguese não existe")
        return
    
    print("🔨 Correção profunda...")
    fixed = 0
    
    for root, _, files in os.walk(TL_DIR):
        for f in files:
            if f.endswith(".rpy"):
                path = os.path.join(root, f)
                
                try:
                    with open(path, "r", encoding="utf-8") as fin:
                        lines = fin.readlines()
                    
                    clean_lines = []
                    for line in lines:
                        # Se a linha tem múltiplas strings concatenadas
                        if line.count('""') > 1:
                            # Tenta juntar em uma string única
                            # Remove espaços extras entre strings
                            fixed_line = re.sub(r'"\s*"', ' ', line)
                            clean_lines.append(fixed_line)
                        else:
                            clean_lines.append(line)
                    
                    with open(path, "w", encoding="utf-8") as fout:
                        fout.writelines(clean_lines)
                    
                    fixed += 1
                    print(f"  ✓ {os.path.relpath(path, TL_DIR)}")
                
                except Exception as e:
                    print(f"  ✗ Erro: {e}")
    
    print(f"✅ {fixed} arquivos corrigidos")

# ---------------- ANALYSIS ---------------- #
def detect_structure():
    print("🔍 Analisando...")
    
    rpy = rpyc = rpyc_only = 0
    for root, _, files in os.walk(GAME_DIR):
        if "/tl/" in root or "\\tl\\" in root or "/cache/" in root:
            continue
        
        for f in files:
            if f.endswith(".rpy"):
                rpy += 1
            elif f.endswith(".rpyc"):
                rpyc += 1
                if not os.path.exists(os.path.join(root, f[:-1])):
                    rpyc_only += 1
    
    print(f"  • .rpy: {rpy}")
    print(f"  • .rpyc: {rpyc}")
    print(f"  • .rpyc sem .rpy: {rpyc_only}")
    
    print("\n📋 RECOMENDAÇÃO:")
    if rpy > 0 and rpyc_only == 0:
        print("  ✅ Jogo com fontes")
        print("  → Use opção 4 (completo)")
        print("  → Teste antes de usar opção 5")
    elif rpyc_only > 0:
        print("  🔒 Jogo só com .rpyc")
        print("  → Use opção 4 + 5 obrigatório")
    
    return {'rpy': rpy, 'rpyc_only': rpyc_only}

# ---------------- OVERWRITE ---------------- #
def overwrite_originals():
    if not os.path.exists(TL_DIR):
        print("⚠ Execute a tradução primeiro")
        return
    
    print("\n" + "="*60)
    print("⚡ MODO SOBREESCRITA")
    print("="*60)
    
    structure = detect_structure()
    
    confirm = input("\nConfirmar? (s/N): ")
    if confirm.lower() != "s":
        return
    
    print("\n📄 Copiando arquivos...")
    count = 0
    
    for root, _, files in os.walk(TL_DIR):
        for f in files:
            if f.endswith(".rpy"):
                src = os.path.join(root, f)
                rel = os.path.relpath(src, TL_DIR)
                dst = os.path.join(GAME_DIR, rel)
                
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                count += 1
                print(f"  ✓ {rel}")
                
                # Remove .rpyc para forçar recompilação
                rpyc = dst + "c"
                if os.path.exists(rpyc):
                    try:
                        os.remove(rpyc)
                    except:
                        pass
    
    # Limpa cache
    cache = os.path.join(GAME_DIR, "cache")
    if os.path.exists(cache):
        try:
            shutil.rmtree(cache, onerror=_force_remove)
            print("🧹 Cache removido")
        except:
            pass
    
    print(f"\n✅ {count} arquivos substituídos")
    print("💡 Execute o jogo para recompilar")

# ---------------- MENU ---------------- #
def show_menu():
    print("""
╔══════════════════════════════════════╗
   TRADUTOR REN'PY v3.0 (CORRIGIDO)
╚══════════════════════════════════════╝
1 - 🔓 Desproteger (.rpa)
2 - 🌍 Traduzir
3 - 🔧 Corrigir erros
4 - 📦 Completo (1+2+3)
5 - ⚡ Sobreescrever originais
6 - ♻️  Restaurar backup
7 - 🔍 Analisar estrutura
8 - 🗑️  Deletar .rpa
9 - 🔨 Correção profunda (casos extremos)
0 - ❌ Sair
╚══════════════════════════════════════╝
""")

def main():
    print("🎮 Tradutor Ren'Py v3.0 - Versão Corrigida")
    print(f"📁 {ROOT}\n")
    
    while True:
        show_menu()
        choice = input("Opção: ").strip()
        
        if choice == "0":
            print("👋 Até logo!")
            break
        elif choice == "1":
            create_backup()
            unprotect()
        elif choice == "2":
            create_backup()
            translate_all()
        elif choice == "3":
            fix_translation_errors()
        elif choice == "4":
            create_backup()
            unprotect()
            translate_all()
            fix_translation_errors()
        elif choice == "5":
            create_backup()
            overwrite_originals()
        elif choice == "6":
            restore_backup()
        elif choice == "7":
            detect_structure()
        elif choice == "8":
            if os.path.exists(BACKUP_DIR):
                delete_rpa_files()
            else:
                print("⚠ Crie backup primeiro")
        elif choice == "9":
            deep_fix()
        else:
            print("⚠ Opção inválida")

if __name__ == "__main__":
    main()
