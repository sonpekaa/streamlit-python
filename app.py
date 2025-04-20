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
if 'expert_weights' not in st.session_state:
    st.session_state.expert_weights = []

# --- Bước 1: Tải file và nhập thông tin ---
if st.session_state.step == 1:
    st.header("Bước 1: Tải file & nhập thông tin")
    st.session_state.uploaded_file = st.file_uploader("Tải lên file bài giảng", type=["pdf", "docx", "pptx"])
    st.session_state.ten_bai_giang = st.text_input("Nhập tên bài giảng")
    st.session_state.so_chuyen_gia = st.number_input("Số lượng chuyên gia đánh giá", min_value=1, step=1, format="%d")

    if st.button("Tiếp tục"):
        if st.session_state.uploaded_file and st.session_state.ten_bai_giang:
            st.session_state.step = 2
        else:
            st.warning("Vui lòng nhập đầy đủ thông tin và tải file bài giảng.")

# --- Bước 2: Nhập điểm đánh giá ---
elif st.session_state.step == 2:
    st.header("Bước 2: Nhập điểm và trọng số chuyên gia")
    scores = []
    for i in range(st.session_state.so_chuyen_gia):
        st.markdown(f"**Chuyên gia {i+1}:**")
        expert_scores = []
        for crit in criteria:
            score = st.slider(f"{crit}", min_value=1, max_value=10, key=f"score_{crit}_{i}")
            expert_scores.append(score)
        scores.append(expert_scores)

    st.subheader("Trọng số chuyên gia (tổng = 1)")
    weights_input = []
    total = 0.0
    for crit in criteria:
        w = st.number_input(f"Trọng số cho: {crit}", min_value=0.0, max_value=1.0, step=0.01, key=f"w_{crit}")
        weights_input.append(w)
        total += w
    if not np.isclose(total, 1.0):
        st.warning(f"Tổng trọng số hiện tại là {total:.2f}, cần bằng 1 để tiếp tục.")
    else:
        if st.button("Đánh giá"):
            st.session_state.expert_scores = scores
            st.session_state.expert_weights = weights_input
            st.session_state.step = 3

# --- Bước 3: Kết quả đánh giá ---
elif st.session_state.step == 3:
    st.header("Bước 3: Kết quả đánh giá")
    try:
        scores_matrix = np.array(st.session_state.expert_scores)
        weights_expert = np.array(st.session_state.expert_weights)

        # Chuẩn hóa ma trận
        norm = scores_matrix / np.sqrt((scores_matrix**2).sum(axis=0))

        # TOPSIS chuyên gia
        weighted_expert = norm * weights_expert
        pis_expert = np.max(weighted_expert, axis=0)
        nis_expert = np.min(weighted_expert, axis=0)

        dist_pis_expert = np.linalg.norm(weighted_expert - pis_expert, axis=1)
        dist_nis_expert = np.linalg.norm(weighted_expert - nis_expert, axis=1)
        topsis_expert_scores = dist_nis_expert / (dist_pis_expert + dist_nis_expert)

        # Tính trọng số bằng Entropy
        pij = scores_matrix / scores_matrix.sum(axis=0)
        ej = -np.nansum(pij * np.log(pij + 1e-9), axis=0) / np.log(len(scores_matrix))
        dj = 1 - ej
        weights_entropy = dj / dj.sum()

        # TOPSIS entropy
        weighted_entropy = norm * weights_entropy
        pis_entropy = np.max(weighted_entropy, axis=0)
        nis_entropy = np.min(weighted_entropy, axis=0)

        dist_pis_entropy = np.linalg.norm(weighted_entropy - pis_entropy, axis=1)
        dist_nis_entropy = np.linalg.norm(weighted_entropy - nis_entropy, axis=1)
        topsis_entropy_scores = dist_nis_entropy / (dist_pis_entropy + dist_nis_entropy)

        avg_expert = topsis_expert_scores.mean()
        avg_entropy = topsis_entropy_scores.mean()

        def xep_loai(score):
            if score > 0.7:
                return "Xuất sắc"
            elif score > 0.5:
                return "Tốt"
            elif score > 0.3:
                return "Trung bình"
            else:
                return "Kém"

        st.success(f"✅ Bài giảng: {st.session_state.ten_bai_giang}")
        st.write("### 🎯 So sánh kết quả đánh giá:")
        df_ket_qua = pd.DataFrame({
            "Phương pháp": ["Chuyên gia (AHP)", "Entropy"],
            "Điểm đánh giá": [avg_expert, avg_entropy],
            "Xếp loại": [xep_loai(avg_expert), xep_loai(avg_entropy)]
        })
        st.dataframe(df_ket_qua, use_container_width=True)

        st.write("### 📊 Trọng số chuyên gia")
        df_weights = pd.DataFrame({
            "Tiêu chí": criteria,
            "Trọng số chuyên gia": weights_expert,
            "Trọng số Entropy": weights_entropy
        })
        st.dataframe(df_weights, use_container_width=True)

    except Exception as e:
        st.error(f"Lỗi khi đánh giá: {e}")

    if st.button("🔁 Đánh giá lại"):
        st.session_state.step = 1
