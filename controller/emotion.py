from function.koneksi import get_db_connection
import io, json, base64
from collections import Counter, defaultdict
from datetime import datetime
from flask import render_template
import matplotlib
matplotlib.use("Agg")  # backend non-GUI untuk server
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
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
    JSON_PATH = f"emo_data/{file_json}"  # ganti jika perlu
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
        return ""  # atau None

    # Urutkan
    data.sort(key=lambda x: x[0])
    times = [t for t, _ in data]
    ys    = [y for _, y in data]

    # Plot
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.step(times, ys, where="post")
    ax.scatter(times, ys, s=12)
    ax.set_yticks([0, 1], ["tidak fokus", "fokus"])
    ax.set_xlabel("Timestamp")
    #ax.set_ylabel("Fokus")
    #ax.set_title("Grafik Kefokusan")
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

    # Return base64 (PNG)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def grafik_emotion_(file_json):
    JSON_PATH = f"emo_data/{file_json}"
    
    classes = ["angry","disgust","fear","happy","neutral","sad","surprise"]

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        rows = json.load(f)

    df = pd.DataFrame(rows)
    if df.empty or "timestamp" not in df or "emosi" not in df:
        return ""  # atau None

    # keep only target classes & timestamp valid
    df = df[df["emosi"].isin(classes) & df["timestamp"].notna()].copy()
    if df.empty:
        return ""

    # convert timestamp -> detik dari awal (untuk sumbu X numerik)
    df["t"] = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df = df[df["t"].notna()]
    if df.empty:
        return ""
    t0 = df["t"].min()
    df["sec"] = (df["t"] - t0).dt.total_seconds()

    # KDE butuh >=2 titik per kelas
    valid_counts = df.groupby("emosi")["sec"].count()
    use_classes = [c for c in classes if valid_counts.get(c, 0) >= 2]
    if not use_classes:
        return ""

    # --- plot ridgeline ---
    sns.set_theme(style="white")
    g = sns.FacetGrid(
        df[df["emosi"].isin(use_classes)],
        row="emosi", hue="emosi",
        row_order=use_classes,  # urut sesuai daftar yang kamu kasih
        sharex=True, sharey=False,
        height=1.1, aspect=6
    )
    g.map(sns.kdeplot, "sec", fill=True, alpha=.7, bw_adjust=.9, clip_on=False)

    # bersihkan axis agar gaya "ridgeline"
    for ax in g.axes.flatten():
        ax.set_yticks([])
        ax.set_ylabel("")
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)

    g.set_titles(row_template="{row_name}")
    g.set_xlabels("Detik dari awal")
    g.figure.subplots_adjust(hspace=-0.35)

    # --- Return base64 (PNG) ---
    buf = io.BytesIO()
    g.figure.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(g.figure)
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
    ax.set_title("Distribusi Emosi")
    ax.legend(ncol=4, fontsize=8)
    fig.tight_layout()

    # --- return base64 PNG ---
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")

    
