import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta, timezone

# --- 設定頁面 ---
st.set_page_config(page_title="TokoMamanis POS", layout="wide")

# --- CSS 美化工程 ---
st.markdown("""
<style>
    /* 全域字體 */
    .stApp { font-family: 'Heiti TC', sans-serif; }
    
    /* 1. 頂部數據卡片風格 */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #aaa; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #4FC3F7; font-weight: bold; }
    
    /* 2. 按鈕 (Pills) */
    .stPills button {
        border-radius: 20px !important;
        font-weight: 600 !important;
        border: 1px solid #444 !important;
        padding: 4px 12px !important;
        font-size: 0.9rem !important;
    }
    
    /* 3. 輸入面板外框 */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px;
        padding: 10px;
    }

    /* 4. 表格標題 */
    h3 { color: #4FC3F7 !important; font-size: 1.3rem !important; margin-bottom: 0px !important; }
    
    /* 5. 修正頂部間距 (加大到 4rem，解決切頭問題) */
    .block-container { padding-top: 4rem; padding-bottom: 3rem; }
    div[data-testid="stVerticalBlock"] { gap: 0.5rem; }
    
    /* 價格表樣式 */
    div[data-testid="stDataEditor"] { border: 1px solid #444; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 台灣時間函數 ---
def get_taiwan_time():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime("%H:%M:%S")

# --- 初始化 Session State ---
if 'orders' not in st.session_state: st.session_state.orders = []
for key in ['history_items', 'history_colors', 'history_sizes']:
    if key not in st.session_state: st.session_state[key] = []
if 'price_map' not in st.session_state: st.session_state.price_map = {} 
if 'cost_map' not in st.session_state: st.session_state.cost_map = {} 

# --- 預設資料 ---
DEFAULT_COLORS = ["黑/Hitam", "白/Putih", "灰/Abu", "藍/Biru", "深藍/Biru Tua", "淺藍/Biru Muda", "米色/Krem"]
DEFAULT_SIZES = ["XS", "S", "M", "L", "XL", "2XL", "3XL"]

# --- 檔案處理 ---
DATA_FOLDER = "order_records"
if not os.path.exists(DATA_FOLDER): os.makedirs(DATA_FOLDER)

# ==========================================
#  側邊欄：價格與檔案
# ==========================================
with st.sidebar:
    st.header("💰 設定利潤 / Atur Margin")
    
    all_items = sorted(list(set(st.session_state.history_items)))
    
    if all_items:
        st.caption("👇 雙擊修改 / Klik 2x edit")
        
        price_data = []
        for code in all_items:
            c_price = st.session_state.price_map.get(code, 0)
            c_cost = st.session_state.cost_map.get(code, 0)
            price_data.append({
                "貨號": code, 
                "成本": c_cost,
                "售價": c_price,
                "毛利": c_price - c_cost
            })
        
        df_price = pd.DataFrame(price_data)
        
        edited_prices = st.data_editor(
            df_price, 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "貨號": st.column_config.TextColumn("貨號 / Kode", disabled=True), 
                "成本": st.column_config.NumberColumn("成本 / Modal", min_value=0, step=50, format="$%d", required=True),
                "售價": st.column_config.NumberColumn("售價 / Jual", min_value=0, step=50, format="$%d", required=True),
                "毛利": st.column_config.NumberColumn("毛利 / Untung", disabled=True, format="$%d") 
            },
            key="price_editor",
            height=300
        )
        
        for index, row in edited_prices.iterrows():
            st.session_state.price_map[row['貨號']] = row['售價']
            st.session_state.cost_map[row['貨號']] = row['成本']
    else:
        st.info("尚無貨號 / Belum ada kode")

    st.markdown("---")
    st.header("📂 檔案 / File")
    
    today_str = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.csv')]
    files.sort(reverse=True)
    existing_today = [f for f in files if f.startswith(today_str)]
    default_filename = f"{today_str}-{len(existing_today) + 1}"
    
    save_name = st.text_input("檔名 / Nama File", value=default_filename)
    if st.button("💾 儲存 / Simpan", type="primary", use_container_width=True):
        if st.session_state.orders:
            orders_to_save = []
            for o in st.session_state.orders:
                o_copy = o.copy()
                code = o['貨號 / Kode']
                o_copy['售價 / Jual'] = st.session_state.price_map.get(code, 0)
                o_copy['成本 / Modal'] = st.session_state.cost_map.get(code, 0)
                o_copy['毛利 / Laba'] = o_copy['售價 / Jual'] - o_copy['成本 / Modal']
                orders_to_save.append(o_copy)
            pd.DataFrame(orders_to_save).to_csv(os.path.join(DATA_FOLDER, f"{save_name}.csv"), index=False)
            st.toast(f"✅ 已儲存 / Tersimpan: {save_name}.csv")
            st.rerun()
        else:
            st.error("清單是空的 / Daftar Kosong")
            
    selected_file = st.selectbox("讀取舊檔 / Pilih File Lama", ["-- 選擇 / Pilih --"] + files)
    if selected_file != "-- 選擇 / Pilih --" and st.button("讀取 / Muat", use_container_width=True):
        try:
            df_load = pd.read_csv(os.path.join(DATA_FOLDER, selected_file))
            st.session_state.orders = df_load.to_dict('records')
            # 恢復歷史
            for col, h_list in [("貨號 / Kode",'history_items'), ("顏色 / Warna",'history_colors'), ("尺寸 / Ukuran",'history_sizes')]:
                if col in df_load.columns:
                    for x in df_load[col].unique():
                        if str(x)!='nan' and x not in DEFAULT_COLORS+DEFAULT_SIZES and x not in st.session_state[h_list]:
                            st.session_state[h_list].append(x)
            # 恢復價格
            if '售價 / Jual' in df_load.columns:
                 for i, r in df_load.iterrows():
                    if pd.notna(r['售價 / Jual']): st.session_state.price_map[r['貨號 / Kode']] = int(r['售價 / Jual'])
                    if pd.notna(r['成本 / Modal']): st.session_state.cost_map[r['貨號 / Kode']] = int(r['成本 / Modal'])
            st.success("讀取成功 / Berhasil Dimuat!")
            st.rerun()
        except Exception as e: st.error(str(e))

# ==========================================
#  頂部儀表板 (Header)
# ==========================================
current_revenue = 0
current_cost = 0
for order in st.session_state.orders:
    code = order['貨號 / Kode']
    current_revenue += st.session_state.price_map.get(code, 0)
    current_cost += st.session_state.cost_map.get(code, 0)
current_profit = current_revenue - current_cost

with st.container():
    c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
    with c1:
        st.markdown("## 📦 TokoMamanis POS")
        # 補上印尼文: Pantauan Live
        st.caption(f"📅 {today_str} | Pantauan Live")
    with c2:
        st.metric("📦 總單量 / Pcs", f"{len(st.session_state.orders)}")
    with c3:
        st.metric("💰 總營收 / Omset", f"${current_revenue:,}")
    with c4:
        st.metric("💵 總淨利 / Laba", f"${current_profit:,}", delta="Profit" if current_profit > 0 else None)
    
    st.divider()

# ==========================================
#  核心操作區
# ==========================================
col_list, col_input = st.columns([6, 4], gap="medium")

# --- 左欄：表格 ---
with col_list:
    tab1, tab2 = st.tabs(["📋 叫貨總表 / List Order (Total)", "📊 詳細統計 / Detail Pesanan"])
    
    df = pd.DataFrame(st.session_state.orders)
    
    with tab1: # Pivot
        if not df.empty:
            pivot = df.pivot_table(index=['貨號 / Kode', '顏色 / Warna'], columns='尺寸 / Ukuran', aggfunc='size', fill_value=0)
            cols = pivot.columns.tolist()
            std_cols = [c for c in ["XS","S","M","L","XL","2XL","3XL"] if c in cols]
            other_cols = [c for c in cols if c not in std_cols]
            pivot = pivot[std_cols + other_cols]
            pivot['總量 / Total'] = pivot.sum(axis=1)
            st.dataframe(pivot, use_container_width=True, height=500)
        else:
            st.info("等待輸入... / Menunggu input")

    with tab2: # Detail
        if not df.empty:
            df_show = df.copy()
            df_show['售價 / Jual'] = df_show['貨號 / Kode'].map(st.session_state.price_map).fillna(0)
            df_show['成本 / Modal'] = df_show['貨號 / Kode'].map(st.session_state.cost_map).fillna(0)
            
            edited_df = st.data_editor(
                df_show,
                num_rows="dynamic",
                use_container_width=True,
                height=500,
                key="editor",
                column_config={
                    "售價 / Jual": st.column_config.NumberColumn(disabled=True),
                    "成本 / Modal": st.column_config.NumberColumn(disabled=True)
                }
            )
            if not df.equals(edited_df[df.columns]):
                st.session_state.orders = edited_df[df.columns].to_dict('records')
                st.rerun()

# --- 右欄：輸入面板 ---
with col_input:
    with st.container(border=True):
        st.markdown("### 📝 輸入 / Input Panel")
        
        # 1. 貨號
        st.caption("🏷️ **貨號 / Kode**")
        opts = ["➕新/Baru"] + st.session_state.history_items
        sel_item = st.pills("Item", opts, selection_mode="single", key="pill_item", label_visibility="collapsed")
        
        item_code = ""
        if sel_item == "➕新/Baru" or sel_item is None:
             item_code = st.text_input("input_code", placeholder="Contoh: 3", label_visibility="collapsed")
        else:
             item_code = sel_item
             st.success(f"已選 / Terpilih: {item_code}") 

        # 2. 客人
        st.caption("👤 **客人 / Nama**")
        customer_name = st.text_input("input_cust", placeholder="Contoh: anis", label_visibility="collapsed")

        st.markdown("---")
        
        # 3. 顏色與尺寸
        st.caption("🎨 **顏色 / Warna**")
        c_opts = DEFAULT_COLORS + st.session_state.history_colors + ["➕自填/Lainnya"]
        sel_color = st.pills("Color", c_opts, selection_mode="single", key="pill_color", label_visibility="collapsed")
        
        final_color = None
        if sel_color == "➕自填/Lainnya":
            final_color = st.text_input("new_color", placeholder="新顏色 / Warna Baru...", label_visibility="collapsed")
        else:
            final_color = sel_color

        st.caption("📏 **尺寸 / Ukuran**")
        s_opts = DEFAULT_SIZES + st.session_state.history_sizes + ["➕自填/Lainnya"]
        sel_size = st.pills("Size", s_opts, selection_mode="single", key="pill_size", label_visibility="collapsed")
        
        final_size = None
        if sel_size == "➕自填/Lainnya":
            final_size = st.text_input("new_size", placeholder="新尺寸 / Ukuran Baru...", label_visibility="collapsed")
        else:
            final_size = sel_size
        
        st.markdown("---")

        # 按鈕區
        b1, b2 = st.columns([7, 3])
        with b1:
            if st.button("✅ 確認加入 / TAMBAH", type="primary", use_container_width=True):
                if item_code and customer_name and final_color and final_size:
                    new_order = {
                        "貨號 / Kode": item_code,
                        "客人 / Nama": customer_name,
                        "顏色 / Warna": final_color,
                        "尺寸 / Ukuran": final_size,
                        "時間 / Waktu": get_taiwan_time()
                    }
                    st.session_state.orders.insert(0, new_order)
                    
                    if item_code not in st.session_state.history_items:
                        st.session_state.history_items.append(item_code)
                        if item_code not in st.session_state.price_map: st.session_state.price_map[item_code]=0
                        if item_code not in st.session_state.cost_map: st.session_state.cost_map[item_code]=0
                    
                    if sel_color=="➕自填/Lainnya" and final_color and final_color not in DEFAULT_COLORS: st.session_state.history_colors.append(final_color)
                    if sel_size=="➕自填/Lainnya" and final_size and final_size not in DEFAULT_SIZES: st.session_state.history_sizes.append(final_size)
                    
                    st.rerun()
                else:
                    st.error("缺資料 / Data Kurang")
        
        with b2:
            # 這裡補上了印尼文 Batal
            if st.button("↩ 撤銷 / Batal", use_container_width=True):
                if st.session_state.orders:
                    st.session_state.orders.pop(0)
                    st.rerun()
