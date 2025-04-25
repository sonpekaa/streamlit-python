import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
from io import BytesIO

st.set_page_config(page_title="Đánh giá bài giảng - AHP & TOPSIS", layout="wide")
st.title("📊 Phần mềm đánh giá bài giảng")

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

# --- State init ---
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
if 'file_url' not in st.session_state:
    st.session_state.file_url = ""
if 'evaluated_files' not in st.session_state:
    st.session_state.evaluated_files = []

# --- Bước 1 ---
if st.session_state.step == 1:
    st.header("Bước 1: Tải file & nhập thông tin")
    uploaded_file = st.file_uploader("Tải lên file bài giảng", type=["pdf", "docx", "pptx"])
    st.session_state.ten_bai_giang = st.text_input("Nhập tên bài giảng")
    st.session_state.so_chuyen_gia = st.number_input("Số lượng chuyên gia đánh giá", min_value=1, step=1, format="%d")

    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        bytes_data = uploaded_file.read()
        b64 = base64.b64encode(bytes_data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{uploaded_file.name}">📥 Tải lại file bài giảng</a>'
        st.session_state.file_url = href

    if st.button("Tiếp tục"):
        if st.session_state.uploaded_file and st.session_state.ten_bai_giang:
            st.session_state.step = 2
        else:
            st.warning("Vui lòng nhập đầy đủ thông tin và tải file bài giảng.")

# --- Bước 2 ---
elif st.session_state.step == 2:
    st.header("Bước 2: Nhập điểm & trọng số đánh giá")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📌 Nhập điểm từ chuyên gia")
        scores = []
        for i in range(st.session_state.so_chuyen_gia):
            st.markdown(f"**Chuyên gia {i+1}:**")
            expert_scores = []
            for crit in criteria:
                score = st.slider(f"{crit}", min_value=1, max_value=10, key=f"score_{crit}_{i}")
                expert_scores.append(score)
            scores.append(expert_scores)

    with col2:
        st.subheader("⚖️ Trọng số tiêu chí (tổng = 1)")
        weights_input = []
        total = 0.0
        for crit in criteria:
            w = st.number_input(f"{crit}", min_value=0.0, max_value=1.0, step=0.01, key=f"w_{crit}")
            weights_input.append(w)
            total += w

        if not np.isclose(total, 1.0):
            st.warning(f"Tổng trọng số hiện tại là {total:.2f}, cần bằng 1 để tiếp tục.")
        else:
            if st.button("Đánh giá"):
                st.session_state.expert_scores = scores
                st.session_state.expert_weights = weights_input
                st.session_state.step = 3

# --- Bước 3 ---
elif st.session_state.step == 3:
    st.header("Bước 3: Kết quả đánh giá")

    try:
        scores_matrix = np.array(st.session_state.expert_scores)
        weights_expert = np.array(st.session_state.expert_weights)

        # --- Chuẩn hóa Min-Max ---
        norm = (scores_matrix - scores_matrix.min(axis=0)) / (scores_matrix.max(axis=0) - scores_matrix.min(axis=0) + 1e-9)

        # --- TOPSIS chuyên gia ---
        weighted_expert = norm * weights_expert
        pis_expert = np.max(weighted_expert, axis=0)
        nis_expert = np.min(weighted_expert, axis=0)
        dist_pis_expert = np.linalg.norm(weighted_expert - pis_expert, axis=1)
        dist_nis_expert = np.linalg.norm(weighted_expert - nis_expert, axis=1)
        topsis_expert_scores = dist_nis_expert / (dist_pis_expert + dist_nis_expert + 1e-9)

        # --- Entropy weights ---
        pij = scores_matrix / (scores_matrix.sum(axis=0) + 1e-9)
        ej = -np.nansum(pij * np.log(pij + 1e-9), axis=0) / np.log(len(scores_matrix))
        dj = 1 - ej
        weights_entropy = dj / dj.sum()

        # --- TOPSIS entropy ---
        weighted_entropy = norm * weights_entropy
        pis_entropy = np.max(weighted_entropy, axis=0)
        nis_entropy = np.min(weighted_entropy, axis=0)
        dist_pis_entropy = np.linalg.norm(weighted_entropy - pis_entropy, axis=1)
        dist_nis_entropy = np.linalg.norm(weighted_entropy - nis_entropy, axis=1)
        topsis_entropy_scores = dist_nis_entropy / (dist_pis_entropy + dist_nis_entropy + 1e-9)

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
            "Phương pháp": ["Chuyên gia", "Entropy"],
            "Điểm đánh giá": [avg_expert, avg_entropy],
            "Xếp loại": [xep_loai(avg_expert), xep_loai(avg_entropy)]
        })
        st.dataframe(df_ket_qua, use_container_width=True)

        st.write("### 📊 Trọng số tiêu chí")
        df_weights = pd.DataFrame({
            "Tiêu chí": criteria,
            "Trọng số chuyên gia": weights_expert,
            "Trọng số Entropy": weights_entropy
        })
        st.dataframe(df_weights, use_container_width=True)

        st.write("### 🧑‍🔬 Bảng điểm của các chuyên gia")
        df_diem = pd.DataFrame(scores_matrix, columns=criteria)
        df_diem.index = [f"Chuyên gia {i+1}" for i in range(scores_matrix.shape[0])]
        st.dataframe(df_diem, use_container_width=True)

        st.write("### 📥 File bài giảng")
        st.markdown(st.session_state.file_url, unsafe_allow_html=True)

        # --- Lưu file kết quả đánh giá ---
        filename = f"{st.session_state.ten_bai_giang.replace(' ', '_')}_ket_qua.csv"
        output = BytesIO()
        df_ket_qua.to_csv(output, index=False)
        b64_result = base64.b64encode(output.getvalue()).decode()
        download_link = f'<a href="data:file/csv;base64,{b64_result}" download="{filename}">📄 Tải kết quả đánh giá</a>'
        st.markdown(download_link, unsafe_allow_html=True)

        # --- Thêm vào danh sách đã đánh giá ---
        st.session_state.evaluated_files.append((st.session_state.ten_bai_giang, download_link))

        st.write("### 🗂️ Danh sách bài giảng đã đánh giá:")
        for name, link in st.session_state.evaluated_files:
            st.markdown(f"- **{name}**: {link}", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Lỗi khi đánh giá: {e}")

    if st.button("🔁 Đánh giá lại"):
        st.session_state.step = 1
