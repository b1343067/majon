import streamlit as st
import pandas as pd

# 必須寫在第一行，預設把側邊欄打開
st.set_page_config(page_title="麻將結算神器", page_icon="🀄", layout="centered", initial_sidebar_state="expanded")

# ==========================================
# 🎨 V5 尊爵黑金奢華風 CSS (VIP Casino Style)
# ==========================================
st.markdown("""
<style>
    /* 讓頂部裝飾條變透明，保留選單按鈕但不突兀 */
    header {background: transparent !important;}

    /* 奢華黑漸層背景 */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #2b2b2b, #111111, #000000);
        color: #E8E8E8;
    }

    /* 側邊欄深邃質感 */
    [data-testid="stSidebar"] {
        background-color: #141414;
        border-right: 1px solid #D4AF37; /* 香檳金邊框 */
    }

    /* 👑 奢華金邊記分板卡片 */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #1f1f1f, #121212) !important;
        border: 1px solid #D4AF37 !important;
        padding: 20px 10px;
        border-radius: 12px;
        box-shadow: 0 5px 15px rgba(212, 175, 55, 0.15) !important;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(212, 175, 55, 0.3) !important;
    }
    
    /* 讓玩家名字和數字呈現金色質感 */
    div[data-testid="metric-container"] label {
        color: #F3E5AB !important; /* 柔和淺金 */
        font-size: 1.1rem;
        font-weight: 600;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #D4AF37 !important; /* 香檳金 */
        font-weight: 800;
    }
    div[data-testid="stMetricDelta"] svg { display: none; }

    /* 👑 奢華金標籤頁 */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        border-bottom: 1px solid #333;
        gap: 20px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 500;
        color: #666;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #D4AF37 !important;
        border-bottom: 2px solid #D4AF37 !important;
        text-shadow: 0 0 10px rgba(212, 175, 55, 0.3);
    }

    /* 👑 金屬光澤主按鈕 */
    button[kind="primary"] {
        background: linear-gradient(45deg, #B8860B, #FFD700, #DAA520) !important;
        color: #111111 !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 15px rgba(218, 165, 32, 0.4) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease !important;
    }
    button[kind="primary"]:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.6) !important;
    }

    /* 標題與分隔線美化 */
    h1, h2, h3 {
        color: #D4AF37 !important;
    }
    hr {
        border-color: rgba(212, 175, 55, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 狀態初始化 ---
if 'init' not in st.session_state:
    st.session_state.base = 100
    st.session_state.tai = 20
    st.session_state.names = ["東風", "南風", "西風", "北風", "", ""]
    st.session_state.balances = [0] * 6
    st.session_state.records = []
    st.session_state.init = True

# ==========================================
# 側邊欄 (Sidebar)
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ 遊戲設定")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.base = st.number_input("底 (元)", value=st.session_state.base, step=10)
    with col2:
        st.session_state.tai = st.number_input("台 (元)", value=st.session_state.tai, step=10)
        
    st.divider()
    
    st.markdown("### 👥 玩家名單")
    st.caption("留白即隱藏，不參與結算。")
    for i in range(6):
        st.session_state.names[i] = st.text_input(
            f"座位 {i+1}", 
            value=st.session_state.names[i], 
            placeholder=f"玩家 {i+1}",
            label_visibility="collapsed"
        )
        
    st.divider()
    if st.button("🚨 清空所有資料", type="primary", use_container_width=True):
        st.session_state.balances = [0] * 6
        st.session_state.records = []
        st.rerun()

active_players = [(i, name) for i, name in enumerate(st.session_state.names) if name.strip()]

# ==========================================
# 主畫面
# ==========================================
st.markdown("<h1 style='text-align: center; margin-bottom: 10px; text-shadow: 0px 2px 10px rgba(212,175,55,0.3);'>🀄 皇家麻將結算中心</h1>", unsafe_allow_html=True)

tab_board, tab_record, tab_history = st.tabs(["📊 戰況結算", "📝 登記牌局", "📜 歷史對帳"])

# --- Tab 1: 戰況結算 ---
with tab_board:
    st.write("") 
    cols = st.columns(3)
    for idx, (original_idx, name) in enumerate(active_players):
        bal = st.session_state.balances[original_idx]
        # 金色主題下，贏錢顯示正號，輸錢顯示負號，不再硬上紅綠色
        delta_str = f"+{bal}" if bal > 0 else str(bal)
        with cols[idx % 3]:
            st.metric(label=name, value=bal, delta=delta_str if bal!=0 else "平手", delta_color="off")

    st.divider()
    
    st.markdown("### 💸 最佳化轉帳清算")
    temp_bal = [{"name": name, "bal": st.session_state.balances[idx]} for idx, name in active_players]
    creditors = sorted([p for p in temp_bal if p["bal"] > 0], key=lambda x: x["bal"], reverse=True)
    debtors = sorted([p for p in temp_bal if p["bal"] < 0], key=lambda x: x["bal"])

    if not creditors or not debtors:
        st.info("🥂 目前大家平手或無戰況，暫不需進行任何轉帳！")
    else:
        c_idx, d_idx = 0, 0
        with st.container(border=True):
            while c_idx < len(creditors) and d_idx < len(debtors):
                creditor = creditors[c_idx]
                debtor = debtors[d_idx]
                
                transfer = min(-debtor["bal"], creditor["bal"])
                if transfer > 0:
                    st.success(f"💸 **{debtor['name']}** ➔ 轉給 👑 **{creditor['name']}** ： **{transfer} 元**")
                    
                cred
