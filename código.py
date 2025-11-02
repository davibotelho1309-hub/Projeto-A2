import os
import requests
import pandas as pd
from collections import Counter
import streamlit as st

# ============================
# CONFIGURAÇÕES INICIAIS
# ============================

st.set_page_config(page_title="Análise Legislativa", page_icon="🏛️", layout="wide")

SENADO_BASE = "https://legis.senado.leg.br/dadosabertos/materia/pesquisa"
CAMARA_BASE = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"
YEARS = list(range(2020, 2026))

# Chave da API do YouTube (defina como variável de ambiente)
YOUTUBE_API_KEY = os.environ.get("AIzaSyASTN-AAwkkQMnpxDkzLCW4m-x8FH8n340")


# ============================
# FUNÇÕES AUXILIARES
# ============================

def buscar_materias(keyword):
    """Busca matérias no Senado e, se falhar, usa a Câmara dos Deputados."""
    resultados = []

    # --- TENTA SENADO ---
    try:
        params = {"palavraChave": keyword, "format": "json"}
        r = requests.get(SENADO_BASE, params=params, timeout=10)
        if r.ok:
            data = r.json()
            materias = data.get("PesquisaMateria", {}).get("Materias", {}).get("Materia", [])
            for m in materias:
                info = m.get("IdentificacaoMateria", {})
                resultados.append({
                    "ano": int(info.get("AnoMateria", 0)),
                    "sigla": info.get("SiglaSubtipoMateria"),
                    "numero": info.get("NumeroMateria"),
                    "ementa": m.get("Ementa", ""),
                    "url": f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{info.get('CodigoMateria')}",
                    "origem": "Senado"
                })
    except Exception as e:
        st.warning(f"⚠️ Erro ao acessar API do Senado: {e}")

    # --- SE FALHAR, USA CÂMARA ---
    if not resultados:
        try:
            r = requests.get(f"{CAMARA_BASE}?palavraChave={keyword}&itens=100", timeout=10)
            if r.ok:
                data = r.json()
                for p in data.get("dados", []):
                    resultados.append({
                        "ano": int(p.get("ano", 0)) if p.get("ano") else None,
                        "sigla": p.get("siglaTipo"),
                        "numero": p.get("numero"),
                        "ementa": p.get("ementa", ""),
                        "url": p.get("uri"),
                        "origem": "Câmara"
                    })
        except Exception as e:
            st.error(f"Erro ao acessar API da Câmara: {e}")

    return [r for r in resultados if r.get("ano")]


def contar_por_ano(materias):
    contagem = Counter()
    for m in materias:
        if 2020 <= m["ano"] <= 2025:
            contagem[m["ano"]] += 1
    return {ano: contagem.get(ano, 0) for ano in YEARS}


def buscar_videos_youtube(tema, max_results=5):
    """Busca vídeos no YouTube relacionados ao tema."""
    if not YOUTUBE_API_KEY:
        return []

    try:
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
    except Exception as e:
        st.warning(f"⚠️ Erro ao buscar vídeos no YouTube: {e}")
        return []


# ============================
# INTERFACE STREAMLIT
# ============================

st.title("🏛️ Análise de Temas no Congresso Nacional (2020–2025)")
st.markdown("Pesquise como um tema foi abordado em projetos de lei no **Senado** e na **Câmara dos Deputados**, e veja sua evolução ao longo do tempo.")

tema = st.text_input("Digite o tema que deseja analisar:", placeholder="ex: inteligência artificial, meio ambiente, educação...")

if st.button("🔍 Buscar informações"):
    if not tema.strip():
        st.warning("Por favor, insira um tema para continuar.")
    else:
        with st.spinner("Buscando matérias nas bases legislativas..."):
            materias = buscar_materias(tema)

        if not materias:
            st.error("Nenhuma matéria encontrada para esse tema.")
        else:
            st.success(f"{len(materias)} matérias encontradas!")

            df = pd.DataFrame(materias)
            st.dataframe(df[["ano", "sigla", "numero", "ementa", "origem", "url"]])

            # --- Gráfico de Frequência ---
            contagem = contar_por_ano(materias)
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(contagem.keys(), contagem.values(), color="#0056A3")
            ax.set_xlabel("Ano")
            ax.set_ylabel("Número de matérias")
            ax.set_title(f"Distribuição de matérias sobre '{tema}' (2020–2025)")
            st.pyplot(fig)

            # --- Vídeos do YouTube ---
            st.subheader("🎥 Vídeos recomendados sobre o tema")
            videos = buscar_videos_youtube(tema)
            if videos:
                for v in videos:
                    st.markdown(f"- [{v['title']}]({v['url']})")
            else:
                st.info("Nenhum vídeo encontrado ou chave da API do YouTube não configurada.")
