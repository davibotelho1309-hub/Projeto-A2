import os
import requests
import pandas as pd
from collections import Counter
import streamlit as st

# ============================
# CONFIGURAÇÕES
# ============================
SENADO_BASE = "https://legis.senado.leg.br/dadosabertos/materia/pesquisa"
YEARS = list(range(2020, 2026))
YOUTUBE_API_KEY = os.environ.get(""AIzaSyASTN-AAwkkQMnpxDkzLCW4m-x8FH8n340)

# ============================
# FUNÇÕES AUXILIARES
# ============================

def buscar_materias(keyword):
    params = {"palavraChave": keyword, "format": "json"}
    r = requests.get(SENADO_BASE, params=params, timeout=20)
    if not r.ok:
        return []

    data = r.json()
    materias = data.get("PesquisaMateria", {}).get("Materias", {}).get("Materia", [])
    resultado = []
    for m in materias:
        info = m.get("IdentificacaoMateria", {})
        resultado.append({
            "ano": int(info.get("AnoMateria", 0)),
            "sigla": info.get("SiglaSubtipoMateria"),
            "numero": info.get("NumeroMateria"),
            "ementa": m.get("Ementa", ""),
            "url": f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{info.get('CodigoMateria')}"
        })
    return resultado

def contar_por_ano(materias):
    contagem = Counter()
    for m in materias:
        if 2020 <= m["ano"] <= 2025:
            contagem[m["ano"]] += 1
    return {ano: contagem.get(ano, 0) for ano in YEARS}

def buscar_videos_youtube(tema, max_results=5):
    if not YOUTUBE_API_KEY:
        return []
    service = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    query = f"{tema} Senado Federal Congresso Brasil"
    request = service.search().list(q=query, part="snippet", maxResults=max_results, type="video")
    response = request.execute()

    videos = []
    for item in response.get("items", []):
        videos.append({
            "title": item["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        })
    return videos

# ============================
# INTERFACE STREAMLIT
# ============================

st.set_page_config(page_title="Análise de Temas no Senado", page_icon="🏛️", layout="wide")

st.title("🏛️ Análise de Temas no Congresso Nacional (2020–2025)")
tema = st.text_input("Digite o tema para análise (ex: inteligência artificial, meio ambiente...):")

if st.button("Buscar informações"):
    if not tema.strip():
        st.warning("Por favor, insira um tema para continuar.")
    else:
        st.info(f"🔎 Buscando matérias sobre **{tema}** no Senado...")
        materias = buscar_materias(tema)
        if not materias:
            st.error("Nenhuma matéria encontrada.")
        else:
            st.success(f"{len(materias)} matérias encontradas!")

            df = pd.DataFrame(materias)
            st.dataframe(df[["ano", "sigla", "numero", "ementa", "url"]])

            contagem = contar_por_ano(materias)

            # Gráfico
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(contagem.keys(), contagem.values(), color="#0072B2")
            ax.set_xlabel("Ano")
            ax.set_ylabel("Número de matérias")
            ax.set_title(f"Tema: {tema}")
            st.pyplot(fig)

            # Vídeos do YouTube
            st.subheader("🎥 Vídeos recomendados no YouTube")
            videos = buscar_videos_youtube(tema)
            if videos:
                for v in videos:
                    st.markdown(f"- [{v['title']}]({v['url']})")
            else:
                st.info("Nenhum vídeo encontrado ou chave da API do YouTube não configurada.")
