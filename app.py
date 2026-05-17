import streamlit as st
import pandas as pd

# 必須寫在第一行
st.set_page_config(page_title="麻將結算", page_icon="🀄", layout="centered")

# ==========================================
# 🎨 極簡風格 CSS (無印/Apple風)
# ==========================================
st.markdown("""
<style>
    /* 隱藏頂部裝飾條與預設選單空間 */
    header {visibility: hidden;}

    /* 極簡淺色背景與字體設定 */
    .stApp {
        background-color: #FAFAFA;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* 側邊欄乾淨白底 */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #F0F0F0;
    }

    /* 簡約記分板卡片 (去除厚重陰影，改用極細邊框) */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        padding: 20px 10px;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
        text-align: center;
    }
    div[data-testid="stMetricDelta"] svg { display: none; }

    /* 簡約標籤頁 (底線風格，去除區塊背景) */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        border-bottom: 1px solid #E5E7EB;
        gap: 20px;
        justify-content: center;
        padding-bottom: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 500;
        padding: 8px 4px;
        color: #9CA3AF;
        border: none;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #111827 !important;
        border-bottom: 2px solid #111827 !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    /* 極簡黑按鈕 */
    button[kind="primary"] {
        background: #111827 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        transition: opacity 0.2s;
    }
    button[kind="primary"]:hover {
        opacity: 0.8 !important;
        transform: none !important;
    }

    /* 隱藏元素背景，保持留白 */
    [data-testid="stVerticalBlock"] {
        background: transparent;
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
    st.markdown("### 遊戲設定")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.base = st.number_input("底 (元)", value=st.session_state.base, step=10)
    with col2:
        st.session_state.tai = st.number_input("台 (元)", value=st.session_state.tai, step=10)
        
    st.divider()
    
    st.markdown("### 玩家名單")
    st.caption("留白即隱藏，不參與結算。")
    for i in range(6):
        st.session_state.names[i] = st.text_input(
            f"座位 {i+1}", 
            value=st.session_state.names[i], 
            placeholder=f"玩家 {i+1}",
            label_visibility="collapsed"
        )
        
    st.divider()
    if st.button("清空所有資料", type="primary", use_container_width=True):
        st.session_state.balances = [0] * 6
        st.session_state.records = []
        st.rerun()

active_players = [(i, name) for i, name in enumerate(st.session_state.names) if name.strip()]

# ==========================================
# 主畫面
# ==========================================
st.markdown("<h2 style='text-align: center; color: #111827; margin-bottom: 20px;'>麻將結算</h2>", unsafe_allow_html=True)

tab_board, tab_record, tab_history = st.tabs(["戰況結算", "登記牌局", "歷史對帳"])

# --- Tab 1: 戰況結算 ---
with tab_board:
    st.write("") # 增加留白
    
    cols = st.columns(3)
    for idx, (original_idx, name) in enumerate(active_players):
        bal = st.session_state.balances[original_idx]
        color = "off" if bal == 0 else ("normal" if bal > 0 else "inverse")
        delta_str = f"+{bal}" if bal > 0 else str(bal)
        with cols[idx % 3]:
            st.metric(label=name, value=bal, delta=delta_str if bal!=0 else "平", delta_color=color)

    st.divider()
    
    st.markdown("#### 轉帳清算")
    temp_bal = [{"name": name, "bal": st.session_state.balances[idx]} for idx, name in active_players]
    creditors = sorted([p for p in temp_bal if p["bal"] > 0], key=lambda x: x["bal"], reverse=True)
    debtors = sorted([p for p in temp_bal if p["bal"] < 0], key=lambda x: x["bal"])

    if not creditors or not debtors:
        st.info("目前無待轉帳款項。")
    else:
        c_idx, d_idx = 0, 0
        while c_idx < len(creditors) and d_idx < len(debtors):
            creditor = creditors[c_idx]
            debtor = debtors[d_idx]
            
            transfer = min(-debtor["bal"], creditor["bal"])
            if transfer > 0:
                st.success(f"{debtor['name']} ➔ 轉給 {creditor['name']}： {transfer} 元")
                
            creditor["bal"] -= transfer
            debtor["bal"] += transfer
            
            if abs(creditor["bal"]) < 0.1: c_idx += 1
            if abs(debtor["bal"]) < 0.1: d_idx += 1

# --- Tab 2: 登記牌局 ---
with tab_record:
    st.write("") # 增加留白
    
    st.markdown("#### 1. 輸贏設定")
    player_options = [p[1] for p in active_players]
    
    c1, c2, c3 = st.columns(3)
    with c1:
        winner_name = st.selectbox("贏家", options=player_options)
    with c2:
        win_type = st.selectbox("方式", options=["放槍", "自摸"])
    with c3:
        loser_options = [p for p in player_options if p != winner_name]
        loser_name = st.selectbox("苦主", options=loser_options, disabled=(win_type=="自摸"))

    st.write("")
    st.markdown("#### 2. 台數計算")
    tai_dict = {
        "莊家 (+1)": 1, "門清 (+1)": 1, "自摸 (+1)": 1, 
        "平胡 (+2)": 2, "三暗刻 (+2)": 2, "全求人 (+2)": 2,
        "碰碰胡 (+4)": 4, "混一色 (+4)": 4, "小三元 (+4)": 4,
        "清一色 (+8)": 8, "大三元 (+8)": 8
    }
    
    selected_tais = st.multiselect("快速台數 (可複選)", options=list(tai_dict.keys()), label_visibility="collapsed")
    auto_tai = sum([tai_dict[k] for k in selected_tais])
    
    c4, c5 = st.columns([2, 1])
    with c4:
        manual_tai = st.number_input("手動附加台數", value=0, min_value=0, step=1)
    with c5:
        total_tai = auto_tai + manual_tai
        st.metric("總計台數", f"{total_tai} 台")

    st.write("")
    if st.button("確認登記", type="primary", use_container_width=True):
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
            "苦主": "-" if win_type == "自摸" else loser_name,
            "台數": total_tai,
            "異動": f"-{amount} /家" if win_type == "自摸" else f"-{amount}"
        })
        
        st.toast("登記成功")
        st.rerun()

# --- Tab 3: 歷史對帳 ---
with tab_history:
    st.write("")
    if not st.session_state.records:
        st.caption("尚無紀錄")
    else:
        df = pd.DataFrame(reversed(st.session_state.records))
        df.index = [len(st.session_state.records) - i for i in range(len(st.session_state.records))]
        st.dataframe(df, use_container_width=True)
