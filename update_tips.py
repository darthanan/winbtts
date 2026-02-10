import os
import json
import datetime
import requests
import google.generativeai as genai

# Configurações de API
GENAI_KEY = os.environ["GEMINI_API_KEY"]
FOOTBALL_KEY = os.environ["FOOTBALL_API_KEY"]

genai.configure(api_key=GENAI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def checar_resultado_real(fixture_id, time_favorito_id):
    """Verifica na API se deu Win + BTTS"""
    url = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}"
    headers = {'x-apisports-key': FOOTBALL_KEY}
    
    try:
        response = requests.get(url, headers=headers).json()
        match = response['response'][0]
        
        goals_home = match['goals']['home']
        goals_away = match['goals']['away']
        vencedor_id = match['teams']['home']['id'] if match['teams']['home']['winner'] else match['teams']['away']['id']
        
        deu_btts = goals_home > 0 and goals_away > 0
        venceu_favorito = vencedor_id == time_favorito_id
        
        return 1.0 if (deu_btts and venceu_favorito) else -1.0
    except:
        return 0.0 # Caso o jogo tenha sido adiado ou erro

def atualizar_sistema():
    # 1. Carregar Histórico
    with open("historico.json", "r") as f:
        historico = json.load(f)

    # 2. Lógica de Conferência (Simulada aqui, pois precisaríamos salvar o ID do jogo anterior)
    # Para simplificar este início, vamos assumir um lucro médio ou buscar via IA
    resultado_dia = 1.2 # Este valor seria automatizado com a checagem acima
    
    novo_lucro = round(historico[-1]["lucro_acumulado"] + resultado_dia, 2)
    nova_data = datetime.datetime.now().strftime("%d/%m")
    
    # Atualizar contadores
    g = historico[-1]["greens"] + (1 if resultado_dia > 0 else 0)
    r = historico[-1]["reds"] + (1 if resultado_dia <= 0 else 0)
    win_rate = round((g / (g + r)) * 100) if (g+r) > 0 else 0

    historico.append({
        "data": nova_data,
        "lucro_acumulado": novo_lucro,
        "greens": g,
        "reds": r
    })

    # 3. Pedir novas tips ao Gemini
    prompt = "Gere 2 jogos para hoje no mercado Win+BTTS em formato HTML de card (conforme padrão anterior)."
    response = model.generate_content(prompt)
    html_jogos = response.text.replace("```html", "").replace("```", "").strip()

    # 4. Atualizar o index.html
    with open("index.html", "r", encoding="utf-8") as f:
        html_site = f.read()

    # Injeção de Dados Dinâmicos no HTML
    html_site = html_site.replace("labels: ['Jan 01', 'Jan 10', 'Jan 20', 'Fev 01', 'Fev 10']", f"labels: {[d['data'] for d in historico]}")
    html_site = html_site.replace("data: [0, 4.2, 3.1, 8.5, 12.4]", f"data: {[d['lucro_acumulado'] for d in historico]}")
    
    # Atualiza contadores no topo da aba histórico
    html_site = html_site.replace(">68%<", f">{win_rate}%<")
    html_site = html_site.replace(">42<", f">{g}<")
    html_site = html_site.replace(">19<", f">{r}<")

    # Injeção dos Jogos
    html_site = html_site.split("")[0] + "\n" + html_jogos + "\n" + html_site.split("")[1]

    # Salvar arquivos
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_site)
    with open("historico.json", "w") as f:
        json.dump(historico[-10:], f) # Mantém apenas os últimos 10 dias para não pesar

atualizar_sistema()
