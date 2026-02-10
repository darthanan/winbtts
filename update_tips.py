import os
import google.generativeai as genai

# Configura o Gemini com sua chave secreta
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-pro')

# O Prompt que eu (IA) vou processar todo dia
prompt = """
Aja como um analista de apostas. Verifique os jogos de futebol de hoje. 
Identifique 2 jogos com alto potencial de 'Vitória + Ambos Marcam'.
Retorne APENAS o código HTML (os blocos dos cards) com:
1. Nomes dos times e logos da football-data.org.
2. Odds simuladas para Bet365, BetMGM e Betano.
3. Breve análise tática e estatística.
Use o formato do código anterior.
"""

response = model.generate_content(prompt)

# O script então abre o seu index.html e injeta o que eu respondi
with open("index.html", "r") as f:
    conteudo = f.read()

# Lógica simples de substituição para atualizar a lista de jogos
# (Você marcaria no HTML onde os jogos entram e o Python substituiria)
novo_html = conteudo.replace("", response.text)

with open("index.html", "w") as f:
    f.write(novo_html)
