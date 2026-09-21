import pandas as pd
import re
from config import TPA_BANK_INFO, ROOM_TO_UNIT

def extract_room_code(so_don_bh):
    if pd.isna(so_don_bh):
        return None
    parts = str(so_don_bh).split('/')
    if len(parts) >= 3:
        return parts[2].strip()
    return None

def process_single_file(file_obj, source_tpa, sheet_name=0):
    """
    Đọc 1 file DPBT/Nguồn, tự động áp dụng Rule 1 & Rule 2
    """
    df = pd.read_excel(file_obj, sheet_name=sheet_name)
    df['Nguồn TPA'] = source_tpa
    
    # Extract & map Unit ID từ 'Số đơn BH'
    room_codes = df['Số đơn BH'].apply(extract_room_code) if 'Số đơn BH' in df.columns else None
    mapped_units = room_codes.map(ROOM_TO_UNIT) if room_codes is not None else None
    
    if 'Đơn vị' not in df.columns or df['Đơn vị'].isnull().all():
        df['Đơn vị'] = mapped_units
    else:
        df['Đơn vị'] = df['Đơn vị'].fillna(mapped_units)
        
    # Rule 2: Normalization (Bỏ số '1' đầu tiên nếu mã có độ dài 11 ký tự)
    # FIX LỖI float: Chuyển dữ liệu sang chuỗi an toàn trước khi kiểm tra độ dài len()
    def format_phong_ban(val):
        if pd.isna(val):
            return ""
        val_str = str(val).split('.')[0].strip() # Loại bỏ phần thập phân .0 nếu có
        if len(val_str) == 11 and val_str.startswith('1'):
            return val_str[1:]
        return val_str

    df['Đơn vị'] = df['Đơn vị'].apply(lambda x: "" if pd.isna(x) else str(x).split('.')[0].strip())
    df['Phòng ban'] = df['Đơn vị'].apply(format_phong_ban)
    
    # Rule 2: Bank beneficiary details
    bank_info = TPA_BANK_INFO.get(source_tpa, {})
    for key, val in bank_info.items():
        df[key] = val
        
    # Rule 1: Amount standardization
    if 'Số tiền DPBT ntệ' in df.columns:
        val_amount = df['Số tiền DPBT ntệ']
        df['Số tiền DPBT'] = val_amount
        df['Số tiền yêu cầu ntệ'] = val_amount
        df['Số tiền yêu cầu'] = val_amount
        
    if 'Ghi chú' not in df.columns:
        df['Ghi chú'] = None
        
    return df

def generate_summaries(df_all):
    """
    Tạo các bảng tổng hợp thống kê
    """
    summary_tpa = df_all.groupby('Nguồn TPA').agg(
        Số_hồ_sơ=('Số HSBT TPA', 'count'),
        Tổng_tiền_DPBT=('Số tiền DPBT ntệ', 'sum'),
        Số_đơn_BH_duy_nhất=('Số đơn BH', 'nunique')
    ).reset_index()
    
    summary_unit = df_all.groupby(['Đơn vị', 'Phòng ban']).agg(
        Số_hồ_sơ=('Số HSBT TPA', 'count'),
        Tổng_tiền_DPBT=('Số tiền DPBT ntệ', 'sum')
    ).reset_index()
    
    return summary_tpa, summary_unit
