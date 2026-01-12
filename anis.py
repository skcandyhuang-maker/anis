import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 設定頁面 (寬版模式) ---
st.set_page_config(page_title="直播點貨系統 / Sistem Stok Live", layout="wide")

# --- CSS 優化 (按鈕圓潤 + 表格標題醒目) ---
st.markdown("""
<style>
    .stPills button {
        border-radius: 20px !important;
        font-weight: bold !important;
        border: 1px solid #ddd !important;
    }
    /* 讓左側清單標題更明顯 */
    h3 {
        color: #2e86de; 
    }
</style>
""", unsafe_allow_html=True)

# --- 初始化 Session State ---
if 'orders' not in st.session_state:
    st.session_state.orders = []
if 'history_items' not in st.session_state:
    st.session_state.history_items = [] 
if 'history_colors' not in st.session_state:
    st.session_state.history_colors = [] 
if 'history_sizes' not in st.session_state:
    st.session_state.history_sizes = [] 

# --- 預設資料 ---
DEFAULT_COLORS = ["黑/Hitam", "白/Putih", "灰/Abu", "藍/Biru", "深藍/Biru Tua", "淺藍/Biru Muda", "米色/Krem"]
DEFAULT_SIZES = ["XS", "S", "M", "L", "XL", "2XL", "3XL"]

# --- 檔案儲存路徑 ---
DATA_FOLDER = "order_records"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# --- 標題 ---
st.title("📦 直播點貨 POS 系統 / Sistem POS Live")

# --- 側邊欄：歷史紀錄讀取 ---
with st.sidebar:
    st.header("📂 紀錄與存檔 / Arsip")
    # 存檔功能移到側邊欄，避免佔用主畫面空間
    st.markdown("### 💾 儲存 / Simpan")
    today_str = datetime.now().strftime("%Y-%m-%d")
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.csv')]
    files.sort(reverse=True)
    
    existing_today = [f for f in files if f.startswith(today_str)]
    next_index = len(existing_today) + 1
    default_filename = f"{today_str}-{next_index}"
    
    save_name = st.text_input("檔名 / Nama File", value=default_filename)
    if st.button("立即儲存 / Simpan CSV", type="primary"):
        if st.session_state.orders:
            df_save = pd.DataFrame(st.session_state.orders)
            full_path = os.path.join(DATA_FOLDER, f"{save_name}.csv")
            df_save.to_csv(full_path, index=False)
            st.toast(f"✅ 已儲存: {save_name}.csv") # 跳出小提示
            files.insert(0, f"{save_name}.csv") # 假裝更新列表
        else:
            st.error("清單是空的 / Kosong")

    st.markdown("---")
    
    st.markdown("### 📖 讀取舊檔 / Baca File")
    selected_file = st.selectbox("選擇檔案", ["-- 選擇 / Pilih --"] + files)
    if selected_file != "-- 選擇 / Pilih --":
        if st.button("讀取 / Muat"):
            try:
                df_load = pd.read_csv(os.path.join(DATA_FOLDER, selected_file))
                st.session_state.orders = df_load.to_dict('records')
                # 恢復歷史選項
                for col, history_list in [("貨號 / Kode", 'history_items'), ("顏色 / Warna", 'history_colors'), ("尺寸 / Ukuran", 'history_sizes')]:
                    if col in df_load.columns:
                        existing = df_load[col].unique().tolist()
                        for item in existing:
                            if item not in DEFAULT_COLORS and item not in DEFAULT_SIZES and item not in st.session_state[history_list]:
                                st.session_state[history_list].append(item)
                st.success("已讀取!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# ==========================================
#  版面佈局：左邊清單 (55%) | 右邊操作 (45%)
# ==========================================
col_list, col_input = st.columns([5.5, 4.5], gap="large")

# ------------------------------------------
# 左欄：清單顯示區 (監控)
# ------------------------------------------
with col_list:
    st.subheader("📋 已點清單 / Daftar Pesanan")
    
    if st.session_state.orders:
        df = pd.DataFrame(st.session_state.orders)
        
        # 1. 顯示統計 (優先顯示統計，方便一眼看總量)
        with st.expander("📊 點擊查看統計 / Lihat Statistik", expanded=True):
            if not df.empty:
                # 簡單的統計表格
                summary = df.groupby(['貨號 / Kode', '顏色 / Warna', '尺寸 / Ukuran']).size().reset_index(name='數量')
                st.dataframe(summary, use_container_width=True, height=200)

        # 2. 顯示詳細清單 (可編輯)
        # height=500 限制高度，這樣在手機上不會佔據整個畫面
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            height=500, 
            key="editor"
        )
        
        # 同步修改內容
        if not df.equals(edited_df):
            st.session_state.orders = edited_df.to_dict('records')
            st.rerun()
    else:
        st.info("☞ (電腦版) 請在右側輸入資料\n\n☟ (手機版) 請在下 方輸入資料")

