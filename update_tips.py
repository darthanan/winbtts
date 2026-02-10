import os
import json
import datetime
import google.generativeai as genai

# Configuração da IA
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def atualizar_dados_historicos(novo_resultado_unidades):
    # 1. Lê o arquivo JSON
    with open("historico.json", "r") as f:
        historico = json.load(f)
    
    # 2. Calcula novos valores
    ultima_entrada = historico[-1]
    novo_lucro = ultima_entrada["lucro_acumulado"] + novo_resultado_unidades
    nova_data = datetime.datetime.now().strftime("%d/%m")
    
    # Simulação simples de contagem de greens/reds para o exemplo
    g = ultima_entrada["greens"] + (1 if novo_resultado_unidades > 0 else 0)
    r = ultima_entrada["reds"] + (1 if novo_resultado_unidades <= 0 else 0)

    # 3. Adiciona ao histórico
    historico.append({
        "data": nova_data,
        "lucro_acumulado": round(novo_lucro, 2),
        "greens": g,
        "reds": r
    })
    
    # 4. Salva de volta no JSON
    with open("historico.json", "w") as f:
        json.dump(historico, f, indent=2)
    
    return historico

# --- PROMPT PARA GERAR OS JOGOS ---
prompt_jogos = "Gere 2 blocos HTML de cards de apostas Win+BTTS para hoje (use o formato anterior)..."
response = model.generate_content(prompt_jogos)
html_jogos = response.text.replace("```html", "").replace("```", "").strip()

# --- ATUALIZAÇÃO DO HISTÓRICO ---
# Aqui simulamos o resultado do dia anterior. 
# Em um script avançado, a IA checaria o placar real via API.
resultado_ontem = 1.5 # Exemplo: Ganhou 1.5 unidades ontem
dados_completos = atualizar_dados_historicos(resultado_ontem)

# Preparar listas para o gráfico do Javascript
labels_grafico = [d["data"] for d in dados_completos]
valores_grafico = [d["lucro_acumulado"] for d in dados_completos]
stats_finais = dados_completos[-1]

# --- INJEÇÃO NO INDEX.HTML ---
with open("index.html", "r", encoding="utf-8") as f:
    html_site = f.read()

# Atualiza os jogos
html_site = html_site.split("")[0] + "\n" + html_jogos + "\n" + html_site.split("")[1]

# Atualiza o gráfico no Javascript (procura a linha do 'data:' no JS do index.html)
# Nota: Para isso funcionar 100%, o Python substitui as variáveis do Chart.js
html_site = html_site.replace("labels: ['Jan 01', 'Jan 10', 'Jan 20', 'Fev 01', 'Fev 10']", f"labels: {labels_grafico}")
html_site = html_site.replace("data: [0, 4.2, 3.1, 8.5, 12.4]", f"data: {valores_grafico}")

# Salva o index atualizado
with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_site)
