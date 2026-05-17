import streamlit as st
import pandas as pd

# 必須寫在第一行
st.set_page_config(page_title="🀄 麻將結算神器", page_icon="🀄", layout="centered")

# ==========================================
# 🎨 終極視覺強化 CSS (毛玻璃、發光、漸層)
# ==========================================
st.markdown("""
<style>
    /* 隱藏頂部裝飾條 */
    header {visibility: hidden;}

    /* App 級別深色漸層背景 */
    .stApp {
        background: linear-gradient(135deg, #141e30, #243b55);
    }

    /* 側邊欄深色化 */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
    }

    /* 🌟 毛玻璃記分板卡片 (Glassmorphism) */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding: 20px 10px;
        border-radius: 16px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        text-align: center;
        transition: all 0.3s ease !important;
    }

    /* 🌟 記分板滑鼠懸浮發光特效 */
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 0 25px rgba(0, 210, 255, 0.5) !important;
        border-color: rgba(0, 210, 255, 0.7) !important;
    }

    /* 隱藏預設箭頭 */
    div[data-testid="stMetricDelta"] svg { display: none; }

    /* 🌟 標籤頁美化 (更像現代 App) */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(0,0,0,0.3);
        border-radius: 12px;
        padding: 5px;
        gap: 5px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 8px;
        color: #8b9bb4;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.15) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    }

    /* 🌟 漸層主按鈕特效 */
    button[kind="primary"] {
        background: linear-gradient(45deg, #ff416c, #ff4b2b) !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(255, 75, 43, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    button[kind="primary"]:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 6px 20px rgba(255, 75, 43, 0.6) !important;
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
    st.title("⚙️ 遊戲設定")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.base = st.number_input("底 (元)", value=st.session_state.base, step=10)
    with col2:
        st.session_state.tai = st.number_input("台 (元)", value=st.session_state.tai, step=10)
        
    st.divider()
    
    st.subheader("👥 玩家名單")
    for i in range(6):
        st.session_state.names[i] = st.text_input(
            f"座位 {i+1}", 
            value=st.session_state.names[i], 
            placeholder=f"玩家 {i+1}"
        )
        
    st.divider()
    if st.button("🚨 結算並清空全部資料", type="primary", use_container_width=True):
        st.session_state.balances = [0] * 6
        st.session_state.records = []
        st.rerun()

active_players = [(i, name) for i, name in enumerate(st.session_state.names) if name.strip()]

# ==========================================
# 主畫面
# ==========================================
st.title("🀄 麻將結算神器")

tab_board, tab_record, tab_history = st.tabs(["📊 戰況結算", "📝 登記牌局", "📜 歷史對帳"])

# --- Tab 1: 戰況結算 ---
with tab_board:
    st.subheader("即時戰況餘額")
    
    cols = st.columns(3)
    for idx, (original_idx, name) in enumerate(active_players):
        bal = st.session_state.balances[original_idx]
        color = "off" if bal == 0 else ("normal" if bal > 0 else "inverse")
        delta_str = f"+{bal}" if bal > 0 else str(bal)
        with cols[idx % 3]:
            st.metric(label=name, value=bal, delta=delta_str if bal!=0 else "平手", delta_color=color)

    st.divider()
    
    st.subheader("💸 最佳化轉帳清算")
    temp_bal = [{"name": name, "bal": st.session_state.balances[idx]} for idx, name in active_players]
    creditors = sorted([p for p in temp_bal if p["bal"] > 0], key=lambda x: x["bal"], reverse=True)
    debtors = sorted([p for p in temp_bal if p["bal"] < 0], key=lambda x: x["bal"])

    if not creditors or not debtors:
        st.info("👏 目前大家平手或無戰況，暫不需進行任何轉帳！")
    else:
        c_idx, d_idx = 0, 0
        with st.container(border=True):
            while c_idx < len(creditors) and d_idx < len(debtors):
                creditor = creditors[c_idx]
                debtor = debtors[d_idx]
                
                transfer = min(-debtor["bal"], creditor["bal"])
                if transfer > 0:
                    st.success(f"**{debtor['name']}** ➔ 轉給 👑 **{creditor['name']}** : **{transfer} 元**")
                    
                creditor["bal"] -= transfer
                debtor["bal"] += transfer
                
                if abs(creditor["bal"]) < 0.1: c_idx += 1
                if abs(debtor["bal"]) < 0.1: d_idx += 1

# --- Tab 2: 登記牌局 ---
with tab_record:
    with st.container(border=True):
        st.subheader("1. 選擇輸贏家")
        player_options = [p[1] for p in active_players]
        
        c1, c2, c3 = st.columns(3)
        with c1:
            winner_name = st.selectbox("👑 贏家 (胡牌)", options=player_options)
        with c2:
            win_type = st.selectbox("🎲 方式", options=["放槍", "自摸"])
        with c3:
            loser_options = [p for p in player_options if p != winner_name]
            loser_name = st.selectbox("😭 放槍苦主", options=loser_options, disabled=(win_type=="自摸"))

    with st.container(border=True):
        st.subheader("2. 台數計算機")
        tai_dict = {
            "莊家/連莊 (+1)": 1, "門清 (+1)": 1, "自摸 (+1)": 1, 
            "平胡 (+2)": 2, "三暗刻 (+2)": 2, "全求人 (+2)": 2,
            "碰碰胡 (+4)": 4, "混一色 (+4)": 4, "小三元 (+4)": 4,
            "清一色 (+8)": 8, "大三元 (+8)": 8
        }
        
        selected_tais = st.multiselect("☑️ 快速點選 (可複選)", options=list(tai_dict.keys()))
        auto_tai = sum([tai_dict[k] for k in selected_tais])
        
        c4, c5 = st.columns(2)
        with c4:
            manual_tai = st.number_input("➕ 其他台數 (手動加總)", value=0, min_value=0, step=1)
        with c5:
            total_tai = auto_tai + manual_tai
            st.metric("總台數", f"{total_tai} 台")

    if st.button("✅ 結算此局並登記", type="primary", use_container_width=True):
        amount = st.session_state.base + (total_tai * st.session_state.tai)
        
        winner_idx = next(i for i, name in active_players if name == winner_name)
        loser_idx = next(i for i, name in active_players if name == loser_name) if win_type == "放槍" else None
        
        if win_type == "自摸":
            in_game_count = len(active_players)
            st.session_state.balances[winner_idx] += amount * (in_game_count - 1)
            for i, name in active_players:
                if i != winner_idx:
                    st.session_state.balances[i] -= amount
        else:
            st.session_state.balances[winner_idx] += amount
            st.session_state.balances[loser_idx] -= amount
            
        st.session_state.records.append({
            "贏家": winner_name,
            "方式": win_type,
            "苦主": "其餘玩家" if win_type == "自摸" else loser_name,
            "台數": total_tai,
            "金額變動": f"每家 -{amount}" if win_type == "自摸" else f"苦主 -{amount}"
        })
        
        # 🌟 隱藏彩蛋：大牌慶祝特效
        if total_tai >= 5:
            st.balloons()
            
        st.toast("✅ 登記成功！已更新戰況")
        st.rerun()

# --- Tab 3: 歷史對帳 ---
with tab_history:
    if not st.session_state.records:
        st.caption("目前尚無任何牌局紀錄。")
    else:
        df = pd.DataFrame(reversed(st.session_state.records))
        df.index = [len(st.session_state.records) - i for i in range(len(st.session_state.records))]
        st.dataframe(df, use_container_width=True)
