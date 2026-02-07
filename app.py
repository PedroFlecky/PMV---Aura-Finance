import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# --- 1. GESTÃO DE DADOS ---
def iniciar_db():
    conn = sqlite3.connect('financas.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transacoes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, tipo TEXT, categoria TEXT, data DATE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS metas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, objetivo REAL, atual REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orcamentos (categoria TEXT PRIMARY KEY, limite REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS recorrentes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, descricao TEXT, valor REAL, categoria TEXT, tipo TEXT)''')
    try: c.execute("ALTER TABLE recorrentes ADD COLUMN tipo TEXT")
    except: pass 
    conn.commit()
    conn.close()

def salvar_transacao(desc, val, tp, cat, dt):
    if not desc or desc.strip() == "":
        desc = "Gasolina" if cat == "Transporte" else cat
    conn = sqlite3.connect('financas.db')
    c = conn.cursor()
    c.execute("INSERT INTO transacoes (descricao, valor, tipo, categoria, data) VALUES (?, ?, ?, ?, ?)", 
              (desc, val, tp, cat, dt))
    if tp == "Aporte em Meta":
        c.execute("UPDATE metas SET atual = atual + ? WHERE nome = ?", (val, cat))
    conn.commit()
    conn.close()

def deletar_registros_massa(ids):
    conn = sqlite3.connect('financas.db')
    c = conn.cursor()
    for id_reg in ids:
        res = c.execute("SELECT tipo, valor, categoria FROM transacoes WHERE id = ?", (id_reg,)).fetchone()
        if res and res[0] == "Aporte em Meta":
            c.execute("UPDATE metas SET atual = atual - ? WHERE nome = ?", (res[1], res[2]))
        c.execute("DELETE FROM transacoes WHERE id = ?", (id_reg,))
    conn.commit()
    conn.close()

iniciar_db()

