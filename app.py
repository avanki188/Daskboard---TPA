import streamlit as st
import pandas as pd
import io
from dpbt_engine import process_single_file, generate_summaries

st.set_page_config(page_title="DPBT Online System", layout="wide")

# Cấu hình mật khẩu truy cập
PASSWORD_CHOP_PHEP = "123456"  # <-- Ní đổi mật khẩu ở đây nha!

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔒 Đăng Nhập Hệ Thống DPBT Online")
        pwd = st.text_input("Nhập mật khẩu truy cập:", type="password")
        if st.button("Đăng nhập"):
            if pwd == PASSWORD_CHOP_PHEP:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Mật khẩu không đúng!")
        return False
    return True

if not check_password():
    st.stop()

# Giao diện chính sau khi đăng nhập
st.title("🛡️ DPBT Online - Hệ Thống Tracking & Thống Kê Hồ Sơ")
st.caption("Phương thức: Link Dữ Liệu Tự Động (Áp dụng Rule 1 & Rule 2)")

st.sidebar.header("📥 Nạp Dữ Liệu Hồ Sơ")
tpa_option = st.sidebar.selectbox("Chọn TPA Nguồn:", ["PPY", "FHVI", "INS", "FPTIS"])
uploaded_file = st.sidebar.file_uploader("Upload File Excel (DPBT / Nguồn):", type=["xls", "xlsx", "xlsm"])

if uploaded_file is not None:
    st.success(f"Đã nhận file: {uploaded_file.name}")
    
    try:
        df_processed = process_single_file(uploaded_file, tpa_option)
        
        st.subheader("📊 Báo Cáo Chi Tiết Sau Khi Link Rule 1 & Rule 2")
        st.dataframe(df_processed.head(50), use_container_width=True)
        
        sum_tpa, sum_unit = generate_summaries(df_processed)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("### 📈 Thống kê theo TPA")
            st.dataframe(sum_tpa, use_container_width=True)
        with col2:
            st.write("### 🏢 Thống kê theo Đơn vị & Phòng ban")
            st.dataframe(sum_unit, use_container_width=True)
            
        # Nút xuất file Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_processed.to_excel(writer, sheet_name='Chi_Tiet_Ho_So', index=False)
            sum_tpa.to_excel(writer, sheet_name='Tong_Hop_TPA', index=False)
            sum_unit.to_excel(writer, sheet_name='Tong_Hop_Don_Vi', index=False)
            
        st.download_button(
            label="📥 Tải Báo Cáo Excel Tổng Hợp",
            data=output.getvalue(),
            file_name=f"DPBT_Processed_{tpa_option}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        st.error(f"Lỗi xử lý file: {str(e)}")
else:
    st.info("👋 Vui lòng chọn TPA và upload file ở thanh bên trái để bắt đầu link dữ liệu.")
