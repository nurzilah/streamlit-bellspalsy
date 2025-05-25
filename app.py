import streamlit as st
import pandas as pd
from pymongo import MongoClient
import matplotlib.pyplot as plt

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

# Parsing subscribers jika ada
def parse_subscribers(sub_str):
    if not sub_str:
        return 0
    sub_str = str(sub_str).lower().replace('subscribers', '').strip()
    if 'k' in sub_str:
        return int(float(sub_str.replace('k', '')) * 1e3)
    elif 'm' in sub_str:
        return int(float(sub_str.replace('m', '')) * 1e6)
    try:
        return int(float(sub_str))
    except:
        return 0

if 'subscribers' in df.columns:
    df['subscribers_num'] = df['subscribers'].apply(parse_subscribers)
else:
    df['subscribers_num'] = 0

# Parsing tanggal
def parse_date(date_str):
    try:
        return pd.to_datetime(date_str)
    except:
        return pd.NaT

df['published_dt'] = df['published'].apply(parse_date)

# Visualisasi 1: Top 5 Video Views
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

# Visualisasi 2: Top 10 Channel berdasarkan jumlah video
st.subheader("Top 10 Channel yang Paling Sering Membahas Bells Palsy")
top_channels = df.groupby('channel').size().reset_index(name='jumlah_video').sort_values(by='jumlah_video', ascending=False).head(10)

fig2, ax2 = plt.subplots(figsize=(10, 5))
ax2.barh(top_channels['channel'], top_channels['jumlah_video'], color='#4B7BF5')
ax2.invert_yaxis()
ax2.set_xlabel('Jumlah Video')
ax2.set_ylabel('Channel')
ax2.set_title('Top 10 Channel berdasarkan Jumlah Video')
for i, v in enumerate(top_channels['jumlah_video']):
    ax2.text(v + max(top_channels['jumlah_video']) * 0.01, i, f"{v}", va='center')
st.pyplot(fig2)

# Visualisasi 3: Top 10 Channel berdasarkan subscriber
st.subheader("Top 10 Channel berdasarkan Jumlah Subscriber")
top_channels_subs = df.groupby('channel').agg({'subscribers_num': 'max'}).reset_index()
top_channels_subs = top_channels_subs.sort_values(by='subscribers_num', ascending=False).head(10)

fig3, ax3 = plt.subplots(figsize=(10, 5))
ax3.barh(top_channels_subs['channel'], top_channels_subs['subscribers_num'], color='#2CA02C')
ax3.invert_yaxis()
ax3.set_xlabel('Jumlah Subscriber')
ax3.set_ylabel('Channel')
ax3.set_title('Top 10 Channel berdasarkan Subscriber')
for i, v in enumerate(top_channels_subs['subscribers_num']):
    ax3.text(v + max(top_channels_subs['subscribers_num']) * 0.01, i, f"{v:,}", va='center')
st.pyplot(fig3)
