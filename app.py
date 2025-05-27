import streamlit as st
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt
from collections import Counter
import re

# Koneksi MongoDB
client = MongoClient(st.secrets["mongo_uri"])
db = client['big_data']
collection = db['crawling_yt_revisi1']

st.set_page_config(layout="wide", page_title="YouTube Data Visualization")
st.title("Visualisasi Data Crawling YouTube dari MongoDB")
@st.cache_data(ttl=600)
def load_data():
    data = list(collection.find())
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    if '_id' in df.columns:
        df.drop(columns=['_id'], inplace=True)
    return df

df = load_data()

if df.empty:
    st.warning("Belum ada data di database MongoDB.")
    st.stop()

required_cols = ['views', 'published', 'channel', 'title', 'url']
for col in required_cols:
    if col not in df.columns:
        st.error(f"Kolom '{col}' tidak ditemukan di data.")
        st.stop()

# Fungsi parsing views
def parse_views(view_str):
    if not view_str:
        return 0
    view_str = str(view_str).replace(',', '').replace(' views', '').strip()
    if 'K' in view_str:
        return int(float(view_str.replace('K', '')) * 1e3)
    elif 'M' in view_str:
        return int(float(view_str.replace('M', '')) * 1e6)
    try:
        return int(float(view_str))
    except:
        return 0

df['views_num'] = df['views'].apply(parse_views)

# Parsing tanggal
def parse_date(date_str):
    try:
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

df['published_dt'] = df['published'].apply(parse_date)

# Parsing komentar
if 'comments' in df.columns:
    df['comments_num'] = pd.to_numeric(df['comments'], errors='coerce').fillna(0).astype(int)
else:
    df['comments_num'] = 0

# --- Visualisasi 1: Top 5 Video dengan Viewers Tertinggi ---
st.subheader("Top 5 Video dengan Viewers Tertinggi")
top5 = df.sort_values(by='views_num', ascending=False).head(5)
for idx, row in top5.iterrows():
    st.markdown(f"- [{row['title'][:60]}...]({row['url']})")

fig1, ax1 = plt.subplots(figsize=(10, 5))
ax1.barh(top5['title'].str[:50] + "...", top5['views_num'], color='#FF4B4B')
ax1.invert_yaxis()
ax1.set_xlabel('Jumlah Views')
ax1.set_ylabel('Judul Video')
ax1.set_title('5 Video dengan Viewers Terbanyak')
ax1.grid(axis='x', linestyle='--', alpha=0.7)
for i, v in enumerate(top5['views_num']):
    ax1.text(v + max(top5['views_num']) * 0.01, i, f"{v:,}", va='center')
st.pyplot(fig1)

# --- Visualisasi 2: Top 10 Channel berdasarkan jumlah video ---
st.subheader("Top 10 Channel yang Paling Sering Membahas Bells Palsy")

# Hilangkan channel yang kosong (NaN atau string kosong)
df_clean = df[df['channel'].notna() & (df['channel'].str.strip() != '')]

top_channels = (
    df_clean.groupby('channel')
    .size()
    .reset_index(name='jumlah_video')
    .sort_values(by='jumlah_video', ascending=False)
    .head(10)
)

fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.barh(top_channels['channel'], top_channels['jumlah_video'], color='#4B7BF5')
ax2.invert_yaxis()
ax2.set_xlabel('Jumlah Video')
ax2.set_ylabel('Channel')
ax2.set_title('Top 10 Channel berdasarkan Jumlah Video')
for i, v in enumerate(top_channels['jumlah_video']):
    ax2.text(v + max(top_channels['jumlah_video']) * 0.01, i, f"{v}", va='center')
st.pyplot(fig2)


# --- Visualisasi 3: Top 10 Channel berdasarkan Jumlah Komentar ---
st.subheader("Top 10 Channel berdasarkan Aktivitas Komentar Pengguna")
top_channels_comments = df.groupby('channel').agg({'comments_num': 'sum'}).reset_index()
top_channels_comments = top_channels_comments.sort_values(by='comments_num', ascending=False).head(10)

fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.barh(top_channels_comments['channel'], top_channels_comments['comments_num'], color='#FFA500')
ax3.invert_yaxis()
ax3.set_xlabel('Jumlah Komentar')
ax3.set_ylabel('Channel')
ax3.set_title('Top 10 Channel dengan Komentar Terbanyak')
for i, v in enumerate(top_channels_comments['comments_num']):
    ax3.text(v + max(top_channels_comments['comments_num']) * 0.01, i, f"{v:,}", va='center')
st.pyplot(fig3)

# --- Visualisasi 4: Top Kata Kunci yang Sering Muncul di Judul Video ---
st.subheader("Top Kata Kunci yang Sering Muncul di Judul Video")

# Ambil semua judul, ubah jadi lowercase dan tokenize kata (hilangkan simbol non alphabet)
all_titles = df['title'].dropna().str.lower().str.cat(sep=' ')
words = re.findall(r'\b[a-zA-Z]{2,}\b', all_titles)  # hanya kata dengan 2+ huruf

# Hitung frekuensi kata
word_freq = Counter(words)

# DataFrame 15 kata terpopuler
top_keywords_df = pd.DataFrame(word_freq.most_common(15), columns=['Kata Kunci', 'Jumlah Kemunculan'])

# Tampilkan tabel
st.dataframe(top_keywords_df)

# Visualisasi bar chart
fig_kw, ax_kw = plt.subplots(figsize=(10, 5))
ax_kw.barh(top_keywords_df['Kata Kunci'][::-1], top_keywords_df['Jumlah Kemunculan'][::-1], color='#FFA07A')
ax_kw.set_xlabel("Jumlah Kemunculan")
ax_kw.set_title("Top 15 Kata Kunci yang Paling Sering Muncul di Judul Video")
st.pyplot(fig_kw)
