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

    focus_map = {"fokus": 1, "tidak fokus": 0}

    data = []
    for r in rows:
        fval = r.get("fokus")
        ts = r.get("timestamp")
        if fval in focus_map and ts:
            try:
                t = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue
            data.append((t, focus_map[fval]))

    if not data:
        return ""

    # Urutkan
    data.sort(key=lambda x: x[0])

    # Waktu relatif dari awal +1 detik agar mulai 00:00:01
    start_time = data[0][0] - timedelta(seconds=1)
    rel_times = [(t - start_time).total_seconds() for t, _ in data]

    # Fungsi format jam:menit:detik
    def format_hhmmss(sec):
        h, rem = divmod(int(sec), 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    ys = [y for _, y in data]

    # Plot
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.step(rel_times, ys, where="post")
    ax.scatter(rel_times, ys, s=12)
    ax.set_yticks([0, 1], ["tidak fokus", "fokus"])

    # Batasi jumlah label sumbu-x maksimal 10
    max_labels = 10
    if len(rel_times) > max_labels:
        chosen_idx = np.linspace(0, len(rel_times) - 1, max_labels, dtype=int)
        xticks = [rel_times[i] for i in chosen_idx]
    else:
        xticks = rel_times

    ax.set_xticks(xticks)
    ax.set_xticklabels([format_hhmmss(s) for s in xticks], rotation=45)

    #ax.set_xlabel("Waktu")
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
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    def parse_ts(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    BAD = {"Bad Processed"}
    rows = [r for r in rows if r.get("emosi") in classes and r.get("timestamp") and r.get("emosi") not in BAD]

    if not rows:
        return ""

    # konversi timestamp -> detik dari awal
    times = [parse_ts(r["timestamp"]) for r in rows]
    rows = [r for r, t in zip(rows, times) if t is not None]
    times = [t for t in times if t is not None]
    if not times:
        return ""

    t0 = min(times)
    for r, t in zip(rows, times):
        r["sec"] = (t - t0).total_seconds()

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
            # kalau hanya 1 titik, KDE tidak bisa; tampilkan titiknya saja
            ax.scatter(xs, [0], s=22, label=f"{cls} (1)")

    #ax.set_xlabel("Detik dari awal")
    #ax.set_ylabel("Kepadatan")
    #ax.set_title("Distribusi Emosi")
    ax.legend(ncol=4, fontsize=8)
    fig.tight_layout()

    # --- return base64 PNG ---
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")

def grafik_emotion_pie(file_json):
    JSON_PATH = f"emo_data/{file_json}"
    classes = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
    BAD = {"Bad Processed"}

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    # Filter: emosi valid, ada timestamp, bukan BAD, dan hanya fokus
    rows = [
        r for r in rows
        if r.get("emosi") in classes
        and r.get("timestamp")
        and r.get("emosi") not in BAD
        and r.get("fokus") == "fokus"
    ]
    if not rows:
        return ""

    # Hitung frekuensi per emosi
    counts = {c: 0 for c in classes}
    for r in rows:
        counts[r["emosi"]] += 1

    # Buang kelas nol agar tidak ada slice kosong
    labels = [k.capitalize() for k, v in counts.items() if v > 0]
    sizes  = [v for v in counts.values() if v > 0]
    if not sizes:
        return ""

    total = sum(sizes)

    # Tampilkan persen + jumlah
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
    ax.axis("equal")  # pie jadi lingkaran

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

    rows = [
        r for r in rows
        if r.get("emosi") in classes
        and r.get("timestamp")
        and r.get("emosi") not in BAD
    ]
    if not rows:
        return ""

    def parse_ts(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except:
            return None

    times = [parse_ts(r["timestamp"]) for r in rows]
    rows  = [r for r, t in zip(rows, times) if t is not None]
    times = [t for t in times if t is not None]
    if not times:
        return ""

    # Relatif dari awal +1 detik (mulai 00:00:01)
    t0 = min(times)
    start_time = t0 - timedelta(seconds=1)
    for r, t in zip(rows, times):
        r["sec"] = (t - start_time).total_seconds()

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

        #ax.set_title(f"{emo.capitalize()} (n={len(xs)})", fontsize=11, pad=6)

    #fig.supxlabel("Waktu (HH:MM:SS) dari awal", y=0.04)
    fig.tight_layout(rect=[0, 0.06, 1, 1])

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
