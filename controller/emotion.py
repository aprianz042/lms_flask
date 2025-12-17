from function.koneksi import get_db_connection
import io, json, base64
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from flask import render_template
import matplotlib
matplotlib.use("Agg")  # backend non-GUI untuk server
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
import math

import google.generativeai as genai

'''
def get_emotion(materi, mahasiswa):
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    try:
        with connection.cursor() as cursor:
            sql_select = "SELECT * FROM enrollment WHERE id_materi = %s AND id_mahasiswa = %s;"
            cursor.execute(sql_select, (materi, mahasiswa))
            emotion = cursor.fetchone() 

        return emotion, None
    finally:
        connection.close()
'''

def get_mhs(mahasiswa):
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    try:
        with connection.cursor() as cursor:
            sql_select = "SELECT * FROM mahasiswa WHERE id_mahasiswa = %s;"
            cursor.execute(sql_select, (mahasiswa))
            mhs = cursor.fetchone() 

        return mhs, None
    finally:
        connection.close()


def get_emotion(materi, mahasiswa):
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    try:
        with connection.cursor() as cursor:
            sql_select = """
                SELECT 
                    e.id, e.id_mahasiswa, e.id_materi, e.last_access, e.emo_file,  
                    m.judul_materi,
                    mh.nama_mahasiswa
                FROM 
                    enrollment e
                JOIN
                    materi m ON e.id_materi = m.id
                JOIN 
                    mahasiswa mh ON e.id_mahasiswa = mh.id_mahasiswa
                WHERE 
                    e.id_materi = %s AND e.id_mahasiswa = %s
                ORDER BY 
                    e.last_access DESC
                LIMIT 1;
                """
            cursor.execute(sql_select, (materi, mahasiswa))
            emotion = cursor.fetchone() 
        return emotion, None
    finally:
        connection.close()

