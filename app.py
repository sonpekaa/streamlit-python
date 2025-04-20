# Nâng cấp ứng dụng đánh giá bài giảng với trọng số chuyên gia và so sánh AHP vs Entropy
import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
from io import BytesIO
import shutil

st.set_page_config(page_title="Đánh giá bài giảng - AHP & TOPSIS", layout="wide")
st.title("📊 Phần mềm đánh giá bài giảng (AHP + TOPSIS + Entropy)")

criteria = [
    "Khả năng khảo sát thực tế và xây dựng kiến thức",
    "Thúc đẩy học tập tích cực và đánh giá xác thực",
    "Thu hút sinh viên bởi các động lực và thách thức",
    "Cung cấp các công cụ để tăng năng suất học",
    "Cung cấp công cụ hỗ trợ tư duy cao",
    "Tăng tính độc lập của người học",
    "Tăng cường sự hợp tác và cộng tác",
    "Thiết kế chương trình học cho người học",
    "Khắc phục khuyết điểm thể chất"
]

if 'step' not in st.session_state:
    st.session_state.step = 1
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'ten_bai_giang' not in st.session_state:
    st.session_state.ten_bai_giang = ""
if 'so_chuyen_gia' not in st.session_state:
    st.session_state.so_chuyen_gia = 1
if 'expert_scores' not in st.session_state:
    st.session_state.expert_scores = []
if 'ahp_weights_input' not in st.session_state:
    st.session_state.ahp_weights_input = []

# Bước 1: Nhập dữ liệu
def step1():
    st.header("Bước 1: Tải file & nhập thông tin")
    st.session_state.uploaded_file = st.file_uploader("Tải lên file bài giảng", type=["pdf", "docx", "pptx"])
    st.session_state.ten_bai_giang = st.text_input("Nhập tên bài giảng")
    st.session_state.so_chuyen_gia = st.number_input("Số lượng chuyên gia đánh giá", min_value=1, step=1, format="%d")

    if st.button("Tiếp tục"):
        if st.session_state.uploaded_file and st.session_state.ten_bai_giang:
            st.session_state.step = 2
        else:
            st.warning("Vui lòng nhập đầy đủ thông tin và tải file bài giảng.")

# Bước 2: Nhập điểm và trọng số

def step2():
    st.header("Bước 2: Nhập điểm đánh giá từ chuyên gia")
    scores = []
    weights = []
    for i in range(st.session_state.so_chuyen_gia):
        st.markdown(f"### Chuyên gia {i+1}")
        expert_scores = []
        expert_weights = []
        cols = st.columns(2)
        for j, crit in enumerate(criteria):
            score = cols[0].slider(f"{crit} (Điểm)", min_value=1, max_value=10, key=f"score_{i}_{j}")
            weight = cols[1].number_input(f"{crit} (Trọng số AHP)", min_value=0.0, step=0.1, key=f"weight_{i}_{j}")
            expert_scores.append(score)
            expert_weights.append(weight)
        scores.append(expert_scores)
        weights.append(expert_weights)

    if st.button("Tính toán và Đánh giá"):
        st.session_state.expert_scores = scores
        st.session_state.ahp_weights_input = weights
        st.session_state.step = 3

# Bước 3: Kết quả đánh giá và so sánh AHP vs Entropy

def step3():
    st.header("Bước 3: Kết quả đánh giá")
    try:
        scores_matrix = np.array(st.session_state.expert_scores)
        weights_matrix = np.array(st.session_state.ahp_weights_input)

        # AHP weights (bình quân trọng số từ chuyên gia)
        ahp_weights = weights_matrix.mean(axis=0)
        ahp_weights /= ahp_weights.sum()

        # Entropy weights
        norm_scores = scores_matrix / scores_matrix.sum(axis=0)
        entropy = -np.nansum(norm_scores * np.log(norm_scores + 1e-9), axis=0) / np.log(len(scores_matrix))
        diversity = 1 - entropy
        entropy_weights = diversity / np.sum(diversity)

        # TOPSIS đánh giá với AHP
        def topsis(matrix, weights):
            norm = matrix / np.sqrt((matrix**2).sum(axis=0))
            weighted = norm * weights
            best = weighted.max(axis=0)
            worst = weighted.min(axis=0)
            d_best = np.linalg.norm(weighted - best, axis=1)
            d_worst = np.linalg.norm(weighted - worst, axis=1)
            return d_worst / (d_best + d_worst + 1e-9)

        topsis_ahp = topsis(scores_matrix, ahp_weights).mean()
        topsis_entropy = topsis(scores_matrix, entropy_weights).mean()

        def classify(score):
            if score >= 0.7:
                return "Xuất sắc"
            elif score >= 0.5:
                return "Tốt"
            elif score >= 0.3:
                return "Trung bình"
            return "Kém"

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔍 Kết quả dùng trọng số chuyên gia (AHP)")
            st.metric("Điểm", round(topsis_ahp, 4))
            st.write("Xếp loại:", classify(topsis_ahp))

        with col2:
            st.subheader("🔍 Kết quả dùng trọng số Entropy")
            st.metric("Điểm", round(topsis_entropy, 4))
            st.write("Xếp loại:", classify(topsis_entropy))

        st.markdown("### 📊 So sánh Trọng số từng tiêu chí")
        df_weights = pd.DataFrame({
            "Tiêu chí": criteria,
            "Trọng số AHP": ahp_weights,
            "Trọng số Entropy": entropy_weights
        })
        st.dataframe(df_weights, use_container_width=True)

    except Exception as e:
        st.error(f"Lỗi khi xử lý dữ liệu: {e}")

    if st.button("🔁 Đánh giá lại"):
        st.session_state.step = 1

# Điều hướng theo bước
if st.session_state.step == 1:
    step1()
elif st.session_state.step == 2:
    step2()
elif st.session_state.step == 3:
    step3()
