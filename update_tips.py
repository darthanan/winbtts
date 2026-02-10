import os
import json
import datetime
import requests
import google.generativeai as genai
import re

# 1. Configurações de Conectividade
GENAI_KEY = os.environ.get("GEMINI_API_KEY")
FOOTBALL_KEY = os.environ.get("FOOTBALL_API_KEY")

genai.configure(api_key=GENAI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def conferir_resultados_ontem():
    """Lê o HTML, busca os IDs e valida o Win+BTTS na API-Football"""
    try:
        if not os.path.exists("index.html"): return 0
        with open("index.html", "r", encoding="utf-8") as f:
            html_antigo = f.read()
        
        # Busca IDs ocultos nos atributos data-fixture e data-fav
        fixtures = re.findall(r'data-fixture="(\d+)"', html_antigo)
        favoritos = re.findall(r'data-fav="(\d+)"', html_antigo)
        
        lucro_total = 0
        headers = {'x-apisports-key': FOOTBALL_KEY}

        for i in range(len(fixtures)):
            url = f"https://v3.football.api-sports.io/fixtures?id={fixtures[i]}"
            res = requests.get(url, headers=headers).json()
            
            if res.get('response'):
                match = res['response'][0]
                if match['fixture']['status']['short'] == 'FT':
                    g_home = match['goals']['home']
                    g_away = match['goals']['away']
                    
                    vencedor_id = None
                    if match['teams']['home']['winner']: vencedor_id = match['teams']['home']['id']
                    elif match['teams']['away']['winner']: vencedor_id = match['teams']['away']['id']

                    # Regra: Vitória do favorito + Ambos Marcam
                    if (g_home > 0 and g_away > 0) and (str(vencedor_id) == favoritos[i]):
                        lucro_total += 1.5
                    else:
                        lucro_total -= 1.0
        return lucro_total
    except Exception as e:
        print(f"Erro ao conferir: {e}")
        return 0

def gerar_novas_tips():
    """Solicita ao Gemini o consenso com links REAIS para as casas"""
    prompt = """
    Aja como um analista focado no consenso entre 'Alex Keble' e 'The Goal King'.
    Gere 2 cards HTML para o mercado 'Vitória do Favorito + Ambos Marcam'.
    
    ESTRUTURA OBRIGATÓRIA DO CARD:
    1. O container principal deve ter: <div class="card" data-fixture="ID_DA_API" data-fav="ID_DO_TIME">.
    2. AS ODDS DEVEM SER LINKS CLICÁVEIS:
       Use EXATAMENTE este formato para os links:
       <a href="URL_DA_CASA" target="_blank" rel="noopener" class="block bg-slate-800 p-3 rounded-lg border border-transparent hover:border-emerald-500/50 transition-all cursor-pointer no-underline text-white mb-2">
          <span class="text-xs text-slate-400 block">NOME_DA_CASA</span>
          <span class="font-bold text-lg">ODD_VALOR</span>
       </a>

    URLs DAS CASAS:
    - Bet365: https://www.bet365.com
    - BetMGM: https://sports.betmgm.com
    - Betano: https://br.betano.com

    3. No texto, cite a tática (Keble) e a estatística (Goal King).
    4. Retorne APENAS o HTML puro, sem blocos de código markdown.
    """
    response = model.generate_content(prompt)
    return response.text.replace("```html", "").replace("```", "").strip()

def atualizar_tudo():
    lucro_dia = conferir_resultados_ontem()

    if not os.path.exists("historico.json"):
        historico = [{"data": "Início", "lucro_acumulado": 0, "greens": 0, "reds": 0}]
    else:
        with open("historico.json", "r") as f:
            historico = json.load(f)
    
    ultimo = historico[-1]
    novo_acumulado = round(ultimo["lucro_acumulado"] + lucro_dia, 2)
    g = ultimo["greens"] + (1 if lucro_dia > 0 else 0)
    r = ultimo["reds"] + (1 if lucro_dia < 0 else 0)
    win_rate = round((g / (g + r)) * 100) if (g+r) > 0 else 0
    
    historico.append({
        "data": datetime.datetime.now().strftime("%d/%m"),
        "lucro_acumulado": novo_acumulado, "greens": g, "reds": r
    })

    html_novos_jogos = gerar_novas_tips()

    with open("index.html", "r", encoding="utf-8") as f:
        site = f.read()

    # Atualizações de texto e gráfico via Regex
    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y")
    site = re.sub(r'id="update-date">Atualizado:.*?<', f'id="update-date">Atualizado: {data_hoje}<', site)
    
    # Injeção de conteúdo usando marc
