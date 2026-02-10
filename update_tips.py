import os
import json
import datetime
import requests
import google.generativeai as genai
import re

# 1. Configurações de Conectividade
GENAI_KEY = os.environ["GEMINI_API_KEY"]
FOOTBALL_KEY = os.environ["FOOTBALL_API_KEY"]

genai.configure(api_key=GENAI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def conferir_resultados_ontem():
    """Lê o HTML, busca os IDs e valida o Win+BTTS na API-Football"""
    try:
        if not os.path.exists("index.html"): return 0
        with open("index.html", "r", encoding="utf-8") as f:
            html_antigo = f.read()
        
        fixtures = re.findall(r"", html_antigo)
        favoritos = re.findall(r"", html_antigo)
        
        lucro_total = 0
        headers = {'x-apisports-key': FOOTBALL_KEY}

        for i in range(len(fixtures)):
            if not fixtures[i].isdigit(): continue
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

                    if (g_home > 0 and g_away > 0) and (str(vencedor_id) == favoritos[i]):
                        lucro_total += 1.5
                    else:
                        lucro_total -= 1.0
        return lucro_total
    except:
        return 0

def gerar_novas_tips():
    """Solicita ao Gemini o consenso com links para as casas"""
    prompt = """
    Aja como um analista focado no consenso entre 'Alex Keble' e 'The Goal King'.
    Gere 2 cards HTML para o mercado 'Vitória do Favorito + Ambos Marcam'.
    
    REGRAS OBRIGATÓRIAS:
    1. Inclua os IDs ocultos: e .
    2. SEGURANÇA: Use IDs reais de ligas principais (Premier League, La Liga, etc).
    3. ODDS COMO BOTÕES: As 3 odds (Bet365, BetMGM, Betano) devem ser tags <a>.
       - Bet365: https://www.bet365.com
       - BetMGM: https://sports.betmgm.com
       - Betano: https://br.betano.com
    4. Estilo das Odds: Usar 'bg-slate-800 p-2 rounded block hover:bg-slate-700 transition-all border border-transparent hover:border-emerald-500/50'.
    5. No card, mencione a tática (Keble) e a estatística (Goal King).
    
    Retorne apenas o HTML puro.
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

    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y")
    site = re.sub(r'id="update-date">Atualizado:.*?<', f'id="update-date">Atualizado: {data_hoje}<', site)

    # Gráfico
    labels = [d["data"] for d in historico[-10:]]
    valores = [d["lucro_acumulado"] for d in historico[-10:]]
    site = re.sub(r"labels: \[.*?\]", f"labels: {labels}", site)
    site = re.sub(r"data: \[.*?\]", f"data: {valores}", site)

    # Stats
    site = re.sub(r'\d+%(?=</span>)', f'{win_rate}%', site, 1)
    site = re.sub(r'(Greens</span>.*?text-xl font-bold text-emerald-400">)(\d+)', rf'\1{g}', site, flags=re.DOTALL)
    site = re.sub(r'(Reds</span>.*?text-xl font-bold text-red-400">)(\d+)', rf'\1{r}', site, flags=re.DOTALL)

    # Injeção
    topo = site.split("")[0]
    base = site.split("")[1]
    site_final = f"{topo}\n{html_novos_jogos}\n{base}"

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(site_final)
    with open("historico.json", "w") as f:
        json.dump(historico, f, indent=2)

if __name__ == "__main__":
    atualizar_tudo()
