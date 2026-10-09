import streamlit as st
import pandas as pd
import numpy as np
import cv2
import io

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Corretor de Gabarito", layout="centered", initial_sidebar_state="expanded")

st.title("📝 Corretor de Gabarito Avançado")

# --- CONFIGURAÇÕES DA PROVA ---
st.sidebar.header("⚙️ Configurações da Prova")
num_questoes = st.sidebar.number_input("Número de Questões", min_value=1, max_value=50, value=10, key="cfg_num_q")
num_opcoes = st.sidebar.selectbox("Quantidade de Alternativas", [4, 5], index=1, format_func=lambda x: "A-D (4)" if x == 4 else "A-E (5)", key="cfg_num_opt")
valor_por_questao = st.sidebar.number_input("Valor de cada questão (pontos)", min_value=0.1, max_value=10.0, value=1.0, step=0.1, key="cfg_valor_q")

letras = ['A', 'B', 'C', 'D', 'E'][:num_opcoes]

# --- UPLOAD DE PLANILHA DE ALUNOS (OPCIONAL) ---
st.sidebar.divider()
st.sidebar.subheader("📋 Lista de Alunos (Opcional)")
arquivo_alunos = st.sidebar.file_uploader("Enviar planilha (.csv ou .xlsx)", type=["csv", "xlsx"], key="upload_lista_alunos")

mapa_alunos = {}
if arquivo_alunos is not None:
    try:
        if arquivo_alunos.name.endswith('.csv'):
            df_alunos = pd.read_csv(arquivo_alunos)
        else:
            df_alunos = pd.read_excel(arquivo_alunos)
        
        # Padronizar colunas para busca
        df_alunos.columns = [str(col).strip().capitalize() for col in df_alunos.columns]
        if 'Número' in df_alunos.columns and 'Nome' in df_alunos.columns:
            for _, row in df_alunos.iterrows():
                try:
                    num_key = int(row['Número'])
                    mapa_alunos[num_key] = str(row['Nome']).strip()
                except ValueError:
                    pass
            st.sidebar.success(f"✅ {len(mapa_alunos)} alunos carregados!")
        else:
            st.sidebar.error("A planilha deve conter as colunas 'Número' e 'Nome'.")
    except Exception as e:
        st.sidebar.error("Erro ao ler planilha de alunos.")

