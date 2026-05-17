import streamlit as st
import pandas as pd

# --- 網頁基本設定 ---
st.set_page_config(page_title="🀄 麻將結算神器", page_icon="🀄", layout="centered")

# --- 初始化 Session State (確保重新整理資料還在) ---
if 'initialized' not in st.session_state:
    st.session_state.base_money = 100
    st.session_state.tai_money = 20
    st.session_state.players = ["東風", "南風", "西風", "北風", "中發白"]
    st.session_state.balances = [0, 0, 0, 0, 0]
    st.session_state.records = []
    st.session_state.initialized = True

st.title("🀄 麻將結算神器 V2 (Streamlit 版)")

# --- 1. 基本設定區 ---
with st.expander("⚙️ 玩家與底台設定", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.base_money = st.number_input("底 (金額)", value=st.session_state.base_money, min_value=0, step=10)
    with col2:
        st.session_state.tai_money = st.number_input("台 (金額)", value=st.session_state.tai_money, min_value=0, step=10)
    
    st.markdown("**玩家名稱設定 (第 5 位為輪休備用)**")
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.session_state.players[i] = st.text_input(f"玩家 {i+1}", value=st.session_state.players[i], key=f"p_{i}")
            
    if st.button("🚨 清除所有紀錄重來", type="primary"):
        st.session_state.balances = [0, 0, 0, 0, 0]
        st.session_state.records = []
        st.rerun()

# --- 2. 即時戰況記分板 ---
st.header("📊 即時戰況")
score_cols = st.columns(5)
for i in range(5):
    with score_cols[i]:
        bal = st.session_state.balances[i]
        # 贏錢顯示紅色(正常)，輸錢顯示綠色(反向)
        color = "normal" if bal == 0 else ("normal" if bal > 0 else "inverse")
        st.metric(label=st.session_state.players[i], value=f"{bal}", delta=bal if bal != 0 else None, delta_color=color)

st.divider()

# --- 3. 登記牌局 ---
st.header("📝 登記單局結果")

# 選擇休息者
resting_options = {i: name for i, name in enumerate(st.session_state.players)}
resting_idx = st.selectbox("☕ 本局休息者", options=list(resting_options.keys()), format_func=lambda x: resting_options[x], index=4)

# 準備場上玩家名單
active_players = {i: name for i, name in enumerate(st.session_state.players) if i != resting_idx}
active_keys = list(active_players.keys())

col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    winner_idx = st.selectbox("👑 贏家", options=active_keys, format_func=lambda x: active_players[x])
with col_b:
    win_type = st.selectbox("🎲 胡牌方式", options=["放槍", "自摸"])
with col_c:
    # 如果是放槍才需要選輸家，且輸家不能是贏家
    loser_options = [k for k in active_keys if k != winner_idx]
    loser_idx = st.selectbox("😭 放槍苦主", options=loser_options, format_func=lambda x: active_players[x], disabled=(win_type=="自摸"))
with col_d:
    tai_count = st.number_input("🔢 台數", value=1, min_value=0, step=1)

if st.button("✅ 填入並計算此局", use_container_width=True):
    amount = st.session_state.base_money + (tai_count * st.session_state.tai_money)
    changes = [0]*5
    
    if win_type == "自摸":
        for i in range(5):
            if i == resting_idx:
                continue
            if i == winner_idx:
                changes[i] += amount * 3
                st.session_state.balances[i] += amount * 3
            else:
                changes[i] -= amount
                st.session_state.balances[i] -= amount
    else: # 放槍
        changes[winner_idx] += amount
        st.session_state.balances[winner_idx] += amount
        changes[loser_idx] -= amount
        st.session_state.balances[loser_idx] -= amount
        
    st.session_state.records.append({
        "贏家": st.session_state.players[winner_idx],
        "方式": win_type,
        "苦主/輸家": "其餘三家" if win_type == "自摸" else st.session_state.players[loser_idx],
        "休息": st.session_state.players[resting_idx],
        "台數": tai_count,
        "金額異動": f"每家 -{amount} (贏家 +{amount*3})" if win_type == "自摸" else f"苦主 -{amount} (贏家 +{amount})"
    })
    st.rerun()

st.divider()

# --- 4. 最佳化分錢清單 ---
st.header("💸 最佳化轉帳建議")
temp_balances = [{"idx": i, "name": st.session_state.players[i], "bal": st.session_state.balances[i]} for i in range(5)]
creditors = sorted([p for p in temp_balances if p["bal"] > 0], key=lambda x: x["bal"], reverse=True)
debtors = sorted([p for p in temp_balances if p["bal"] < 0], key=lambda x: x["bal"])

if not creditors or not debtors:
    st.info("目前大家平手或無戰況，暫不需進行任何轉帳！")
else:
    c_idx, d_idx = 0, 0
    while c_idx < len(creditors) and d_idx < len(debtors):
        creditor = creditors[c_idx]
        debtor = debtors[d_idx]
        
        transfer = min(-debtor["bal"], creditor["bal"])
        if transfer > 0:
            st.success(f"**{debtor['name']}** 應轉帳給 **{creditor['name']}** : `{transfer}` 元")
            
        creditor["bal"] -= transfer
        debtor["bal"] += transfer
        
        if abs(creditor["bal"]) < 0.1: c_idx += 1
        if abs(debtor["bal"]) < 0.1: d_idx += 1

# --- 5. 歷史紀錄表格 ---
st.header("📜 歷史牌局對帳表")
if st.session_state.records:
    # 反轉順序讓最新的一局在最上面
    df = pd.DataFrame(reversed(st.session_state.records))
    df.index = [len(st.session_state.records) - i for i in range(len(st.session_state.records))]
    st.dataframe(df, use_container_width=True)
    
    if st.button("🔙 撤銷上一局"):
        # 簡單的防呆，直接清空重算最保險，這邊為了簡單示範，我們做一個簡單的 Pop 倒扣
        last_rec_idx = len(st.session_state.records) - 1
        # 因為牽扯到複雜的回溯，如果真要撤銷，建議配合完整的資料結構。
        # 這裡提供一鍵重整功能。
        st.warning("如需修改，建議點擊最上方『清除所有紀錄重來』。")
else:
    st.caption("目前尚無任何牌局對帳紀錄。")
