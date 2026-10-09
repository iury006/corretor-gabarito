import streamlit as st
import pandas as pd
import numpy as np
import cv2
import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Corretor de Gabarito", layout="centered", initial_sidebar_state="expanded")

st.title("📝 Corretor de Gabarito")

# --- CONFIGURAÇÕES DA PROVA ---
st.sidebar.header("⚙️ Configurações da Prova")
num_questoes = st.sidebar.number_input("Número de Questões", min_value=1, max_value=50, value=10, key="cfg_num_q")
num_opcoes = st.sidebar.selectbox("Quantidade de Alternativas", [4, 5], index=1, format_func=lambda x: "A-D (4)" if x == 4 else "A-E (5)", key="cfg_num_opt")

letras = ['A', 'B', 'C', 'D', 'E'][:num_opcoes]

# --- FUNÇÃO PARA GERAR O PDF COMPACTO DO GABARITO ---
def gerar_pdf_gabarito(q_total, opt_total):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter # 612 x 792 pontos

    # Cálculo da largura e altura dinâmica do bloco compacto com base no nº de questões
    num_colunas_questoes = 1 + ((q_total - 1) // 20)
    box_width = 240 + (num_colunas_questoes * 120)
    q_por_coluna = min(q_total, 20)
    box_height = 100 + max(q_por_coluna * 16, 150)

    # Posição inicial (topo esquerdo do cartão compacto)
    x_start = 40
    y_top = height - 40
    y_bottom = y_top - box_height
    anchor_size = 16

    # 1. Âncoras pretas bem próximas abraçando o conteúdo
    c.setFillColorRGB(0, 0, 0)
    c.rect(x_start, y_top - anchor_size, anchor_size, anchor_size, fill=True, stroke=False) # Topo-Esq
    c.rect(x_start + box_width - anchor_size, y_top - anchor_size, anchor_size, anchor_size, fill=True, stroke=False) # Topo-Dir
    c.rect(x_start, y_bottom, anchor_size, anchor_size, fill=True, stroke=False) # Base-Esq
    c.rect(x_start + box_width - anchor_size, y_bottom, anchor_size, anchor_size, fill=True, stroke=False) # Base-Dir

    # 2. Cabeçalho Compacto
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_start + 25, y_top - 14, "CARTÃO RESPOSTA")

    # 3. Campos de Identificação
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_start + 25, y_top - 32, "NOME:")
    c.line(x_start + 60, y_top - 34, x_start + 220, y_top - 34)

    c.drawString(x_start + 230, y_top - 32, "TURMA:")
    c.line(x_start + 270, y_top - 34, x_start + box_width - 25, y_top - 34)

    # 4. Grade de Frequência (Nº do Aluno: 2 dígitos - 0 a 9)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_start + 25, y_top - 55, "FREQUÊNCIA:")

    y_freq = y_top - 72
    for col in range(2):
        for digit in range(10):
            x = x_start + 28 + (col * 28)
            y = y_freq - (digit * 13)
            c.circle(x, y, 4.5, fill=False)
            c.setFont("Helvetica", 6)
            c.drawString(x - 1.8, y - 2, str(digit))

    # 5. Questões e Alternativas
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_start + 115, y_top - 55, "RESPOSTAS:")

    y_q = y_top - 72
    x_q = x_start + 115

    for q in range(1, q_total + 1):
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x_q, y_q, f"{q:02d}:")

        for opt_idx in range(opt_total):
            x_circle = x_q + 22 + (opt_idx * 18)
            c.circle(x_circle, y_q + 2.5, 4.5, fill=False)
            c.setFont("Helvetica", 6)
            c.drawString(x_circle - 1.8, y_q + 0.5, letras[opt_idx])

        y_q -= 15
        if q % 20 == 0 and q < q_total:
            y_q = y_top - 72
            x_q += 115

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- BOTÃO DE GERAR GABARITO IMPRESSO ---
st.sidebar.divider()
st.sidebar.subheader("🖨️ Modelo da Folha")
pdf_bytes = gerar_pdf_gabarito(num_questoes, num_opcoes)
st.sidebar.download_button(
    label="📄 Baixar PDF do Gabarito",
    data=pdf_bytes,
    file_name=f"gabarito_{num_questoes}Q.pdf",
    mime="application/pdf",
    key="btn_download_pdf"
)

# --- DEFINIÇÃO DO GABARITO OFICIAL (LISTA VERTICAL ÚNICA) ---
st.subheader("1. Gabarito Oficial")
gabarito_oficial = []

for i in range(num_questoes):
    resp = st.selectbox(
        f"Questão {i+1:02d}", 
        letras, 
        key=f"gabarito_q_{i+1}"
    )
    gabarito_oficial.append(resp)

# --- INICIALIZAÇÃO DA SESSÃO ---
if "resultados" not in st.session_state:
    st.session_state.resultados = []

st.divider()

# --- LEITURA DO GABARITO DO ALUNO ---
st.subheader("2. Corrigir Cartão Resposta")

st.write("📌 *Ao abrir a câmera pela primeira vez, permita o acesso no seu navegador.*")
foto = st.camera_input("Capturar Gabarito", key="camera_input_aluno")

if foto is not None:
    bytes_data = foto.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

    numero_aluno = st.text_input("Nº Frequência:", key="input_num_aluno")
    nome_aluno = st.text_input("Nome do Aluno (Opcional):", key="input_nome_aluno")

    if st.button("💾 Salvar Correção", key="btn_salvar_nota"):
        if not numero_aluno:
            st.warning("Insira o número da frequência antes de salvar.")
        else:
            acertos_simulados = np.random.randint(0, num_questoes + 1)
            nota = round((acertos_simulados / num_questoes) * 10, 1)

            st.session_state.resultados.append({
                "Número": numero_aluno,
                "Nome": nome_aluno if nome_aluno else "Não informado",
                "Acertos": f"{acertos_simulados}/{num_questoes}",
                "Nota": nota
            })
            st.success(f"✅ Salvo! Aluno Nº {numero_aluno} — Nota: {nota}")

# --- TABELA DE RESULTADOS E EXPORTAÇÃO ---
st.divider()
st.subheader("3. Notas Registradas")

if st.session_state.resultados:
    df = pd.DataFrame(st.session_state.resultados)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📊 Gerar Planilha (CSV)",
        data=csv,
        file_name="notas_gabarito.csv",
        mime="text/csv",
        key="btn_download_csv"
    )
else:
    st.info("Nenhuma nota registrada ainda.")
