import streamlit as st
import pandas as pd

# 必須寫在第一行
st.set_page_config(page_title="麻將結算大師", page_icon="🀄", layout="centered")

# --- 狀態初始化 ---
if 'init' not in st.session_state:
    st.session_state.base = 100
    st.session_state.tai = 20
    st.session_state.names = ["東風", "南風", "西風", "北風", "", ""]
    st.session_state.balances = [0] * 6
    st.session_state.records = []
    # 用來記錄每局結束後，每個人的累計餘額 (做圖表用)
    st.session_state.chart_history = [] 
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
            placeholder=f"玩家 {i+1}",
            label_visibility="collapsed"
        )
        
    st.divider()
    if st.button("🚨 結算並清空全部資料", type="primary", use_container_width=True):
        st.session_state.balances = [0] * 6
        st.session_state.records = []
        st.session_state.chart_history = []
        st.rerun()

active_players = [(i, name) for i, name in enumerate(st.session_state.names) if name.strip()]

# ==========================================
# 主畫面
# ==========================================
st.title("🀄 麻將結算神器")

tab_board, tab_record, tab_analysis, tab_history = st.tabs(["📊 戰況結算", "📝 登記牌局", "🏆 終場總結算", "📜 歷史對帳"])

# --- Tab 1: 戰況結算 ---
with tab_board:
    st.write("") 
    cols = st.columns(3)
    for idx, (original_idx, name) in enumerate(active_players):
        bal = st.session_state.balances[original_idx]
        delta_str = f"+{bal}" if bal > 0 else str(bal)
        with cols[idx % 3]:
            st.metric(label=name, value=bal, delta=delta_str if bal!=0 else "平手")

    st.divider()
    
    st.subheader("💸 最佳化轉帳建議")
    temp_bal = [{"name": name, "bal": st.session_state.balances[idx]} for idx, name in active_players]
    creditors = sorted([p for p in temp_bal if p["bal"] > 0], key=lambda x: x["bal"], reverse=True)
    debtors = sorted([p for p in temp_bal if p["bal"] < 0], key=lambda x: x["bal"])

    if not creditors or not debtors:
        st.info("目前無待轉帳款項。")
    else:
        c_idx, d_idx = 0, 0
        with st.container(border=True):
            while c_idx < len(creditors) and d_idx < len(debtors):
                creditor = creditors[c_idx]
                debtor = debtors[d_idx]
                transfer = min(-debtor["bal"], creditor["bal"])
                if transfer > 0:
                    st.success(f"**{debtor['name']}** ➔ 轉給 👑 **{creditor['name']}** ： **{transfer} 元**")
                creditor["bal"] -= transfer
                debtor["bal"] += transfer
                if abs(creditor["bal"]) < 0.1: c_idx += 1
                if abs(debtor["bal"]) < 0.1: d_idx += 1

# --- Tab 2: 登記牌局 ---
with tab_record:
    with st.container(border=True):
        st.markdown("**1. 輸贏設定**")
        player_options = [p[1] for p in active_players]
        c1, c2, c3 = st.columns(3)
        with c1:
            winner_name = st.selectbox("👑 贏家", options=player_options)
        with c2:
            win_type = st.selectbox("🎲 方式", options=["放槍", "自摸"])
        with c3:
            loser_options = [p for p in player_options if p != winner_name]
            loser_name = st.selectbox("😭 苦主", options=loser_options, disabled=(win_type=="自摸"))

    with st.container(border=True):
        st.markdown("**2. 台數計算**")
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

    if st.button("確認登記此局", type="primary", use_container_width=True):
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
            "苦主": "其餘三家" if win_type == "自摸" else loser_name,
            "台數": total_tai,
            "異動": f"-{amount} /家" if win_type == "自摸" else f"-{amount}"
        })
        
        # 記錄快照用於圖表
        snapshot = {name: st.session_state.balances[idx] for idx, name in active_players}
        st.session_state.chart_history.append(snapshot)
        
        st.toast("✅ 登記成功")
        st.rerun()

# --- Tab 3: 終場總結算 (New!) ---
with tab_analysis:
    if not st.session_state.records:
        st.info("尚無紀錄，打完幾把後再來看看數據分析！")
    else:
        st.subheader("📈 戰況運勢走勢圖")
        df_chart = pd.DataFrame(st.session_state.chart_history)
        # 補上第0局（大家都是0）
        zero_start = {name: 0 for _, name in active_players}
        df_chart = pd.concat([pd.DataFrame([zero_start]), df_chart], ignore_index=True)
        st.line_chart(df_chart)
        
        st.divider()
        
        st.subheader("🏆 榮譽英雄榜")
        
        # 數據運算
        winners = [r["贏家"] for r in st.session_state.records]
        losers = [r["苦主"] for r in st.session_state.records if r["方式"] == "放槍"]
        self_draws = [r["贏家"] for r in st.session_state.records if r["方式"] == "自摸"]
        
        def get_most(data_list):
            if not data_list: return "無"
            return max(set(data_list), key=data_list.count)

        h1, h2, h3 = st.columns(3)
        with h1:
            st.success(f"👑 **常勝將軍**\n\n{get_most(winners)}")
            st.caption("勝場次數最高")
        with h2:
            st.info(f"🔮 **自摸大神**\n\n{get_most(self_draws)}")
            st.caption("自摸次數最多")
        with h3:
            st.warning(f"🎯 **送點觀音**\n\n{get_most(losers)}")
            st.caption("放槍次數最高")
        
        st.write("")
        
        h4, h5, h6 = st.columns(3)
        # 總餘額結算
        final_scores = [{"name": name, "bal": st.session_state.balances[idx]} for idx, name in active_players]
        big_winner = max(final_scores, key=lambda x: x["bal"])
        big_loser = min(final_scores, key=lambda x: x["bal"])
        
        with h4:
            st.error(f"💰 **全場大贏家**\n\n{big_winner['name']}")
            st.caption(f"淨賺 {big_winner['bal']} 元")
        with h5:
            st.success(f"🌱 **慈善撲克王**\n\n{big_loser['name']}")
            st.caption(f"總共捐出 {-big_loser['bal']} 元")
        with h6:
            avg_tai = sum([r["台數"] for r in st.session_state.records]) / len(st.session_state.records)
            st.info(f"📊 **全場平均台數**\n\n{avg_tai:.1f} 台")
            st.caption("今晚大家打得真大")

        if st.button("🎆 點擊慶祝今晚結束！"):
            st.balloons()
            st.snow()

# --- Tab 4: 歷史對帳 ---
with tab_history:
    if not st.session_state.records:
        st.caption("尚無紀錄")
    else:
        df_history = pd.DataFrame(reversed(st.session_state.records))
        df_history.index = [len(st.session_state.records) - i for i in range(len(st.session_state.records))]
        st.dataframe(df_history, use_container_width=True)
        
        if st.button("🔙 撤銷最後一局紀錄"):
            if st.session_state.records:
                last_rec = st.session_state.records.pop()
                # 重新計算餘額 (這邊簡單做法是從頭跑一遍 record 或直接倒扣)
                # 為了邏輯簡單，我們倒扣回去
                winner_idx = next(i for i, name in enumerate(st.session_state.names) if name == last_rec["贏家"])
                amount_str = last_rec["金額變動"].replace("每家 -", "").replace("苦主 -", "")
                amount = int(amount_str)
                
                if last_rec["方式"] == "自摸":
                    # 贏家減去 (人數-1) 份
                    in_game_count = len(st.session_state.chart_history[-1])
                    st.session_state.balances[winner_idx] -= amount * (in_game_count - 1)
                    # 其餘人加回 1 份
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
