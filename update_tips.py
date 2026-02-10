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
    """Lê o HTML atual, busca os IDs ocultos e checa na API o que aconteceu"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_antigo = f.read()
        
        # Busca IDs ocultos usando Regex (Ex: )
        fixtures = re.findall(r"", html_antigo)
        favoritos = re.findall(r"", html_antigo)
        
        lucro_total = 0
        headers = {'x-apisports-key': FOOTBALL_KEY}

        for i in range(len(fixtures)):
            url = f"https://v3.football.api-sports.io/fixtures?id={fixtures[i]}"
            res = requests.get(url, headers=headers).json()
            
            if res['response']:
                match = res['response'][0]
                status = match['fixture']['status']['short']
                
                if status == 'FT': # Jogo Finalizado
                    g_home = match['goals']['home']
                    g_away = match['goals']['away']
                    # Verifica quem ganhou (ID do time com winner: True)
                    vencedor_id = None
                    if match['teams']['home']['winner']: vencedor_id = match['teams']['home']['id']
                    elif match['teams']['away']['winner']: vencedor_id = match['teams']['away']['id']

                    deu_btts = (g_home > 0 and g_away > 0)
                    venceu_favorito = (str(vencedor_id) == favoritos[i])

                    if deu_btts and venceu_favorito:
                        lucro_total += 1.5 # Green (Odd média estimada)
                    else:
                        lucro_total -= 1.0 # Red
        return lucro_total
    except Exception as e:
        print(f"Erro na conferência: {e}")
        return 0

def rodar_atualizacao():
    # A. Conferir lucro de ontem
    lucro_dia = conferir_resultados_ontem()

    # B. Atualizar historico.json
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

    # C. Pedir novas tips ao Gemini com Passo 3 (IDs Ocultos)
    prompt = """
    Aja como um analista de dados esportivos focado em confluência de especialistas.
    
    SUA TAREFA:
    1. Analise as previsões recentes de 'Alex Keble' (tática) e 'The Goal King' (estatística).
    2. Identifique 2 jogos de CONSENSO onde ambos indicam Vitória do Favorito + Ambos Marcam.
    
    REGRAS OBRIGATÓRIAS DE IDENTIFICAÇÃO (API-FOOTBALL):
    1. No topo de cada card, insira: e .
    2. SEGURANÇA DE DADOS: Não invente ou alucine IDs. Se você não tiver 100% de certeza do ID da fixture, você DEVE buscar um jogo de uma LIGA PRINCIPAL (Premier League, La Liga, Bundesliga ou Champions League) onde o ID seja verificado e estável.
    3. Se houver dúvida sobre o ID do jogo específico, priorize o ID da Premier League (League ID: 39).
    
    FORMATO:
    - Retorne os cards HTML conforme nosso padrão visual.
    - Mencione a visão tática de Keble e os dados do Goal King nos campos de análise.
    
    Retorne apenas o HTML puro.
    """

    response = model.generate_content(prompt)
    html_novos_jogos = response.text.replace("```html", "").replace("```", "").strip()

    # D. Injetar no index.html
    with open("index.html", "r", encoding="utf-8") as f:
        site = f.read()

    # Atualiza Gráfico e Stats
    site = site.replace("labels: ['Jan 01', 'Jan 10', 'Jan 20', 'Fev 01', 'Fev 10']", f"labels: {[d['data'] for d in historico]}")
    site = site.replace("data: [0, 4.2, 3.1, 8.5, 12.4]", f"data: {[d['lucro_acumulado'] for d in historico]}")
    
    # Regex para atualizar contadores Win Rate, Greens e Reds
    site = re.sub(r'(\d+)%</span>', f'{win_rate}%</span>', site, 1) # Win Rate
    site = re.sub(r'Greens</span>\s*<span.*?>(\d+)</span>', f'Greens</span><span class="text-xl font-bold text-emerald-400">{g}</span>', site)
    site = re.sub(r'Reds</span>\s*<span.*?>(\d+)</span>', f'Reds</span><span class="text-xl font-bold text-red-400">{r}</span>', site)

    # Injeta Jogos
    topo = site.split("")[0]
    base = site.split("")[1]
    site_final = f"{topo}\n{html_novos_jogos}\n{base}"

    # E. Salvar Tudo
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(site_final)
    with open("historico.json", "w") as f:
        json.dump(historico[-15:], f, indent=2) # Guarda 15 dias de histórico

if __name__ == "__main__":
    rodar_atualizacao()
