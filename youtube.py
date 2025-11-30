import pandas as pd
import os
import json
import requests
import time  # Controlar o ritmo das requisições

# Caminho absoluto da pasta onde está o script atual
base_dir = os.path.dirname(os.path.abspath(__file__))

# Caminhos automáticos. Acessam os arquivos dos filmes e séries dados pela TMDB
filmes = os.path.join(base_dir, "..", "dados", "top50_filmes.json")
series = os.path.join(base_dir, "..", "dados", "top50_series.json")

# Ler os arquivos JSON
df_filmes = pd.read_json(filmes)
df_series = pd.read_json(series)

# Concatenar/juntar ambos arquivos
df_final = pd.concat([df_filmes, df_series], ignore_index=True)


# Função para se conectar com o Youtube
def conexao_youtube(pesquisar):
    # Lista de chaves API (rotação automática)
    api_key = [
        'AIzaSyCcE_YpT1UQ7DSQWvz-PSvQC2u85_2EwYI',
        'AIzaSyDRaqTu_A-lbnYJQwQqYx87Qvk_V1fTBig',
        'AIzaSyD2fmJf_gw2cNbOOMYguC2ucayGbE48wK8',
        'AIzaSyCQM3Sv_9KlicI_Ce2zly86qztNlEBgqoE',
        'AIzaSyCnb8SYLcxzTP1Tf9V5D7zC5JtaE9hKt2Q',
        'AIzaSyCz0LBJhe0Rxwx7RAaaQnngPUI9N1I0meM'
    ]
    url = "https://www.googleapis.com/youtube/v3/search"

    # Pausa entre requisições para evitar bloqueios de taxa
    time.sleep(0.3)

    for chave in api_key:
        params = {
            "part": "snippet",
            "q": pesquisar,
            "key": chave,
            "maxResults": 3
        }

        try:
            resposta = requests.get(url, params=params, timeout=10)
        except requests.exceptions.RequestException:
            # Ignora erros de rede silenciosamente
            continue

        # Se a chave estourou o limite de uso (erro 403), apenas pula
        if resposta.status_code == 403:
            # Silencioso: não mostra nada
            continue

        if resposta.status_code == 200:
            resposta_json = resposta.json()

            if not resposta_json.get("items"):
                return None, None

            video_id = resposta_json["items"][0]["id"].get("videoId")
            titulo_video = resposta_json["items"][0]["snippet"]["title"]

            time.sleep(0.3)

            # Pegar quantidade de VIEWS de cada vídeo
            url_stats = "https://www.googleapis.com/youtube/v3/videos"
            params_stats = {
                "part": "statistics",
                "id": video_id,
                "key": chave
            }
            resposta_stats = requests.get(url_stats, params=params_stats)

            if resposta_stats.status_code == 200:
                stats_json = resposta_stats.json()
                views = int(stats_json["items"][0]["statistics"]["viewCount"])
                return titulo_video, views

        # Pausa entre tentativas de chaves para evitar rejeição por frequência
        time.sleep(0.5)

    # Se nenhuma chave funcionou (só mostra isso no fim)
    print(f"[Aviso] Nenhuma chave disponível para: {pesquisar}")
    return None, None


# Lista para armazenar os resultados
resultados_youtube = []

# Puxar os dados necessários do arquivo
for index, linha in df_final.iterrows():
    titulo = linha["Nome"]
    data = linha["Data"]
    ano = data.split("-")[0]
    pesquisar = f"Trailer {titulo} - {ano}"

    titulo_video, views = conexao_youtube(pesquisar)

    # Criar um dicionário com os dados desejados
    resultado = {
        "Nome": titulo,
        "Ano": ano,
        "Trailer_Youtube": titulo_video if titulo_video else None,
        "Views": views if views else None
    }

    resultados_youtube.append(resultado)

    if titulo_video and views:
        print(f"{titulo_video} - Views: {views}")
    else:
        print(f"Não foi possível obter dados para: {titulo}")

    time.sleep(0.4)

#Resultados vira Json para serem usados
json_resultados = json.dumps(resultados_youtube, ensure_ascii=False, indent=4)

# Salvar em arquivo
caminho_saida = os.path.join(base_dir, "..", "youtube", "resultados_youtube.json")
with open(caminho_saida, "w", encoding="utf-8") as f:
    f.write(json_resultados)