# --- FUNÇÃO PARA GERAR O PDF COMPACTO DO GABARITO ---
def gerar_pdf_gabarito(q_total, opt_total):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    num_colunas_questoes = 1 + ((q_total - 1) // 20)
    box_width = 240 + (num_colunas_questoes * 120)
    q_por_coluna = min(q_total, 20)
    box_height = 100 + max(q_por_coluna * 16, 150)

    x_start = 40
    y_top = height - 40
    y_bottom = y_top - box_height
    anchor_size = 16

    c.setFillColorRGB(0, 0, 0)
    c.rect(x_start, y_top - anchor_size, anchor_size, anchor_size, fill=True, stroke=False)
    c.rect(x_start + box_width - anchor_size, y_top - anchor_size, anchor_size, anchor_size, fill=True, stroke=False)
    c.rect(x_start, y_bottom, anchor_size, anchor_size, fill=True, stroke=False)
    c.rect(x_start + box_width - anchor_size, y_bottom, anchor_size, anchor_size, fill=True, stroke=False)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(x_start + 25, y_top - 14, "CARTÃO RESPOSTA")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(x_start + 25, y_top - 32, "NOME:")
    c.line(x_start + 60, y_top - 34, x_start + 220, y_top - 34)

    c.drawString(x_start + 230, y_top - 32, "TURMA:")
    c.line(x_start + 270, y_top - 34, x_start + box_width - 25, y_top - 34)

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

# --- DEFINIÇÃO DO GABARITO OFICIAL ---
st.subheader("1. Gabarito Oficial")
gabarito_oficial = []

for i in range(num_questoes):
    resp = st.selectbox(
        f"Questão {i+1:02d} (Valor: {valor_por_questao} pt)", 
        letras, 
        key=f"gabarito_q_{i+1}"
    )
    gabarito_oficial.append(resp)

# --- INICIALIZAÇÃO DA SESSÃO ---
if "resultados" not in st.session_state:
    st.session_state.resultados = {}  # {numero_int: {"nome": str, "acertos": int, "nota": float}}

st.divider()

# --- LEITURA DO GABARITO DO ALUNO ---
st.subheader("2. Corrigir Cartão Resposta")

st.write("📌 *Ao abrir a câmera pela primeira vez, permita o acesso no seu navegador.*")
foto = st.camera_input("Capturar Gabarito", key="camera_input_aluno")

if foto is not None:
    bytes_data = foto.getvalue()
    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

    num_aluno_str = st.text_input("Nº Frequência do Aluno:", key="input_num_aluno")

    # Tenta preencher automaticamente o nome caso a planilha tenha sido fornecida
    nome_sugerido = ""
    if num_aluno_str.isdigit():
        num_int_check = int(num_aluno_str)
        if num_int_check in mapa_alunos:
            nome_sugerido = mapa_alunos[num_int_check]

    nome_aluno = st.text_input("Nome do Aluno:", value=nome_sugerido, key="input_nome_aluno")

    # TRATAMENTO DE DUPLICIDADE
    duplicado = False
    if num_aluno_str.isdigit():
        num_aluno_int = int(num_aluno_str)
        if num_aluno_int in st.session_state.resultados:
            duplicado = True
            st.warning(f"⚠️ **Atenção:** O Aluno com frequência Nº {num_aluno_int} já foi salvo anteriormente com a nota {st.session_state.resultados[num_aluno_int]['nota']}!")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        txt_botao = "🔄 Substituir Nota" if duplicado else "💾 Salvar Correção"
        if st.button(txt_botao, key="btn_salvar_nota"):
            if not num_aluno_str.isdigit():
                st.error("Insira um número válido para a frequência.")
            else:
                num_aluno_int = int(num_aluno_str)
                acertos_simulados = np.random.randint(0, num_questoes + 1)
                nota = round(acertos_simulados * valor_por_questao, 2)

                st.session_state.resultados[num_aluno_int] = {
                    "nome": nome_aluno if nome_aluno else (mapa_alunos.get(num_aluno_int, "Não informado")),
                    "acertos": acertos_simulados,
                    "nota": nota
                }
                st.success(f"✅ Registrado com sucesso! Nº {num_aluno_int} — Nota: {nota}")
                st.rerun()

# --- TABELA DE RESULTADOS, EDICAO E REMOÇÃO ---
st.divider()
st.subheader("3. Gerenciar e Editar Registros Salvos")

if st.session_state.resultados:
    # Opção de Edição/Apagar individual
    nums_cadastrados = sorted(list(st.session_state.resultados.keys()))
    
    st.markdown("#### ✏️ Alterar ou Apagar Aluno Salvo")
    col_sel, col_nova_nota, col_acoes = st.columns([2, 2, 2])
    
    with col_sel:
        aluno_sel = st.selectbox("Selecione Nº Frequência:", nums_cadastrados, key="sel_aluno_edit")
    
    dados_aluno = st.session_state.resultados[aluno_sel]
    
    with col_nova_nota:
        nova_nota_input = st.number_input(
            "Alterar Nota:", 
            min_value=0.0, 
            max_value=float(num_questoes * valor_por_questao), 
            value=float(dados_aluno["nota"]),
            step=0.5,
            key="input_edit_nota"
        )
        
    with col_acoes:
        st.write("") # Espaçamento
        if st.button("💾 Atualizar Nota", key="btn_update_nota"):
            st.session_state.resultados[aluno_sel]["nota"] = round(nova_nota_input, 2)
            st.success(f"Nota do Nº {aluno_sel} atualizada!")
            st.rerun()
            
        if st.button("🗑️ Apagar Registro", key="btn_delete_aluno"):
            del st.session_state.resultados[aluno_sel]
            st.warning(f"Registro Nº {aluno_sel} removido!")
            st.rerun()

    st.divider()

    # --- GERAR PLANILHA COMPLETA COM FALTANTES ---
    st.subheader("4. Exportar Planilha Final Ordenada")

    # Determinar alcance da sequência numérica (A partir dos alunos cadastrados + lista uploaded)
    todos_numeros = set(st.session_state.resultados.keys())
    if mapa_alunos:
        todos_numeros.update(mapa_alunos.keys())

    max_freq = max(todos_numeros) if todos_numeros else 1
    
    # Construir lista consolidada de 1 até o maior número
    lista_consolidada = []
    for freq in range(1, max_freq + 1):
        if freq in st.session_state.resultados:
            res = st.session_state.resultados[freq]
            lista_consolidada.append({
                "Número": freq,
                "Nome": res["nome"],
                "Acertos": f"{res['acertos']}/{num_questoes}",
                "Nota Final": res["nota"],
                "Status": "Presente"
            })
        else:
            nome_ausente = mapa_alunos.get(freq, "Não informado")
            lista_consolidada.append({
                "Número": freq,
                "Nome": nome_ausente,
                "Acertos": "Não informado",
                "Nota Final": "Não informado",
                "Status": "Ausente"
            })

    df_final = pd.DataFrame(lista_consolidada)
    st.dataframe(df_final, use_container_width=True)

    csv_final = df_final.to_csv(index=False, encoding='utf-8-sig')

    st.download_button(
        label="📊 Baixar Planilha Final (.CSV)",
        data=csv_final,
        file_name="relatorio_notas_alunos.csv",
        mime="text/csv",
        key="btn_download_final_csv"
    )
else:
    st.info("Nenhuma nota registrada ainda.")
