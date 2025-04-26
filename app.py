import streamlit as st
import pandas as pd
import numpy as np
import os
import base64
import hashlib
import json
from datetime import datetime

# ------------------ USER AUTHENTICATION ------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists("users.json"):
        return {}
    with open("users.json", "r") as f:
        return json.load(f)

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

def create_user_dir(username):
    os.makedirs(f"users/{username}", exist_ok=True)

def login_page():
    st.title("🔐 Đăng nhập hệ thống")
    users = load_users()

    tab1, tab2 = st.tabs(["Đăng nhập", "Tạo tài khoản"])

    with tab1:
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập"):
            if username in users and users[username]["password"] == hash_password(password):
                st.success(f"Chào mừng {username}!")
                st.session_state.user = username
                st.session_state.step = 1
            else:
                st.error("Sai tên đăng nhập hoặc mật khẩu")

    with tab2:
        new_username = st.text_input("Tạo tên đăng nhập")
        new_password = st.text_input("Tạo mật khẩu", type="password")
        if st.button("Tạo tài khoản"):
            if new_username in users:
                st.warning("Tên đăng nhập đã tồn tại.")
            else:
                users[new_username] = {"password": hash_password(new_password)}
                save_users(users)
                create_user_dir(new_username)
                st.success("Tạo tài khoản thành công! Hãy đăng nhập.")

# ------------------ STREAMLIT APP ------------------
st.set_page_config(page_title="Đánh giá bài giảng - AHP & TOPSIS", layout="wide")

if 'user' not in st.session_state:
    login_page()
    st.stop()

# Sidebar
with st.sidebar:
    st.write(f"👤 Đăng nhập với: `{st.session_state.user}`")

    if st.button("🚪 Đăng xuất"):
        st.session_state.clear()
        st.rerun()

    if st.button("🏠 Trang chủ"):
        st.session_state.view_history = False
        st.session_state.step = 1
        st.rerun()

    if st.button("📚 Xem lịch sử đánh giá"):
        st.session_state.view_history = True
        st.rerun()

if st.session_state.get("view_history", False):
    st.title("📚 Lịch sử đánh giá của bạn")
    user_folder = f"users/{st.session_state.user}"
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    search_term = st.text_input("🔍 Tìm kiếm tên bài giảng")
    files = [f for f in os.listdir(user_folder) if f.endswith(".csv")]
    filtered_files = [f for f in files if search_term.lower() in f.lower()]

    if filtered_files:
        for f in sorted(filtered_files, reverse=True):
            with open(os.path.join(user_folder, f), "rb") as file:
                st.download_button(
                    label=f"📥 {f}",
                    data=file,
                    file_name=f,
                    mime="text/csv"
                )
    else:
        st.info("❗ Không tìm thấy bài giảng phù hợp.")
    st.stop()

# ------------- INIT SESSION VARS -------------
criteria = []
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

# Load criteria from CSV
def load_criteria():
    try:
        df = pd.read_csv("criteria.csv")
        return df['Tiêu chí'].dropna().tolist()
    except:
        return [
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

criteria = load_criteria()

# ------------------ STEP 1 ------------------
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

# ------------------ STEP 2 ------------------
elif st.session_state.step == 2:
    st.header("Bước 2: Nhập điểm và trọng số chuyên gia")

    col1, col2 = st.columns(2)

    with col1:
        scores = []
        for i in range(st.session_state.so_chuyen_gia):
            st.markdown(f"**Chuyên gia {i+1}:**")
            expert_scores = []
            for crit in criteria:
                score = st.slider(f"{crit}", min_value=1, max_value=10, key=f"score_{crit}_{i}")
                expert_scores.append(score)
            scores.append(expert_scores)

    with col2:
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

# ------------------ STEP 3 ------------------
elif st.session_state.step == 3:
    st.header("Bước 3: Kết quả đánh giá")

    try:
        scores_matrix = np.array(st.session_state.expert_scores)
        weights_expert = np.array(st.session_state.expert_weights)

        norm = (scores_matrix - scores_matrix.min(axis=0)) / (scores_matrix.max(axis=0) - scores_matrix.min(axis=0) + 1e-9)

        weighted_expert = norm * weights_expert
        pis_expert = np.max(weighted_expert, axis=0)
        nis_expert = np.min(weighted_expert, axis=0)

        dist_pis_expert = np.linalg.norm(weighted_expert - pis_expert, axis=1)
        dist_nis_expert = np.linalg.norm(weighted_expert - nis_expert, axis=1)
        topsis_expert_scores = dist_nis_expert / (dist_pis_expert + dist_nis_expert + 1e-9)

        pij = scores_matrix / (scores_matrix.sum(axis=0) + 1e-9)
        ej = -np.nansum(pij * np.log(pij + 1e-9), axis=0) / np.log(len(scores_matrix))
        dj = 1 - ej
        weights_entropy = dj / dj.sum()

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

        # Lưu lịch sử
        username = st.session_state.user
        output_dir = f"users/{username}"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{st.session_state.ten_bai_giang}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        df_ket_qua.to_csv(output_path, index=False)

    except Exception as e:
        st.error(f"Lỗi khi đánh giá: {e}")

    if st.button("🔁 Đánh giá lại"):
        st.session_state.step = 1
