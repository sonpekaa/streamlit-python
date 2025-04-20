import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
from io import BytesIO
import shutil

st.set_page_config(page_title="Đánh giá bài giảng - AHP & TOPSIS", layout="centered")
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
if 'custom_weights' not in st.session_state:
    st.session_state.custom_weights = []

# Bước 1: Nhập thông tin
if st.session_state.step == 1:
    st.header("Bước 1: Nhập thông tin")
    st.session_state.uploaded_file = st.file_uploader("Tải lên file bài giảng", type=["pdf", "docx", "pptx"])
    st.session_state.ten_bai_giang = st.text_input("Nhập tên bài giảng")
    st.session_state.so_chuyen_gia = st.number_input("Số lượng chuyên gia đánh giá", min_value=1, step=1, format="%d")

    if st.button("Tiếp tục"):
        if st.session_state.uploaded_file and st.session_state.ten_bai_giang:
            st.session_state.step = 2
        else:
            st.warning("Vui lòng nhập đầy đủ thông tin và tải file bài giảng.")

# Bước 2: Nhập điểm đánh giá
elif st.session_state.step == 2:
    st.header("Bước 2: Nhập điểm đánh giá từ chuyên gia")
    scores = []
    for i in range(st.session_state.so_chuyen_gia):
        st.markdown(f"**Chuyên gia {i+1}:**")
        expert_scores = []
        for crit in criteria:
            score = st.slider(crit, min_value=1, max_value=10, key=f"{crit}_{i}")
            expert_scores.append(score)
        scores.append(expert_scores)
    st.session_state.expert_scores = scores
    if st.button("Tiếp tục nhập trọng số chuyên gia"):
        st.session_state.step = 3

# Bước 3: Nhập trọng số chuyên gia
elif st.session_state.step == 3:
    st.header("Bước 3: Nhập trọng số chuyên gia cho từng tiêu chí")
    weights_input = []
    for i, crit in enumerate(criteria):
        val = st.number_input(f"Trọng số cho tiêu chí: {crit}", min_value=0.0, step=0.1, key=f"w_{i}")
        weights_input.append(val)

    sum_weights = sum(weights_input)
    if sum_weights == 0:
        st.warning("Tổng trọng số không được bằng 0.")
    else:
        normalized_weights = [w / sum_weights for w in weights_input]
        st.session_state.custom_weights = normalized_weights

        if st.button("Xem kết quả đánh giá"):
            st.session_state.step = 4

# Bước 4: Kết quả
elif st.session_state.step == 4:
    st.header("Bước 4: Kết quả đánh giá bài giảng")
    try:
        scores_matrix = np.array(st.session_state.expert_scores)

        # --- Bộ trọng số chuyên gia ---
        weights_custom = np.array(st.session_state.custom_weights)

        # --- Bộ trọng số Entropy ---
        P = scores_matrix / scores_matrix.sum(axis=0)
        entropy = -np.nansum(P * np.log(P + 1e-10), axis=0) / np.log(len(scores_matrix))
        d = 1 - entropy
        weights_entropy = d / d.sum()

        def topsis(matrix, weights):
            norm = matrix / np.sqrt((matrix**2).sum(axis=0))
            weighted = norm * weights
            ideal_best = weighted.max(axis=0)
            ideal_worst = weighted.min(axis=0)
            d_best = np.linalg.norm(weighted - ideal_best, axis=1)
            d_worst = np.linalg.norm(weighted - ideal_worst, axis=1)
            score = d_worst / (d_best + d_worst)
            return score.mean()

        score_custom = topsis(scores_matrix, weights_custom)
        score_entropy = topsis(scores_matrix, weights_entropy)

        def classify(score):
            if score > 0.7:
                return "Xuất sắc"
            elif score > 0.5:
                return "Tốt"
            elif score > 0.3:
                return "Trung bình"
            else:
                return "Kém"

        st.subheader("📌 Kết quả đánh giá:")
        st.write(f"**Theo trọng số chuyên gia:** {score_custom:.4f} ({classify(score_custom)})")
        st.write(f"**Theo trọng số Entropy:** {score_entropy:.4f} ({classify(score_entropy)})")

        # Hiển thị bảng trọng số
        st.subheader("📋 Bảng so sánh trọng số")
        weight_table = pd.DataFrame({
            "Tiêu chí": criteria,
            "Trọng số chuyên gia": weights_custom,
            "Trọng số Entropy": weights_entropy
        })
        st.dataframe(weight_table, use_container_width=True)

    except Exception as e:
        st.error(f"Lỗi: {e}")

    if st.button("🔁 Đánh giá lại"):
        st.session_state.step = 1
