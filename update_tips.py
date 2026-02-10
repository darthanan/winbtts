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
    """Lê o HTML, busca os IDs e valida o resultado na API-Football"""
    try:
        if not os.path.exists("index.html"): return 0
        with open("index.html", "r", encoding="utf-8") as f:
            html_antigo = f.read()
        
        # Busca IDs ocultos gerados pelo Gemini (padrão data-fixture="123")
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

                    # Regra: Vitória do favorito + Ambos Marcam (BTTS)
                    if (g_home > 0 and g_away > 0) and (str(vencedor_id) == favoritos[i]):
                        lucro_total += 1.5 # Green
                    else:
                        lucro_total -= 1.0 # Red
        return lucro_total
    except Exception as e:
        print(f"Erro ao conferir resultados: {e}")
        return 0

def gerar_novas_tips():
    """Solicita ao Gemini o consenso com links REAIS e CLICÁVEIS"""
    prompt = """
    Aja como um analista de futebol (Consenso Alex Keble e Goal King).
    Gere 2 cards HTML para o mercado 'Vitória do Favorito + Ambos Marcam'.
    
    REGRAS DE OURO PARA OS LINKS:
    1. Cada card deve ter 3 botões de odds. 
    2. Use OBRIGATORIAMENTE a tag <a href="..." target="_blank">.
    3. Use estes links exatos:
       - Bet365: https://www.bet365.com
       - BetMGM: https://sports.betmgm.com
       - Betano: https://br.betano.com
    
    ESTRUTURA DO LINK (COPIE ESTE MODELO):
    <a href="LINK_AQUI" target="_blank" rel="noopener" style="display: block; width: 100%; cursor: pointer; position: relative; z-index: 10; text-decoration: none;" class="bg-slate-800 p-4 rounded-xl border border-slate-700 hover:border-emerald-500 transition-all mb-3">
        <span style="color: #94a3b8; font-size: 12px; display: block;">NOME_DA_CASA</span>
        <span style="color: #ffffff; font-weight: bold; font-size: 18px;">ODD EX: 2.10</span>
    </a>

    O container principal do card deve ter os atributos: data-fixture="ID_REAL" e data-fav="ID_TIME_FAVORITO".
    Retorne APENAS o HTML puro, sem blocos de texto ou markdown (```html).
    """
    
    response = model.generate_content(prompt)
    html_gerado = response.text.replace("```html", "").replace("```", "").strip()
    return html_gerado

def atualizar_tudo():
    # 1. Conferir o lucro de ontem
    lucro_dia = conferir_resultados_ontem()

    # 2. Gerenciar Histórico JSON
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

    # 3. Gerar novos palpites
    html_novos_jogos = gerar_novas_tips()

    # 4. Atualizar o HTML
    with open("index.html", "r", encoding="utf-8") as f:
        site = f.read()

    # Atualiza data de atualização
    data_hoje = datetime.datetime.now().strftime("%d/%m/%Y")
    site = re.sub(r'id="update-date">.*?<', f'id="update-date">Atualizado: {data_hoje}<', site)

    # Atualiza Gráfico (últimos 10 dias)
    labels = [d["data"] for d in historico[-10:]]
    valores = [d["lucro_acumulado"] for d in historico[-10:]]
    site = re.sub(r"labels: \[.*?\]", f"labels: {labels}", site)
    site = re.sub(r"data: \[.*?\]", f"data: {valores}", site)

    # Atualiza Stats Visuais
    site = re.sub(r'\d+%(?=</span>)', f'{win_rate}%', site, 1)
    # Regex robusto para Greens e Reds
    site = re.sub(r'(Greens</span>.*?text-xl font-bold text-emerald-400">)\d+', rf'\1{g}', site, flags=re.DOTALL)
    site = re.sub(r'(Reds</span>.*?text-xl font-bold text-red-400">)\d+', rf'\1{r}', site, flags=re.DOTALL)

    # 5. Injeção das Tips (Surgical Split)
    try:
        topo = site.split("")[0]
        base = site.split("")[1]
        site_final = f"{topo}\n{html_novos_jogos}\n{base}"
    except IndexError:
        print("Erro Crítico: Marcadores não encontrados no seu index.html")
        return

    # 6. Salvar arquivos
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(site_final)
    
    with open("historico.json", "w") as f:
        json.dump(historico, f, indent=2)

    print(f"Sucesso! Lucro computado: {lucro_dia} | Win Rate: {win_rate}%")

if __name__ == "__main__":
    atualizar_tudo()
