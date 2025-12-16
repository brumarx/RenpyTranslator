# RenpyTranslator
Renpy Translator PT

Feito para linux

Como usar (resumo rápido)
python3 -m venv venv
source venv/bin/activate
pip install deep-translator unrpa
python3 renpy_toolkit_safe.py

Escolha:

3 - Desproteger + Traduzir


📌 Como usar (do zero, sem dor de cabeça)

Dentro da pasta do jogo (onde existe game/):

python3 traduzir.py

📂 Estrutura final correta (Ren’Py)

Depois da tradução, você terá:

game/
 ├─ script.rpy
 ├─ images.rpy
 ├─ ...
 └─ tl/
     └─ portuguese/
         ├─ script.rpy   ✅ traduzido
         ├─ events.rpy   ✅ traduzido
