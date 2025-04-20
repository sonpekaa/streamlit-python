import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
from io import BytesIO
import shutil  # dùng để xóa thư mục

st.set_page_config(page_title="Đánh giá bài giảng - AHP & TOPSIS", layout="centered")

st.title("📊 Phần mềm đánh giá bài giảng (AHP + TOPSIS)")

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

# Điều hướng nhiều trang bằng session state
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

# --- Bước 1: Nhập thông tin cơ bản ---
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

# --- Bước 2: Nhập điểm đánh giá từ chuyên gia ---
elif st.session_state.step == 2:
    st.header("Bước 2: Nhập điểm đánh giá")
    scores = []
    for i in range(st.session_state.so_chuyen_gia):
        st.markdown(f"**Chuyên gia {i+1}:**")
        expert_scores = []
        for crit in criteria:
            score = st.slider(crit, min_value=1, max_value=10, key=f"{crit}_{i}")  # Đã đổi sang 1–10
            expert_scores.append(score)
        scores.append(expert_scores)

    if st.button("Đánh giá"):
        st.session_state.expert_scores = scores
        st.session_state.step = 3

# --- Bước 3: Kết quả ---
elif st.session_state.step == 3:
    st.header("Bước 3: Kết quả đánh giá")
    try:
        scores_matrix = np.array(st.session_state.expert_scores)

        # AHP: Trọng số từ điểm trung bình chuyên gia
        avg_scores = scores_matrix.mean(axis=0)
        pairwise_matrix = np.outer(avg_scores, 1/avg_scores)
        priority_vector = pairwise_matrix.mean(axis=1)
        weights = priority_vector / priority_vector.sum()

        # TOPSIS
        normalized = scores_matrix / np.sqrt((scores_matrix**2).sum(axis=0))
        weighted = normalized * weights

        ideal_best = weighted.max(axis=0)
        ideal_worst = weighted.min(axis=0)

        distances_best = np.linalg.norm(weighted - ideal_best, axis=1)
        distances_worst = np.linalg.norm(weighted - ideal_worst, axis=1)
        topsis_scores = distances_worst / (distances_best + distances_worst)

        final_score = topsis_scores.mean()

        if final_score > 0.7:
            classification = "Xuất sắc"
        elif final_score > 0.5:
            classification = "Tốt"
        elif final_score > 0.3:
            classification = "Trung bình"
        else:
            classification = "Kém"

        st.success(f"✅ Bài giảng: {st.session_state.ten_bai_giang}")
        st.write(f"**Điểm đánh giá:** {final_score:.4f}")
        st.write(f"**Xếp loại:** {classification}")

        # --- Lưu kết quả ---
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = f"output/{st.session_state.ten_bai_giang.replace(' ', '_')}_{timestamp}"
        os.makedirs(save_dir, exist_ok=True)

        uploaded_filename = st.session_state.uploaded_file.name
        uploaded_path = os.path.join(save_dir, uploaded_filename)

        with open(uploaded_path, "wb") as f:
            f.write(st.session_state.uploaded_file.read())

        results_path = "output/results.csv"
        df_result = pd.DataFrame([{ 
            "Tên bài giảng": st.session_state.ten_bai_giang,
            "Tên file bài giảng": uploaded_filename,
            "Đường dẫn file": uploaded_path,
            "Điểm đánh giá": final_score,
            "Xếp loại": classification,
            "Thời gian": timestamp
        }])

        if os.path.exists(results_path):
            old = pd.read_csv(results_path)
            df_result = pd.concat([old, df_result], ignore_index=True)

        df_result.to_csv(results_path, index=False)
        st.success("📁 Kết quả đã được lưu cùng với file bài giảng.")

        if st.button("Xem danh sách kết quả đã lưu"):
            st.session_state.step = 4

    except Exception as e:
        st.error(f"Lỗi khi đánh giá: {e}")

    if st.button("🔁 Đánh giá lại"):
        st.session_state.step = 1

# --- Bước 4: Xem kết quả đã lưu ---
elif st.session_state.step == 4:
    st.header("📚 Danh sách kết quả đã lưu")
    results_path = "output/results.csv"
    if os.path.exists(results_path):
        df = pd.read_csv(results_path)

        for index, row in df.iterrows():
            st.subheader(f"📘 {row['Tên bài giảng']}")
            st.write(f"**Điểm:** {row['Điểm đánh giá']:.4f}")
            st.write(f"**Xếp loại:** {row['Xếp loại']}")
            st.write(f"**Thời gian:** {row['Thời gian']}")
            if os.path.exists(row["Đường dẫn file"]):
                with open(row["Đường dẫn file"], "rb") as f:
                    st.download_button("⬇ Tải file bài giảng", f, file_name=row["Tên file bài giảng"] )
            
            # Nút xóa bài đánh giá
            if st.button(f"🗑️ Xóa bài đánh giá {row['Tên bài giảng']}", key=f"delete_{row['Tên bài giảng']}"):
                try:
                    os.remove(row["Đường dẫn file"])  # Xóa file bài giảng
                    df = df.drop(index)  # Xóa dòng dữ liệu tương ứng
                    df.to_csv(results_path, index=False)  # Lưu lại file sau khi xóa
                    st.success(f"✅ Đã xóa bài đánh giá {row['Tên bài giảng']}")
                except Exception as e:
                    st.error(f"Lỗi khi xóa bài đánh giá: {e}")
            st.markdown("---")
    else:
        st.info("Chưa có kết quả nào được lưu.")

    # --- Nút xóa toàn bộ lịch sử ---
    if st.button("🗑️ Xóa toàn bộ lịch sử đánh giá"):
        try:
            if os.path.exists("output"):
                shutil.rmtree("output")
            st.success("✅ Đã xoá toàn bộ lịch sử đánh giá.")
        except Exception as e:
            st.error(f"Lỗi khi xoá: {e}")

    if st.button("⬅ Quay lại"):
        st.session_state.step = 1
