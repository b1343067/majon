import streamlit as st
import pandas as pd
import urllib.parse  # 處理 LINE 網址文字編碼的新工具

# 必須寫在第一行
st.set_page_config(page_title="麻將結算大師", page_icon="🀄", layout="centered")

# --- 注入美化 CSS (修復手機版側邊欄按鈕消失的問題) ---
st.markdown("""
<style>
    /* 將頂部裝飾條變透明，保留手機版的展開按鈕 */
    header {background: transparent !important;}

    /* 極簡淺色背景與字體 */
    .stApp {
        background-color: #FAFAFA;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* 側邊欄乾淨白底 */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #F0F0F0;
    }

    /* 簡約記分板卡片 */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E7EB !important;
        padding: 20px 10px;
        border-radius: 8px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02) !important;
        text-align: center;
    }
    div[data-testid="stMetricDelta"] svg { display: none; }

    /* 簡約標籤頁 */
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

    /* 極簡深色按鈕 */
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
    st.session_state.chart_history = [] 
    st.session_state.show_final = False 
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
    if st.button("清空所有資料重來", type="primary", use_container_width=True):
        st.session_state.balances = [0] * 6
        st.session_state.records = []
        st.session_state.chart_history = []
        st.session_state.show_final = False
        st.rerun()

active_players = [(i, name) for i, name in enumerate(st.session_state.names) if name.strip()]

# ==========================================
# 主畫面
# ==========================================
st.markdown("<h2 style='text-align: center; color: #111827; margin-bottom: 20px;'>麻將結算</h2>", unsafe_allow_html=True)

tab_board, tab_record, tab_history = st.tabs(["戰況結算", "登記牌局", "歷史對帳"])

# --- Tab 1: 戰況結算 ---
with tab_board:
    st.write("") 
    
    cols = st.columns(3)
    for idx, (original_idx, name) in enumerate(active_players):
        bal = st.session_state.balances[original_idx]
        color = "off" if bal == 0 else ("normal" if bal > 0 else "inverse")
        delta_str = f"+{bal}" if bal > 0 else str(bal)
        with cols[idx % 3]:
            st.metric(label=name, value=bal, delta=delta_str if bal!=0 else "平", delta_color=color)

    st.divider()
    
    st.markdown("#### 轉帳清算建議")
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

    st.divider()
    
    if not st.session_state.records:
        st.caption("暫無歷史數據，登記單局後即可解鎖終場大數據統計。")
    else:
        if not st.session_state.show_final:
            if st.button("🏆 展開今晚終場大數據總結算", type="primary", use_container_width=True):
                st.session_state.show_final = True
                st.balloons() 
                st.rerun()
        else:
            if st.button("🔼 收合終場大數據統計", use_container_width=True):
                st.session_state.show_final = False
                st.rerun()

        if st.session_state.show_final and st.session_state.records:
            st.write("")
            st.markdown("<h3 style='text-align: center; color: #111827;'>📊 終場大數據報告</h3>", unsafe_allow_html=True)
            
            st.markdown("##### 📈 籌碼運勢走勢圖")
            df_chart = pd.DataFrame(st.session_state.chart_history)
            zero_start = {name: 0 for _, name in active_players}
            df_chart = pd.concat([pd.DataFrame([zero_start]), df_chart], ignore_index=True)
            st.line_chart(df_chart)
            
            winners = [r["贏家"] for r in st.session_state.records]
            losers = [r["苦主"] for r in st.session_state.records if r["方式"] == "放槍"]
            self_draws = [r["贏家"] for r in st.session_state.records if r["方式"] == "自摸"]
            
            def get_most(data_list):
                if not data_list: return "-"
                return max(set(data_list), key=data_list.count)

            st.write("")
            st.markdown("##### 🏆 榮譽英雄榜")
            h1, h2, h3 = st.columns(3)
            with h1:
                st.info(f"👑 常勝將軍\n\n**{get_most(winners)}**")
            with h2:
                st.info(f"🔮 自摸大神\n\n**{get_most(self_draws)}**")
            with h3:
                st.info(f"🎯 送點觀音\n\n**{get_most(losers)}**")
            
            st.write("")
            h4, h5, h6 = st.columns(3)
            final_scores = [{"name": name, "bal": st.session_state.balances[idx]} for idx, name in active_players]
            big_winner = max(final_scores, key=lambda x: x["bal"])
            big_loser = min(final_scores, key=lambda x: x["bal"])
            avg_tai = sum([r["台數"] for r in st.session_state.records]) / len(st.session_state.records)
            
            with h4:
                st.info(f"💰 全場大贏家\n\n**{big_winner['name']}** (+{big_winner['bal']})")
            with h5:
                st.info(f"🌱 慈善撲克王\n\n**{big_loser['name']}** ({big_loser['bal']})")
            with h6:
                st.info(f"📊 全場平均台數\n\n**{avg_tai:.1f} 台**")
                
            # ==========================================
            # 🌟 新增：一鍵 LINE 群組請款功能
            # ==========================================
            st.divider()
            
            # 1. 重新抓取乾淨的餘額來計算轉帳 (避免被上面的清算吃掉數字)
            line_temp_bal = [{"name": name, "bal": st.session_state.balances[idx]} for idx, name in active_players]
            line_creditors = sorted([p for p in line_temp_bal if p["bal"] > 0], key=lambda x: x["bal"], reverse=True)
            line_debtors = sorted([p for p in line_temp_bal if p["bal"] < 0], key=lambda x: x["bal"])

            # 2. 組合 LINE 討債文字
            line_msg = "【🀄 今晚麻將終場結算單】\n"
            line_msg += f"👑 大贏家：{big_winner['name']} (+{big_winner['bal']}元)\n"
            line_msg += f"🌱 大善人：{big_loser['name']} ({big_loser['bal']}元)\n"
            line_msg += "-" * 15 + "\n"
            line_msg += "💸 轉帳明細：\n"
            
            has_debt = False
            c_idx, d_idx = 0, 0
            while c_idx < len(line_creditors) and d_idx < len(line_debtors):
                creditor = line_creditors[c_idx]
                debtor = line_debtors[d_idx]
                transfer = min(-debtor["bal"], creditor["bal"])
                if transfer > 0:
                    line_msg += f"👉 {debtor['name']} 應轉給 {creditor['name']}： {transfer} 元\n"
                    has_debt = True
                creditor["bal"] -= transfer
                debtor["bal"] += transfer
                if abs(creditor["bal"]) < 0.1: c_idx += 1
                if abs(debtor["bal"]) < 0.1: d_idx += 1
                
            if not has_debt:
                line_msg += "大家平手，今晚無金錢交易！\n"
                
            line_msg += "-" * 15 + "\n"
            line_msg += "（此訊息由 麻將結算神器 自動生成）"

            # 3. 將文字編碼並產生綠色按鈕
            encoded_msg = urllib.parse.quote(line_msg)
            line_url = f"https://line.me/R/msg/text/?{encoded_msg}"
            
            st.markdown(
                f"""
                <a href="{line_url}" target="_blank" style="
                    display: block;
                    width: 100%;
                    text-align: center;
                    background-color: #06C755;
                    color: white;
                    padding: 12px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: bold;
                    font-size: 1.1rem;
                    box-shadow: 0 4px 6px rgba(6, 199, 85, 0.2);
                    transition: opacity 0.2s;
                ">
                    💬 一鍵傳送結算單至 LINE 群組
                </a>
                """, 
                unsafe_allow_html=True
            )

# --- Tab 2: 登記牌局 ---
with tab_record:
    st.write("") 
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
        
        if win_type == "自摸":
            in_game_count = len(active_players)
            st.session_state.balances[winner_idx] += amount * (in_game_count - 1)
            for i, name in active_players:
                if i != winner_idx:
                    st.session_state.balances[i] -= amount
        else:
            loser_idx = next(i for i, name in active_players if name == loser_name)
            st.session_state.balances[winner_idx] += amount
            st.session_state.balances[loser_idx] -= amount
            
        st.session_state.records.append({
            "贏家": winner_name,
            "方式": win_type,
            "苦主": "-" if win_type == "自摸" else loser_name,
            "台數": total_tai,
            "異動": f"-{amount} /家" if win_type == "自摸" else f"-{amount}"
        })
        
        snapshot = {name: st.session_state.balances[idx] for idx, name in active_players}
        st.session_state.chart_history.append(snapshot)
        
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
        
        if st.button("撤銷最後一局紀錄", use_container_width=True):
            if st.session_state.records:
                last_rec = st.session_state.records.pop()
                winner_idx = next(i for i, name in enumerate(st.session_state.names) if name == last_rec["贏家"])
                amount_str = last_rec["異動"].replace("-", "").replace(" /家", "")
                amount = int(amount_str)
                
                if last_rec["方式"] == "自摸":
                    in_game_count = len(st.session_state.chart_history[-1])
                    st.session_state.balances[winner_idx] -= amount * (in_game_count - 1)
                    for name in st.session_state.chart_history[-1].keys():
                        if name != last_rec["贏家"]:
                            idx = next(i for i, n in enumerate(st.session_state.names) if n == name)
                            st.session_state.balances[idx] += amount
                else:
                    loser_idx = next(i for i, name in enumerate(st.session_state.names) if name == last_rec["苦主"])
                    st.session_state.balances[winner_idx] -= amount
                    st.session_state.balances[loser_idx] += amount
                
                st.session_state.chart_history.pop()
                st.toast("已撤銷最後一局")
                st.rerun()
