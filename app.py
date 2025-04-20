import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
import shutil

# Cấu hình trang
st.set_page_config(page_title="Đánh giá TOPSIS-AHP-Picture Fuzzy", layout="centered")
st.title("📊 Hệ thống đánh giá bài giảng theo TOPSIS-AHP-PICTURE FUZZY")

# Khởi tạo session state
if "step" not in st.session_state:
    st.session_state.step = 1
if "scores" not in st.session_state:
    st.session_state.scores = []

criteria = ["Thái độ", "Kỹ năng", "Kiến thức"]

# Bước 1: Nhập dữ liệu
if st.session_state.step == 1:
    st.header("Bước 1: Nhập thông tin đánh giá")

    num_lectures = st.number_input("Số lượng bài giảng", min_value=1, step=1, value=3)
    num_experts = st.number_input("Số lượng chuyên gia", min_value=1, step=1, value=2)

    names = [st.text_input(f"Tên bài giảng {i+1}", value=f"Bài giảng {chr(65+i)}") for i in range(num_lectures)]

    all_scores = []
    st.subheader("Nhập điểm cho từng chuyên gia:")
    for e in range(num_experts):
        st.markdown(f"**Chuyên gia {e+1}**")
        scores = []
        for i in range(num_lectures):
            row = []
            st.markdown(f"*{names[i]}*")
            for crit in criteria:
                score = st.number_input(f"{crit} ({names[i]})", min_value=0.0, max_value=100.0, step=1.0,
                                        key=f"{e}_{i}_{crit}")
                row.append(score)
            scores.append(row)
        all_scores.append(scores)

    if st.button("Tiếp tục"):
        st.session_state.names = names
        st.session_state.raw_scores = np.mean(np.array(all_scores), axis=0)  # Trung bình giữa các chuyên gia
        st.session_state.step = 2

# Bước 2: Phân tích TOPSIS + AHP + Entropy + Picture Fuzzy
elif st.session_state.step == 2:
    st.header("Bước 2: Kết quả phân tích TOPSIS-AHP-PICTURE FUZZY")

    X = np.array(st.session_state.raw_scores)
    m, n = X.shape

    # B1: Chuẩn hóa dữ liệu
    R = X / np.sqrt((X**2).sum(axis=0))

    # B2: Tính trọng số Entropy
    P = R / R.sum(axis=0)
    P = np.nan_to_num(P, nan=0.0)
    E = -np.sum(P * np.log(P + 1e-12), axis=0) / np.log(m)
    G = 1 - E
    weights = G / G.sum()

    # B3: Ma trận trọng số chuẩn hóa
    V = R * weights

    # B4: Giải pháp lý tưởng PIS & NIS
    V_pos = V.max(axis=0)
    V_neg = V.min(axis=0)

    # B5: Khoảng cách đến PIS và NIS
    R_pos = np.sum(np.abs(V - V_pos), axis=1)
    R_neg = np.sum(np.abs(V - V_neg), axis=1)

    # B6: Chỉ số Ci
    Ci = R_neg / (R_pos + R_neg)

    result_df = pd.DataFrame({
        "Tên bài giảng": st.session_state.names,
        "Chỉ số Ci": Ci,
        "Xếp hạng": pd.Series(Ci).rank(ascending=False, method="min").astype(int)
    }).sort_values("Xếp hạng")

    st.subheader("📈 Kết quả xếp hạng")
    st.dataframe(result_df, use_container_width=True)

    st.subheader("📊 Trọng số tiêu chí (Entropy)")
    st.write({criteria[i]: round(weights[i], 4) for i in range(len(criteria))})

    # Lưu kết quả
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("history", exist_ok=True)
    file_path = f"history/topsis_result_{timestamp}.csv"
    result_df.to_csv(file_path, index=False)
    st.success(f"✅ Kết quả đã lưu vào: {file_path}")

    if st.button("🔁 Thực hiện lại"):
        st.session_state.step = 1

    if st.button("📁 Xem lịch sử đánh giá"):
        st.session_state.step = 3

# Bước 3: Lịch sử đánh giá
elif st.session_state.step == 3:
    st.header("📚 Lịch sử đánh giá")

    if os.path.exists("history"):
        files = sorted(os.listdir("history"), reverse=True)
        for file in files:
            st.markdown(f"**📄 {file}**")
            df = pd.read_csv(os.path.join("history", file))
            st.dataframe(df)
            delete_button = st.button(f"🗑️ Xóa bài đánh giá {file}", key=f"delete_{file}")
            if delete_button:
                try:
                    os.remove(os.path.join("history", file))
                    st.success(f"Đã xóa bài đánh giá {file}")
                except Exception as e:
                    st.error(f"Lỗi khi xóa: {e}")
            st.markdown("---")
    else:
        st.info("Chưa có lịch sử đánh giá.")

    if st.button("🗑️ Xóa toàn bộ lịch sử đánh giá"):
        try:
            shutil.rmtree("history")
            st.success("Đã xóa toàn bộ lịch sử.")
        except Exception as e:
            st.error(f"Lỗi khi xoá: {e}")

    if st.button("⬅ Quay lại"):
        st.session_state.step = 1
