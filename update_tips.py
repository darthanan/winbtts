import os
import datetime
import google.generativeai as genai

# 1. Configuração da IA (A chave deve estar nos Secrets do GitHub como GEMINI_API_KEY)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. O comando que define a inteligência da busca
prompt = """
Aja como um analista de apostas profissional. 
1. Escolha 2 jogos de futebol importantes que acontecem hoje ou amanhã.
2. O foco é o mercado 'Vitória do Favorito + Ambos Marcam'.
3. Para cada jogo, gere EXATAMENTE o seguinte bloco de código HTML usando classes do Tailwind CSS:

<div class="card glass rounded-2xl mb-6 cursor-pointer group hover:border-emerald-500/50 transition-colors" onclick="toggleCard(this)">
    <div class="p-6">
        <div class="flex justify-between items-center mb-4">
            <div class="flex items-center space-x-2">
                <span class="text-xs font-bold text-emerald-400 tracking-wider uppercase">[NOME DA LIGA]</span>
            </div>
            <div class="text-xs text-slate-400 font-mono bg-slate-800 px-2 py-1 rounded">
                <i class="far fa-clock mr-1"></i>[HORARIO DE BRASILIA]
            </div>
        </div>
        <div class="flex justify-between items-center px-2 md:px-8">
            <div class="flex flex-col items-center w-1/3">
                <img src="[URL_LOGO_TIME_A]" class="team-logo mb-2">
                <span class="font-bold text-lg text-center leading-tight">[TIME_A]</span>
            </div>
            <div class="flex flex-col items-center justify-center w-1/3">
                <span class="text-2xl font-black text-slate-600">X</span>
                <div class="mt-2 text-center">
                    <span class="block text-xs text-slate-400">ODD ALVO</span>
                    <span class="text-2xl font-bold text-emerald-400">@[ODD]</span>
                </div>
            </div>
            <div class="flex flex-col items-center w-1/3">
                <img src="[URL_LOGO_TIME_B]" class="team-logo mb-2">
                <span class="font-bold text-lg text-center leading-tight">[TIME_B]</span>
            </div>
        </div>
        <div class="mt-6 flex justify-center">
            <i class="fas fa-chevron-down text-slate-500 chevron transition-transform duration-300"></i>
        </div>
    </div>
    <div class="details-panel bg-slate-900/50 border-t border-slate-700/50">
        <div class="p-6">
            <div class="grid md:grid-cols-2 gap-4 mb-6">
                <div class="bg-slate-800/80 p-4 rounded-lg border border-slate-700">
                    <h3 class="text-xs font-bold text-blue-400 uppercase mb-2">Análise Estatística</h3>
                    <p class="text-sm text-slate-300 italic">[DESCRICAO_ESTATISTICA]</p>
                </div>
                <div class="bg-slate-800/80 p-4 rounded-lg border border-slate-700">
                    <h3 class="text-xs font-bold text-purple-400 uppercase mb-2">Análise Tática</h3>
                    <p class="text-sm text-slate-300 italic">[DESCRICAO_TACTICA]</p>
                </div>
            </div>
            <div class="bg-slate-950 rounded-lg p-4">
                <div class="grid grid-cols-3 gap-2 text-center">
                    <div class="bg-slate-800 p-2 rounded"><span class="block text-xs text-green-500">Bet365</span><span class="font-bold">@[ODD1]</span></div>
                    <div class="bg-slate-800 p-2 rounded"><span class="block text-xs text-yellow-500">BetMGM</span><span class="font-bold">@[ODD2]</span></div>
                    <div class="bg-slate-800 p-2 rounded"><span class="block text-xs text-orange-500">Betano</span><span class="font-bold">@[ODD3]</span></div>
                </div>
            </div>
        </div>
    </div>
</div>

Importante: Retorne APENAS o código HTML, sem explicações.
"""

# 3. Execução da IA
response = model.generate_content(prompt)
html_gerado = response.text.replace("```html", "").replace("```", "").strip()

# 4. Leitura e Atualização do arquivo index.html
with open("index.html", "r", encoding="utf-8") as f:
    conteudo = f.read()

# Atualiza a data de processamento
data_hoje = datetime.datetime.now().strftime("%d/%m/%Y")
conteudo = conteudo.split('id="update-date">')[0] + f'id="update-date">Atualizado: {data_hoje}</p>' + conteudo.split('id="update-date">')[1].split('</p>', 1)[1]

# Injeta os novos jogos entre as âncoras
novo_conteudo = conteudo.split("")[0] + "\n" + html_gerado + "\n" + conteudo.split("")[1]

# 5. Salva o arquivo final
with open("index.html", "w", encoding="utf-8") as f:
    f.write(novo_conteudo)

print("Site atualizado com sucesso pela IA!")
