import streamlit as st
import pandas as pd
import numpy as np
import cv2

st.set_page_config(page_title="Corretor de Gabarito", layout="centered")

st.title("📝 Corretor de Gabarito")

# --- CONFIGURAÇÕES DA PROVA ---
st.sidebar.header("⚙️ Configurações da Prova")
num_questoes = st.sidebar.number_input("Número de Questões", min_value=1, max_value=50, value=10)
num_opcoes = st.sidebar.selectbox("Quantidade de Alternativas", [4, 5], index=1, format_func=lambda x: "A-D (4)" if x == 4 else "A-E (5)")

# Mapeamento de índice para letra
letras = ['A', 'B', 'C', 'D', 'E'][:num_opcoes]

# --- DEFINIÇÃO DO GABARITO OFICIAL ---
st.subheader("1. Gabarito Oficial")
gabarito_oficial = []

cols = st.columns(5)
for i in range(num_questoes):
    col_idx = i % 5
    with cols[col_idx]:
        resp = st.selectbox(f"Q{i+1}", letras, key=f"q_{i}")
        gabarito_oficial.append(resp)

# --- INICIALIZAÇÃO DA SESSÃO PARA ARMAZENAR RESULTADOS ---
if "resultados" not in st.session_state:
    st.session_state.resultados = []

st.divider()

# --- LEITURA DO GABARITO DO ALUNO ---
st.subheader("2. Corrigir Cartão Resposta")

# Captura de foto pela câmera do celular
foto = st.camera_input("Tire a foto do gabarito")

if foto is not None:
    # Converter imagem carregada para OpenCV
    bytes_data = foto.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

    # Entrada manual temporária do número até integrar o detector de OMR da frequência
    numero_aluno = st.text_input("Número/Frequência do Aluno:", key="num_aluno_input")
    nome_aluno = st.text_input("Nome do Aluno (Opcional):", key="nome_aluno_input")

    if st.button("Processar e Salvar Nota"):
        if not numero_aluno:
            st.warning("Por favor, insira o número da frequência.")
        else:
            # Lógica temporária de simulação/exemplo até o alinhamento de visão computacional
            # Substituir por processamento OMR dos contornos
            acertos_simulados = np.random.randint(0, num_questoes + 1)
            nota = round((acertos_simulados / num_questoes) * 10, 1)

            st.session_state.resultados.append({
                "Número": numero_aluno,
                "Nome": nome_aluno if nome_aluno else "Não informado",
                "Acertos": f"{acertos_simulados}/{num_questoes}",
                "Nota": nota
            })
            st.success(f"Nota salva! Número: {numero_aluno} | Nota: {nota}")

# --- TABELA DE RESULTADOS E EXPORTAÇÃO ---
st.divider()
st.subheader("3. Notas Registradas")

if st.session_state.resultados:
    df = pd.DataFrame(st.session_state.resultados)
    st.dataframe(df, use_container_width=True)

    # Converter DataFrame para CSV/Excel
    csv = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📊 Gerar Planilha (CSV)",
        data=csv,
        file_name="notas_gabarito.csv",
        mime="text/csv"
    )
else:
    st.info("Nenhuma nota registrada ainda.")