# ------------------------------------------
# 右欄：輸入操作區 (動作)
# ------------------------------------------
with col_input:
    st.subheader("📝 輸入面板 / Input Panel")
    
    # 把它包在一個容器裡，增加視覺區隔
    with st.container(border=True):
        
        # 1. 貨號與客人
        c1, c2 = st.columns(2)
        with c1:
            input_mode = st.radio("模式", ["輸入", "選舊的"], horizontal=True, label_visibility="collapsed")
            if input_mode == "選舊的" and st.session_state.history_items:
                item_code = st.selectbox("貨號 / Kode", st.session_state.history_items)
            else:
                item_code = st.text_input("貨號 / Kode", placeholder="A01")
        with c2:
            st.write("") # 排版用
            st.write("") 
            customer_name = st.text_input("客人 / Nama", placeholder="Judy")

        st.markdown("---")

        # 2. 顏色 (Pills)
        st.write("🎨 **顏色 / Warna**")
        color_options = DEFAULT_COLORS + st.session_state.history_colors + ["➕自填"]
        selected_color_pill = st.pills("Color", color_options, selection_mode="single", key="color_pill", label_visibility="collapsed")
        
        final_color = None
        if selected_color_pill == "➕自填":
            final_color = st.text_input("輸入新顏色 / Warna Baru")
        else:
            final_color = selected_color_pill

        st.markdown("---")

        # 3. 尺寸 (Pills)
        st.write("📏 **尺寸 / Ukuran**")
        size_options = DEFAULT_SIZES + st.session_state.history_sizes + ["➕自填"]
        selected_size_pill = st.pills("Size", size_options, selection_mode="single", key="size_pill", label_visibility="collapsed")
        
        final_size = None
        if selected_size_pill == "➕自填":
            final_size = st.text_input("輸入新尺寸 / Ukuran Baru")
        else:
            final_size = selected_size_pill
        
        st.markdown("---")

        # 4. 確認按鈕 (特大)
        if st.button("✅ 確認加入 / TAMBAH", type="primary", use_container_width=True):
            if item_code and customer_name and final_color and final_size:
                new_order = {
                    "貨號 / Kode": item_code,
                    "客人 / Nama": customer_name,
                    "顏色 / Warna": final_color,
                    "尺寸 / Ukuran": final_size,
                    "時間 / Waktu": datetime.now().strftime("%H:%M:%S")
                }
                # 插入到最前面 (這樣最新輸入的會在表格最上面，不用捲動到底部)
                st.session_state.orders.insert(0, new_order)
                
                # 記錄歷史
                if item_code not in st.session_state.history_items:
                    st.session_state.history_items.append(item_code)
                if selected_color_pill == "➕自填" and final_color not in DEFAULT_COLORS:
                    st.session_state.history_colors.append(final_color)
                if selected_size_pill == "➕自填" and final_size not in DEFAULT_SIZES:
                    st.session_state.history_sizes.append(final_size)

                st.success(f"Added: {item_code} / {customer_name}")
                st.rerun()
            else:
                st.error("❌ 資料不完整 / Data Tidak Lengkap")
