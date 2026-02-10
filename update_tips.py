import os
import json
import datetime
import requests
import google.generativeai as genai
import re

# 1. Configurações de API (Certifique-se de que os nomes nos Secrets do GitHub são estes)
GENAI_KEY = os.environ["GEMINI_API_KEY"]
FOOTBALL_KEY = os.environ["FOOTBALL_API_KEY"]

genai.configure(api_key=GENAI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def conferir_resultados_ontem():
    """Analisa o index.html, busca os IDs e valida o Win+BTTS na API-Football"""
    try:
        if not os.path.exists("index.html"):
            return 0
            
        with open("index.html", "r", encoding="utf-8") as f:
            html_antigo = f.read()
        
        # Extração de IDs usando Regex
        fixtures = re.findall(r"", html_antigo)
        favoritos = re.findall(r"", html_antigo)
        
        lucro_total = 0
        headers = {'x-apisports-key': FOOTBALL_KEY}

        for i in range(len(fixtures)):
            # Validação: só consulta se for um ID numérico real
            if not fixtures[i].isdigit():
                continue

            url = f"https://v3.football.api-sports.io/fixtures?id={fixtures[i]}"
            res = requests.get(url, headers=headers).json()
            
            if res.get('response'):
                match = res['response'][0]
                if match['fixture']['status']['short'] == 'FT': # Jogo Finalizado
                    g_home = match['goals']['home']
                    g_away = match['goals']['away']
                    
                    # Identifica vencedor
                    vencedor_id = None
                    if match['teams']['home']['winner']: 
                        vencedor_id = match['teams']['home']['id']
                    elif match['teams']['away']['winner']: 
                        vencedor_id = match['teams']['away']['id']

                    deu_btts = (g_home > 0 and g_away > 0)
                    venceu_favorito = (str(vencedor_id) == favoritos[i])

                    if deu_btts and venceu_favorito:
                        lucro_total += 1.5 # Ganho de 1.5 unidades
                    else:
                        lucro_total -= 1.0 # Perda de 1 unidade
        
        return lucro_total
    except Exception as e:
        print(f"Erro na conferência: {e}")
        return 0

def gerar_novas_tips():
    """Solicita ao Gemini o consenso dos especialistas com IDs reais"""
    prompt = """
    Aja como um analista de dados focado em confluência esportiva.
    1. Analise as previsões de 'Alex Keble' (tática) e 'The Goal King' (estatística).
    2. Identifique 2 jogos de hoje onde AMBOS concordam na 'Vitória do Favorito + Ambos Marcam'.
    
    REGRAS TÉCNICAS OBRIGATÓRIAS:
    - No topo de cada card, insira: e .
    - SEGURANÇA: Não invente IDs. Se não tiver certeza absoluta do ID da fixture, use obrigatoriamente um jogo de LIGA PRINCIPAL (Premier League ID: 39, La Liga ID: 140, Bundesliga ID: 78).
    - Use o padrão visual de cards HTML com Tailwind CSS que definimos anteriormente.
    - Mencione Keble e Goal King nas seções de análise.
    
    Retorne apenas o HTML puro, sem explicações.
    """
    response = model.generate_content(prompt)
    return response.text.replace("```html", "").replace("```", "").strip()

def atualizar_tudo():
    # A. Conferir lucro de ontem
    lucro_dia = conferir_resultados_ontem()

    # B. Gerar/Atualizar Histórico JSON
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
        "lucro_acumulado": novo_acumulado,
        "greens": g,
        "reds": r
    })

    # C. Obter novos jogos do Gemini
    html_novos_jogos = gerar_novas_tips()

    # D. Ler e atualizar o index.html
    with open("index.html", "r", encoding="utf-8") as f:
        site = f.read()

    # Atualiza Data
    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y")
    site = re.sub(r'id="update-date">Atualizado:.*?<', f'id="update-date">Atualizado: {data_hoje}<', site)

    # Atualiza Gráfico (Labels e Data)
    labels = [d["data"] for d in historico[-10:]]
    valores = [d["lucro_acumulado"] for d in historico[-10:]]
    site = re.sub(r"labels: \[.*?\]", f"labels: {labels}", site)
    site = re.sub(r"data: \[.*?\]", f"data: {valores}", site)

    # Atualiza Contadores (Win Rate, Greens, Reds)
    site = re.sub(r'\d+%(?=</span>)', f'{win_rate}%', site, 1)
    site = re.sub(r'(Greens</span>.*?text-xl font-bold text-emerald-400">)(\d+)', rf'\1{g}', site, flags=re.DOTALL)
    site = re.sub(r'(Reds</span>.*?text-xl font-bold text-red-400">)(\d+)', rf'\1{r}', site, flags=re.DOTALL)

    # Injeta os novos cards entre as âncoras
    topo = site.split("")[0]
    base = site.split("")[1]
    site_final = f"{topo}\n{html_novos_jogos}\n{base}"

    # E. Salvar arquivos finais
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(site_final)
    with open("historico.json", "w") as f:
        json.dump(historico, f, indent=2)

if __name__ == "__main__":
    atualizar_tudo()
