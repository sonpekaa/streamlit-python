import streamlit as st
import pandas as pd
import numpy as np
import os
import datetime
from io import BytesIO
import shutil

# --- Cấu hình giao diện ---
st.set_page_config(page_title="Đánh giá bài giảng - AHP & TOPSIS", layout="centered")
st.title("📊 Phần mềm đánh giá bài giảng (AHP + TOPSIS)")

# --- Tiêu chí đánh giá ---
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

# --- Khởi tạo session state ---
for key, default in {
    'step': 1,
    'uploaded_file': None,
    'ten_bai_giang': "",
    'so_chuyen_gia': 1,
    'expert_scores': []
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- Tiến độ ---
step_names = ["📁 Tải file", "📝 Nhập điểm", "📊 Kết quả", "📚 Danh sách"]
st.markdown("### ⏳ Tiến độ thực hiện")
st.progress((st.session_state.step - 1) / 3)
st.markdown(f"**Bước {st.session_state.step} trên 4: {step_names[st.session_state.step - 1]}**")

# --- Bước 1: Tải file và nhập thông tin ---
if st.session_state.step == 1:
    st.header("Bước 1: Nhập thông tin bài giảng và chuyên gia")
    st.markdown("- 📎 Tải lên **file bài giảng** (.pdf, .docx, .pptx)")
    st.markdown("- ✍️ Nhập **tên bài giảng** và **số chuyên gia đánh giá**")

    st.session_state.uploaded_file = st.file_uploader("📂 Chọn file bài giảng", type=["pdf", "docx", "pptx"])
    st.session_state.ten_bai_giang = st.text_input("📘 Tên bài giảng")
    st.session_state.so_chuyen_gia = st.number_input("👨‍🏫 Số lượng chuyên gia đánh giá", min_value=1, max_value=10, step=1)

    if st.button("➡️ Tiếp tục sang bước 2"):
        if st.session_state.uploaded_file and st.session_state.ten_bai_giang.strip():
            st.session_state.step = 2
        else:
            st.warning("⚠️ Vui lòng nhập đầy đủ thông tin và tải file bài giảng.")

# --- Bước 2: Nhập điểm đánh giá từ chuyên gia ---
elif st.session_state.step == 2:
    st.header("Bước 2: Nhập điểm đánh giá từ chuyên gia")
    st.markdown("Chuyên gia đánh giá từng tiêu chí từ **1 (thấp)** đến **10 (cao)**.")
    scores = []

    for i in range(st.session_state.so_chuyen_gia):
        st.markdown(f"#### 👨‍⚖️ Chuyên gia {i+1}")
        expert_scores = []
        for crit in criteria:
            score = st.slider(f"{crit} (Chuyên gia {i+1})", 1, 10, key=f"{crit}_{i}")
            expert_scores.append(score)
        scores.append(expert_scores)

    if st.button("📊 Thực hiện đánh giá"):
        st.session_state.expert_scores = scores
        st.session_state.step = 3

# --- Bước 3: Hiển thị kết quả đánh giá ---
elif st.session_state.step == 3:
    st.header("Bước 3: Kết quả đánh giá")
    try:
        scores_matrix = np.array(st.session_state.expert_scores)

        # === AHP đơn giản hóa: Dùng trung bình tiêu chí để tạo trọng số ===
        avg_scores = scores_matrix.mean(axis=0)
        pairwise_matrix = np.outer(avg_scores, 1 / avg_scores)
        priority_vector = pairwise_matrix.mean(axis=1)
        weights = priority_vector / priority_vector.sum()

        # === TOPSIS ===
        normalized = scores_matrix / np.sqrt((scores_matrix**2).sum(axis=0))
        weighted = normalized * weights

        ideal_best = weighted.max(axis=0)
        ideal_worst = weighted.min(axis=0)

        distances_best = np.linalg.norm(weighted - ideal_best, axis=1)
        distances_worst = np.linalg.norm(weighted - ideal_worst, axis=1)
        topsis_scores = distances_worst / (distances_best + distances_worst)
        final_score = topsis_scores.mean()

        # Xếp loại
        if final_score > 0.7:
            classification = "Xuất sắc"
        elif final_score > 0.5:
            classification = "Tốt"
        elif final_score > 0.3:
            classification = "Trung bình"
        else:
            classification = "Kém"

        # Hiển thị kết quả
        st.success(f"✅ Bài giảng: **{st.session_state.ten_bai_giang}**")
        st.metric("🎯 Điểm tổng hợp", f"{final_score:.4f}")
        st.write(f"**Xếp loại:** {classification}")

        # Hiển thị bảng chi tiết
        df_scores = pd.DataFrame(scores_matrix, columns=criteria)
        df_scores["TOPSIS score"] = topsis_scores
        st.markdown("### 📋 Điểm chi tiết từng chuyên gia")
        st.dataframe(df_scores.style.format(precision=2))

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
        st.success("📁 Kết quả đã được lưu.")

        if st.button("📚 Xem danh sách kết quả đã lưu"):
            st.session_state.step = 4

    except Exception as e:
        st.error(f"Lỗi khi tính toán: {e}")

    if st.button("🔁 Đánh giá lại từ đầu"):
        st.session_state.step = 1
        st.session_state.uploaded_file = None

# --- Bước 4: Danh sách kết quả đã lưu ---
elif st.session_state.step == 4:
    st.header("📚 Danh sách kết quả đã lưu")
    results_path = "output/results.csv"

    if os.path.exists(results_path):
        df = pd.read_csv(results_path)

        for _, row in df.iterrows():
            st.subheader(f"📘 {row['Tên bài giảng']}")
            st.write(f"**Điểm:** {row['Điểm đánh giá']:.4f}")
            st.write(f"**Xếp loại:** {row['Xếp loại']}")
            st.write(f"**Thời gian:** {row['Thời gian']}")
            if os.path.exists(row["Đường dẫn file"]):
                with open(row["Đường dẫn file"], "rb") as f:
                    st.download_button("⬇ Tải file bài giảng", f, file_name=row["Tên file bài giảng"] )
            st.markdown("---")
    else:
        st.info("⚠️ Chưa có kết quả nào được lưu.")

    # Xóa toàn bộ lịch sử
    if st.button("🗑️ Xoá toàn bộ lịch sử đánh giá"):
        try:
            if os.path.exists("output"):
                shutil.rmtree("output")
            st.success("✅ Đã xoá toàn bộ dữ liệu.")
            st.session_state.step = 1
            st.session_state.uploaded_file = None
        except Exception as e:
            st.error(f"Lỗi khi xoá: {e}")

    if st.button("⬅ Quay lại trang đầu"):
        st.session_state.step = 1