# --- 2. MOTOR VISUAL AURA TITAN ---
st.set_page_config(page_title="Aura OS Finance", layout="wide", page_icon="🌌")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;900&family=Inter:wght@400;600&display=swap');
    
    @keyframes ps3Wave {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .stApp {
        background: linear-gradient(-45deg, #1a0b2e, #300c41, #0f172a, #280a1a);
        background-size: 300% 300%;
        animation: ps3Wave 20s ease infinite;
        color: #f1f5f9 !important;
        font-family: 'Inter', sans-serif;
    }

    /* FONTES GIGANTES */
    html, body, p, div, label, span { font-size: 18px !important; }
    h1 { font-size: 4rem !important; font-weight: 900 !important; color: #f1f5f9 !important; }
    h2 { font-size: 2.5rem !important; font-weight: 700 !important; color: #f1f5f9 !important; }
    h3 { font-size: 2rem !important; font-weight: 600 !important; color: #f1f5f9 !important; }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 15, 20, 0.6) !important;
        backdrop-filter: blur(25px);
        border-right: 1px solid rgba(255,255,255, 0.1);
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        font-size: 1.1rem !important; color: #f1f5f9 !important;
    }

    /* INPUTS */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div, .stDateInput input, .stNumberInput input {
        background-color: rgba(255, 255, 255, 0.08) !important;
        color: #fff !important;
        font-size: 1.3rem !important;
        height: 3.5rem !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255, 0.2) !important;
    }
    
    div[data-testid="stWidgetLabel"] p {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        color: #a64dff !important;
    }

    /* BOTÕES */
    .stButton button {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        padding: 0.8rem 2rem !important;
        border-radius: 12px !important;
        height: auto !important; color: #f1f5f9 !important;
    }

    /* CARDS */
    .custom-card {
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(15px);
        padding: 30px;
        border-radius: 24px;
        border: 1px solid rgba(255,255,255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        margin-bottom: 25px;
    }
    
    /* ABAS */
    .stTabs [data-baseweb="tab-list"] { gap: 15px; }
    .stTabs [data-baseweb="tab"] {
        padding: 15px 35px;
        border-radius: 15px; 
        background-color: rgba(255, 255, 255, 0.05);
        color: #cbd5e1; border: none;
    }
    .stTabs [data-baseweb="tab"] p {
        font-size: 1.5rem !important; font-weight: 800 !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #a64dff !important;
        color: white !important;
        box-shadow: 0 0 20px rgba(166, 77, 255, 0.5);
    }
    
    [data-testid="stDataFrame"] { background-color: transparent !important; }

    .aura-title {
        font-family: 'Montserrat', sans-serif; font-weight: 800; 
        background: linear-gradient(90deg, #ff4d4d, #a64dff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Auxiliares
def formata_br(valor): return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
def limpa_valor(texto):
    if not texto: return 0.0
    try: return float(texto.replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.'))
    except: return 0.0

# --- 3. DADOS ---
conn = sqlite3.connect('financas.db')
df = pd.read_sql_query("SELECT * FROM transacoes", conn)
df_metas = pd.read_sql_query("SELECT * FROM metas", conn)
df_orc = pd.read_sql_query("SELECT * FROM orcamentos", conn)
df_rec = pd.read_sql_query("SELECT * FROM recorrentes", conn)
conn.close()

if not df.empty:
    df['data'] = pd.to_datetime(df['data'])
    df['mes_ano'] = df['data'].dt.strftime('%m/%Y')
    meses_disponiveis = sorted(df['mes_ano'].unique(), reverse=True)
else:
    meses_disponiveis = [datetime.now().strftime('%m/%Y')]

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='font-family:Montserrat;'>Lançamentos</h2>", unsafe_allow_html=True)
    t_sel = st.selectbox("Tipo", ["Despesa", "Receita", "Aporte em Meta"], key="side_t")
    
    if t_sel == "Receita": cats = ["Salário", "Poker", "Freelance", "Extra", "Outros"]
    elif t_sel == "Despesa": cats = ["Alimentação", "Transporte", "Lazer", "Contas", "Saúde", "Educação", "Outros"]
    else: cats = df_metas['nome'].tolist() if not df_metas.empty else ["Crie uma meta"]
    
    c_sel = st.selectbox("Categoria", cats, key="side_c")
    d_sel = st.text_input("Descrição", placeholder="Ex: Mercado", key="side_d")
    v_raw = st.text_input("Valor (R$)", placeholder="0,00", key="side_v")
    v_fin = limpa_valor(v_raw)
    dt_sel = st.date_input("Data", datetime.now(), key="side_dt")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⚡ REGISTRAR", use_container_width=True, key="btn_reg"):
        if v_fin > 0:
            salvar_transacao(d_sel, v_fin, t_sel, c_sel, dt_sel)
            st.rerun()

# --- 5. DASHBOARD ---
st.markdown("<h1 class='aura-title'>Aura OS Finance</h1>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💎 Dashboard", "🎯 Metas", "⚠️ Limites", "📊 Evolução", "⚙️ Ajustes"])

with tab1:
    m_sel = st.selectbox("Mês de Referência:", meses_disponiveis, key="dash_m")
    if not df.empty: df_f = df[df['mes_ano'] == m_sel]
    else: df_f = pd.DataFrame(columns=df.columns)

    if not df_rec.empty:
        with st.expander("📅 Lançar Recorrências (Salário e Contas)", expanded=True):
            if st.button("🚀 Processar Lançamentos do Mês", key="btn_auto"):
                dt_a = datetime.strptime(m_sel, '%m/%Y').strftime('%Y-%m-01')
                conn = sqlite3.connect('financas.db'); c = conn.cursor()
                for _, r in df_rec.iterrows():
                    c.execute("INSERT INTO transacoes (descricao, valor, categoria, tipo, data) VALUES (?,?,?,?,?)", (r['descricao'], r['valor'], r['categoria'], r['tipo'], dt_a))
                conn.commit(); conn.close(); st.rerun()
    else:
        st.info("💡 Vá na aba 'Ajustes' para configurar Salário e Contas Fixas.")

    rec_s = df_f[df_f['tipo']=='Receita']['valor'].sum() if not df_f.empty else 0.0
    sai_s = df_f[df_f['tipo'].isin(['Despesa','Aporte em Meta'])]['valor'].sum() if not df_f.empty else 0.0
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='custom-card'><h3>Entradas</h3><h2><span style='color:#34d399 !important'>{formata_br(rec_s)}</span></h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='custom-card'><h3>Saídas</h3><h2><span style='color:#ef4444 !important'>{formata_br(sai_s)}</span></h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='custom-card'><h3>Saldo</h3><h2>{formata_br(rec_s - sai_s)}</h2></div>", unsafe_allow_html=True)

    if not df_orc.empty:
        st.write("---")
        st.caption("Visão Rápida dos Limites (Detalhes na aba 'Limites')")
        cols_o = st.columns(len(df_orc))
        for i, row in df_orc.iterrows():
            gasto = df_f[(df_f['categoria'] == row['categoria']) & (df_f['tipo'] == 'Despesa')]['valor'].sum() if not df_f.empty else 0.0
            saldo_limite = row['limite'] - gasto
            if saldo_limite < 0:
                with cols_o[i]:
                    st.markdown(f"🚨 **{row['categoria']}**: Estourou {formata_br(saldo_limite)}")

    st.write("---")
    col_pie, col_tab = st.columns([1, 1.5])
    
    with col_pie:
        st.subheader("Distribuição")
        if not df_f.empty:
            df_p = df_f[df_f['tipo']=='Despesa']
            if not df_p.empty:
                fig_p = px.pie(df_p, values='valor', names='categoria', hole=0.6, template="plotly_dark")
                fig_p.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig_p, use_container_width=True)
            else: st.caption("Sem despesas.")
        else: st.caption("Sem dados.")
    
    with col_tab:
        st.subheader("Histórico Visual")
        if not df_f.empty:
            df_show = df_f.sort_values(by='data', ascending=False)
            event = st.dataframe(
                df_show,
                column_order=("data", "descricao", "categoria", "tipo", "valor"),
                column_config={
                    "data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                    "descricao": st.column_config.TextColumn("Descrição"),
                    "categoria": st.column_config.TextColumn("Categoria"),
                    "tipo": st.column_config.TextColumn("Tipo"),
                    "valor": st.column_config.ProgressColumn("Valor", format="R$ %.2f", min_value=0, max_value=float(df_f['valor'].max())),
                },
                use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row"
            )
            if event.selection.rows:
                ids = df_show.iloc[event.selection.rows]['id'].tolist()
                if st.button(f"🗑️ Excluir {len(ids)} item(s)", type="primary"):
                    deletar_registros_massa(ids); st.rerun()
        else: st.info("Nenhum lançamento.")

# --- ABA 2: METAS (COM GESTÃO) ---
with tab2:
    st.subheader("🎯 Gestão de Objetivos")
    col_add_m, col_rem_m = st.columns(2)
    
    with col_add_m:
        with st.container(border=True):
            st.write("### ➕ Nova Meta")
            nm = st.text_input("Nome", key="new_meta_name")
            vm = st.text_input("Alvo (R$)", key="new_meta_val")
            if st.button("Criar Meta", use_container_width=True):
                v = limpa_valor(vm)
                if v and nm:
                    conn = sqlite3.connect('financas.db')
                    conn.execute("INSERT INTO metas (nome,objetivo,atual) VALUES (?,?,0)", (nm, v))
                    conn.commit(); conn.close(); st.success("Meta Criada!"); st.rerun()

    with col_rem_m:
        with st.container(border=True):
            st.write("### 🗑️ Excluir Meta")
            if not df_metas.empty:
                meta_to_del = st.selectbox("Selecionar Meta:", df_metas['nome'].tolist(), key="del_meta_sel")
                if st.button("Excluir Selecionada", type="primary", use_container_width=True):
                    conn = sqlite3.connect('financas.db')
                    conn.execute("DELETE FROM metas WHERE nome = ?", (meta_to_del,))
                    conn.commit(); conn.close(); st.warning("Meta removida."); st.rerun()
            else:
                st.info("Nenhuma meta para excluir.")

    st.write("---")
    if not df_metas.empty:
        for _, m in df_metas.iterrows():
            prog = (m['atual'] / m['objetivo']) if m['objetivo'] > 0 else 0
            with st.container(border=True):
                cm, cl = st.columns([3, 1])
                with cm:
                    st.write(f"### {m['nome']}"); st.progress(min(prog, 1.0))
                    c1,c2,c3=st.columns(3)
                    c1.write(f"**{prog:.1%}**"); c2.write(f"💰 {formata_br(m['atual'])}"); c3.write(f"🎯 {formata_br(m['objetivo'])}")
                with cl: st.metric("Falta", formata_br(max(m['objetivo'] - m['atual'], 0)))
    else: st.info("Defina suas metas acima.")

# --- ABA 3: LIMITES ---
with tab3:
    st.subheader("⚠️ Gerenciar Limites")
    col_add, col_rem = st.columns(2)

    with col_add:
        with st.container(border=True):
            st.write("### ➕ Definir Limite")
            cl = st.selectbox("Categoria", ["Alimentação", "Transporte", "Lazer", "Contas", "Outros"], key="lim_cat")
            vl = st.text_input("Limite (R$)", key="lim_val")
            if st.button("Salvar Limite", use_container_width=True):
                v = limpa_valor(vl)
                if v:
                    conn = sqlite3.connect('financas.db')
                    conn.execute("INSERT OR REPLACE INTO orcamentos (categoria, limite) VALUES (?, ?)", (cl, v))
                    conn.commit(); conn.close(); st.success("Atualizado!"); st.rerun()

    with col_rem:
        with st.container(border=True):
            st.write("### 🗑️ Excluir Limite")
            if not df_orc.empty:
                lim_to_del = st.selectbox("Selecione para remover:", df_orc['categoria'].tolist(), key="del_lim_sel")
                if st.button("Excluir Limite", type="primary", use_container_width=True):
                    conn = sqlite3.connect('financas.db')
                    conn.execute("DELETE FROM orcamentos WHERE categoria = ?", (lim_to_del,))
                    conn.commit(); conn.close(); st.warning("Removido."); st.rerun()
            else:
                st.info("Nenhum limite cadastrado.")

    st.write("---")
    if not df_orc.empty:
        cols_o = st.columns(2)
        for i, row in df_orc.iterrows():
            col_idx = i % 2
            gasto = df_f[(df_f['categoria'] == row['categoria']) & (df_f['tipo'] == 'Despesa')]['valor'].sum() if not df_f.empty else 0.0
            saldo_limite = row['limite'] - gasto
            progresso = min(gasto / row['limite'], 1.0) if row['limite'] > 0 else 1.0

            with cols_o[col_idx]:
                with st.container(border=True):
                    st.write(f"### {row['categoria']}")
                    st.progress(progresso)
                    if saldo_limite >= 0:
                        st.caption(f"✅ Livre: {formata_br(saldo_limite)}")
                    else:
                        st.markdown(f"<span style='color:#ff4d4d; font-weight:bold'>🚨 Estourou: {formata_br(saldo_limite)}</span>", unsafe_allow_html=True)
    else: st.info("Defina limites acima.")

# --- ABA 4: EVOLUÇÃO ---
with tab4:
    st.subheader("📊 Evolução")
    if not df.empty:
        df_e = df.groupby(['mes_ano', 'tipo'])['valor'].sum().reset_index()
        df_e['dt'] = pd.to_datetime(df_e['mes_ano'], format='%m/%Y')
        fig = px.line(df_e.sort_values('dt'), x='mes_ano', y='valor', color='tipo', markers=True, template="plotly_dark", line_shape='spline')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Sem dados.")

# --- ABA 5: AJUSTES (RESTAURADA) ---
with tab5:
    st.subheader("⚙️ Configuração Automática")
    
    col_sal, col_fixos = st.columns(2)
    
    with col_sal:
        with st.container(border=True):
            st.write("### 🏠 Salário Mensal")
            s = st.text_input("Valor do Salário (R$)", key="aj_s")
            if st.button("Salvar Salário Padrão", use_container_width=True):
                v=limpa_valor(s)
                if v: 
                    conn=sqlite3.connect('financas.db')
                    conn.execute("DELETE FROM recorrentes WHERE categoria='Salário'")
                    conn.execute("INSERT INTO recorrentes (descricao,valor,categoria,tipo) VALUES (?,?,?,?)",("Salário",v,"Salário","Receita"))
                    conn.commit(); conn.close(); st.success("Salário definido! Irá aparecer no botão de lançar do Dashboard."); st.rerun()

    with col_fixos:
        with st.container(border=True):
            st.write("### 📄 Contas Fixas (Todo Mês)")
            n_f=st.text_input("Nome da Conta (ex: Aluguel)", key="aj_n")
            v_f=st.text_input("Valor (R$)", key="aj_v")
            if st.button("Adicionar Conta Fixa", use_container_width=True):
                v=limpa_valor(v_f)
                if v and n_f: 
                    conn=sqlite3.connect('financas.db')
                    conn.execute("INSERT INTO recorrentes (descricao,valor,categoria,tipo) VALUES (?,?,?,?)",(n_f,v,"Contas","Despesa"))
                    conn.commit(); conn.close(); st.success(f"Conta '{n_f}' adicionada!"); st.rerun()
            
    # Tabela para ver o que já está cadastrado
    st.write("---")
    st.write("### 📋 Itens Automáticos Cadastrados:")
    if not df_rec.empty:
        st.dataframe(df_rec[['descricao', 'valor', 'tipo']], use_container_width=True, hide_index=True)
        # Opção de limpar tudo se quiser recomeçar
        if st.button("🗑️ Limpar Todas as Recorrências", type="secondary"):
            conn=sqlite3.connect('financas.db'); conn.execute("DELETE FROM recorrentes"); conn.commit(); conn.close(); st.rerun()
    else:
        st.info("Nenhuma conta fixa ou salário cadastrado ainda.")