def grafik_fokus(file_json):
    JSON_PATH = f"emo_data/{file_json}"
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    engagement_map = {
        "Highly Engaged": 4,     
        "Confused": 3,
        "Boredom": 2,
        "Sleepy": 1,
        "Very Not Engaged": 0
    }

    # Fungsi untuk ubah string elapsed_time "00:00:01" jadi detik (int)
    def hms_to_seconds(s):
        h, m, sec = map(int, s.split(":"))
        return h * 3600 + m * 60 + sec

    data = []
    for r in rows:
        fval = r.get("engagement")
        etime = r.get("elapsed_time")
        if fval in engagement_map and etime:
            try:
                seconds = hms_to_seconds(etime)
            except Exception:
                continue
            data.append((seconds, engagement_map[fval]))

    if not data:
        return ""

    # Urutkan berdasarkan waktu
    data.sort(key=lambda x: x[0])

    # Siapkan data grafik
    rel_times = [t for t, _ in data]
    ys = [y for _, y in data]

    # Fungsi format jam:menit:detik
    def format_hhmmss(sec):
        h, rem = divmod(int(sec), 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # Plot
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.step(rel_times, ys, where="post")
    ax.scatter(rel_times, ys, s=12)
    ax.set_yticks([0, 1, 2, 3, 4], ["Very Not Engaged", "Sleepy", "Boredom", "Confused", "Highly Engaged"])

    # Batasi jumlah label sumbu-x maksimal 10
    max_labels = 10
    if len(rel_times) > max_labels:
        chosen_idx = np.linspace(0, len(rel_times) - 1, max_labels, dtype=int)
        xticks = [rel_times[i] for i in chosen_idx]
    else:
        xticks = rel_times

    ax.set_xticks(xticks)
    ax.set_xticklabels([format_hhmmss(s) for s in xticks], rotation=45)

    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def grafik_emotion(file_json, bw_adjust=0.8):
    JSON_PATH = f"emo_data/{file_json}"
    classes = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
    BAD = {"No face detected"}

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    # Filter: hanya data valid dan punya elapsed_time
    rows = [r for r in rows if r.get("emosi") in classes and r.get("elapsed_time") and r.get("emosi") not in BAD]
    if not rows:
        return ""

    def hms_to_seconds(s):
        h, m, sec = map(int, s.split(":"))
        return h * 3600 + m * 60 + sec

    for r in rows:
        try:
            r["sec"] = hms_to_seconds(r["elapsed_time"])
        except Exception:
            r["sec"] = None

    rows = [r for r in rows if r["sec"] is not None]
    if not rows:
        return ""

    # kumpulkan x per kelas
    x_by_class = {c: [r["sec"] for r in rows if r["emosi"] == c] for c in classes}
    have_any = any(len(xs) >= 2 for xs in x_by_class.values()) or any(len(xs) == 1 for xs in x_by_class.values())
    if not have_any:
        return ""

    # --- plot KDE overlapped ---
    sns.set_theme(style="darkgrid")
    fig, ax = plt.subplots(figsize=(10, 4))

    for cls in classes:
        xs = x_by_class[cls]
        if len(xs) >= 2:
            sns.kdeplot(xs, fill=True, alpha=0.35, bw_adjust=bw_adjust, label=cls, ax=ax)
        elif len(xs) == 1:
            ax.scatter(xs, [0], s=22, label=f"{cls} (1)")

    #ax.set_xlabel("Detik sejak mulai")
    #ax.set_ylabel("Kepadatan")
    #ax.set_title("Distribusi Emosi")
    ax.legend(ncol=4, fontsize=8)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def grafik_emotion_pie(file_json):
    JSON_PATH = f"emo_data/{file_json}"
    classes = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
    BAD = {"No face detected"}

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    # Filter: emosi valid, punya elapsed_time, bukan BAD
    rows = [
        r for r in rows
        if r.get("emosi") in classes
        and r.get("elapsed_time")
        and r.get("emosi") not in BAD
    ]
    if not rows:
        return ""

    # Hitung frekuensi per emosi
    counts = {c: 0 for c in classes}
    for r in rows:
        counts[r["emosi"]] += 1

    # Buang kelas nol kosong
    labels = [k.capitalize() for k, v in counts.items() if v > 0]
    sizes  = [v for v in counts.values() if v > 0]
    if not sizes:
        return ""

    total = sum(sizes)
    def autopct_fmt(pct):
        n = int(round(pct * total / 100.0))
        return f"{pct:.1f}%\n({n})"

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(
        sizes,
        labels=labels,
        autopct=autopct_fmt,
        startangle=90,
        wedgeprops={"edgecolor": "white"},
        textprops={"fontsize": 9}
    )
    ax.axis("equal")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")



def grafik_emotion_bars(file_json):
    JSON_PATH = f"emo_data/{file_json}"
    classes = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
    BAD = {"Bad Processed"}

    color_map = {
        "angry": "#E74C3C",
        "disgust": "#27AE60",
        "fear": "#8E44AD",
        "happy": "#F1C40F",
        "neutral": "#95A5A6",
        "sad": "#3498DB",
        "surprise": "#E67E22"
    }

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    # Filter hanya kelas yang relevan dan ada elapsed_time
    rows = [
        r for r in rows
        if r.get("emosi") in classes
        and r.get("elapsed_time")
        and r.get("emosi") not in BAD
    ]
    if not rows:
        return ""

    # Ubah elapsed_time ke detik
    def hms_to_seconds(s):
        h, m, sec = map(int, s.split(":"))
        return h * 3600 + m * 60 + sec

    for r in rows:
        try:
            r["sec"] = hms_to_seconds(r["elapsed_time"])
        except Exception:
            r["sec"] = None

    rows = [r for r in rows if r["sec"] is not None]
    if not rows:
        return ""

    # Kumpulkan waktu per emosi yang muncul
    x_by_class = {c: sorted([r["sec"] for r in rows if r["emosi"] == c]) for c in classes}
    x_by_class = {k: v for k, v in x_by_class.items() if v}
    if not x_by_class:
        return ""

    def format_hhmmss(sec):
        h, rem = divmod(int(sec), 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    n = len(x_by_class)
    fig, axes = plt.subplots(n, 1, figsize=(12, 2.6 * n), sharex=True)
    if n == 1:
        axes = [axes]

    # Domain X global + xticks merata
    all_secs = [s for lst in x_by_class.values() for s in lst]
    xmin, xmax = min(all_secs), max(all_secs)
    span = max(1.0, xmax - xmin)
    left_margin, right_margin = 1.0, 1.0
    max_labels = 10
    xticks = (np.linspace(xmin, xmax, num=min(max_labels, max(2, len(all_secs))))
              .tolist() if xmax > xmin else [xmin])

    for ax, (emo, xs) in zip(axes, x_by_class.items()):
        # Bar horizontal tipis di level Y = nama emosi (tak ada anotasi per-bar)
        ax.barh([emo]*len(xs), [0.5]*len(xs), left=xs, height=0.5,
                color=color_map.get(emo, "#7F8C8D"))

        # Y = nama emosi
        ax.set_yticks([emo])
        ax.set_yticklabels([emo.capitalize()])

        # Tampilkan label X (HH:MM:SS) DI SETIAP SUBPLOT
        ax.set_xticks(xticks)
        ax.set_xticklabels([format_hhmmss(s) for s in xticks], rotation=0, ha="right")
        ax.tick_params(axis="x", which="both", labelbottom=True)  # penting

        # Batas X + grid
        ax.set_xlim(xmin - left_margin, xmax + right_margin)
        ax.grid(axis="x", linestyle="--", alpha=0.3)

    #fig.supxlabel("Waktu (HH:MM:SS) dari awal", y=0.04)
    fig.tight_layout(rect=[0, 0.06, 1, 1])

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def grafik_emotion_lines(file_json):
    JSON_PATH = f"emo_data/{file_json}"

    # Emotion mapping to numbers, including "No face detected" mapped to 0
    emo_map = {
        "angry": 1,
        "fear": 2,
        "disgust": 3,
        "sad": 4,
        "neutral": 5,
        "happy": 6,
        "surprise": 7,
        "No face detected": 0  # This will be mapped to 0, but labeled as "distracted"
    }

    # Load the JSON data
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    # Convert elapsed_time "00:00:01" to seconds (int)
    def hms_to_seconds(s):
        h, m, sec = map(int, s.split(":"))
        return h * 3600 + m * 60 + sec

    # Replace the emotion string with its numerical equivalent
    data = []
    for r in rows:
        emotion = r.get("emosi")
        etime = r.get("elapsed_time")
        if emotion in emo_map and etime:
            try:
                seconds = hms_to_seconds(etime)
            except Exception:
                continue
            data.append((seconds, emo_map[emotion]))

    if not data:
        return ""

    # Sort the data by elapsed_time seconds
    data.sort(key=lambda x: x[0])

    # Use elapsed_time (in seconds) directly
    rel_times = [t for t, _ in data]
    ys = [y for _, y in data]

    # Format time in HH:MM:SS
    def format_hhmmss(sec):
        h, rem = divmod(int(sec), 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(rel_times, ys, marker='o', color="red", markersize=5, label="Emotion")

    # Set Y-axis ticks with emotion names
    y_labels = [key.capitalize() if key != "No face detected" else "No Face" for key in emo_map.keys()]
    ax.set_yticks(list(emo_map.values()))
    ax.set_yticklabels(y_labels)

    # Limit the number of X-axis labels
    max_labels = 10
    if len(rel_times) > max_labels:
        chosen_idx = np.linspace(0, len(rel_times) - 1, max_labels, dtype=int)
        xticks = [rel_times[i] for i in chosen_idx]
    else:
        xticks = rel_times

    # Set X-axis ticks and label format
    ax.set_xticks(xticks)
    ax.set_xticklabels([format_hhmmss(s) for s in xticks], rotation=45)

    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.tight_layout()

    # Save the plot to a buffer and encode it as base64
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")



######################### Dominan Engagement ######################
def kesimpulan(file_json):
    JSON_PATH = f"emo_data/{file_json}"
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)
    engagement_counts = Counter(row['engagement'] for row in rows)
    total = sum(engagement_counts.values())
    if engagement_counts:
        engagement_terbanyak = engagement_counts.most_common(1)[0][0]
    else:
        engagement_terbanyak = None
    # Persentase dibulatkan 2 angka di belakang koma
    engagement_persen = {kategori: round((jumlah / total * 100), 2) for kategori, jumlah in engagement_counts.items()}
    return engagement_terbanyak, engagement_persen


########################### GEMINI #############################
gem_api ='AIzaSyCwnXTOjCHT3rttgv7jI-UoYr2J5GCLcJg'
#gem_api ='AIzaSyCXUVou2QMVr6gFSaAfCElnYRfDr-PTmqA'
#gem_api ='AIzaSyCBIK0EcJl5D-LX9bddqWb7dQMbMOXRjLM'
#gem_api ='AIzaSyCIv9wUEUszC7Py_lo_XEMMrz5vWP59IMY'

def get_gemini_response(data, prompt):
    data_str = json.dumps(data, indent=4)    
    full_prompt = f"{prompt[0]}\n\nData Siswa:\n{data_str}"    
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content([full_prompt])
    return response.text

def run_task(data, prompt):
    response=get_gemini_response(data, prompt)
    return response

client = genai.configure(api_key=gem_api)

prompt1 = [
    """
    Tugas:
    berikan analisis secara singkat dari data yang diberikan tentang engagement siswa pada saat pembelajaran daring, lalu sebutkan emosi dominannnya. 
    cukup jelaskan dalam 1 paragraf singkat saja. Jawaban jangan mengandung format-format bold atau miring    
    """
]

prompt2 = [
    """
    Tugas:
    berikan rekomendasi evaluasi tentang bagian (menit dan detik dari elapsed_time) materi mana yang harus diperbaiki oleh pengajar berdasarkan tingkat engagement siswa tersebut. 
    cukup jelaskan dalam 1 paragraf singkat saja. Jawaban jangan mengandung format-format bold atau miring    
    """
]

prompt_fix = [
    """
    Tugas:
    1. Berikan analisis singkat tentang engagement siswa dan emosi dominan.
    2. Berikan rekomendasi evaluasi menit/detik materi yang perlu diperbaiki.
    Jawab dalam format JSON:
    {
    "analisis": "...",
    "rekomendasi": "..."
    }
    Jangan gunakan bold/miring.
    Jawablah dengan format JSON valid tanpa teks tambahan apa pun.
    Jangan gunakan ``` dalam jawaban.
    Hanya berisi dua key: analisis dan rekomendasi.
    """
]

def analisis_gemini_ori(file_json):
    JSON_PATH = f"emo_data/{file_json}"
    with open(JSON_PATH, 'r') as file:
        data = json.load(file)
    x = run_task(data, prompt1)
    y = run_task(data, prompt2)
    return x, y


def analisis_gemini(file_json):
    JSON_PATH = f"emo_data/{file_json}"
    with open(JSON_PATH, 'r') as file:
        data = json.load(file)

    response = run_task(data, prompt_fix)
    print(response)
    parsed = json.loads(response)

    x = parsed["analisis"]
    y = parsed["rekomendasi"]
    return x, y