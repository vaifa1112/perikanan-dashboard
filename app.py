import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="Dashboard Perikanan Tangkap Jawa Barat",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Koneksi Database (Mengambil dari secrets)
@st.cache_resource
def get_engine():
    try:
        db_url = st.secrets["DATABASE_URL"]
        # connect_args memastikan koneksi SSL aktif untuk Neon
        engine = create_engine(db_url, connect_args={"sslmode": "require"})
        return engine
    except Exception as e:
        st.error(f"❌ Gagal koneksi database: {e}")
        return None

# 3. Load Data
@st.cache_data(ttl=300)
def load_data():
    engine = get_engine()
    if engine is None:
        return None
    
    # CATATAN: Jika error menyebut kolom 'jenis_ikan' tidak ada, 
    # ganti 'dj.jenis_ikan' menjadi 'dj.nama' atau 'dj.nama_ikan' sesuai struktur tabelmu.
    query = """
        SELECT 
            dk.kab_kota AS kabupaten,
            dj.kelompok_ikan AS kelompok,
            dj.jenis_ikan AS jenis_ikan,
            du.jenis_usaha AS usaha,
            f.tahun,
            f.produksi_ton AS volume,
            f.nilai_produksi_ribu_rupiah AS nilai_ribu
        FROM fact_produksi_perikanan f
        JOIN dim_kab_kota dk ON f.id_kab_kota = dk.id_kab_kota
        JOIN dim_jenis_ikan dj ON f.id_jenis_ikan = dj.id_jenis_ikan
        JOIN dim_jenis_usaha du ON f.id_jenis_usaha = du.id_jenis_usaha
    """
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        
        # Kalkulasi tambahan
        df['nilai_rp'] = df['nilai_ribu'] * 1000
        df['nilai_juta'] = df['nilai_rp'] / 1_000_000
        df['nilai_triliun'] = df['nilai_rp'] / 1_000_000_000_000
        df['harga_per_kg'] = df.apply(
            lambda r: (r['nilai_rp'] / (r['volume'] * 1000)) if r['volume'] > 0 else 0, 
            axis=1
        )
        return df
    except Exception as e:
        st.error(f"❌ Query gagal: {e}")
        st.info("💡 Tips: Jika error menyebut kolom tidak ditemukan, buka DBeaver/Neon dan cek nama kolom yang benar di tabel `dim_jenis_ikan` (mungkin 'nama' atau 'nama_ikan'), lalu ubah di query atas.")
        return None

df_raw = load_data()
if df_raw is None:
    st.stop()

# 4. Header
st.title("🐟 Dashboard Potensi Perikanan Tangkap Jawa Barat")
st.markdown("**Periode 2022–2024** | Data Real-time dari Cloud Database")
st.markdown("---")

# 5. Sidebar Filter
with st.sidebar:
    st.header("🔍 Filter Data")
    
    years = sorted(df_raw['tahun'].unique())
    selected_years = st.multiselect("Tahun", years, default=years)
    
    usaha_list = ["Semua"] + sorted(df_raw['usaha'].unique())
    selected_usaha = st.selectbox("Jenis Usaha", usaha_list)
    
    kab_list = sorted(df_raw['kabupaten'].unique())
    selected_kab = st.multiselect("Kabupaten / Kota", kab_list, default=kab_list[:5])
    
    ikan_list = sorted(df_raw['jenis_ikan'].unique())
    selected_ikan = st.multiselect("Jenis Ikan", ikan_list)

# 6. Filtering Data
df_filtered = df_raw.copy()
if selected_years:
    df_filtered = df_filtered[df_filtered['tahun'].isin(selected_years)]
if selected_usaha != "Semua":
    df_filtered = df_filtered[df_filtered['usaha'] == selected_usaha]
if selected_kab:
    df_filtered = df_filtered[df_filtered['kabupaten'].isin(selected_kab)]
if selected_ikan:
    df_filtered = df_filtered[df_filtered['jenis_ikan'].isin(selected_ikan)]

if df_filtered.empty:
    st.warning("⚠️ Tidak ada data yang sesuai dengan filter.")
    st.stop()

# 7. KPI Metrics
total_volume = df_filtered['volume'].sum()
total_nilai_triliun = df_filtered['nilai_rp'].sum() / 1e12
harga_avg = (df_filtered['nilai_rp'].sum() / (total_volume * 1000)) if total_volume > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("📦 Total Volume", f"{total_volume:,.0f} Ton")
col2.metric("💰 Total Nilai", f"Rp {total_nilai_triliun:,.2f} T")
col3.metric("⚖️ Harga Rata-rata", f"Rp {harga_avg:,.0f}/kg")
col4.metric("📈 Total Data", f"{len(df_filtered):,} Record")
st.markdown("---")

# 8. Visualisasi
tab1, tab2, tab3 = st.tabs(["📈 Tren & Wilayah", "🐠 Komoditas & Usaha", "📋 Data Rinci"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Tren Tahunan Volume vs Nilai Ekonomi")
        df_trend = df_filtered.groupby('tahun').agg({'volume': 'sum', 'nilai_triliun': 'sum'}).reset_index()
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(x=df_trend['tahun'], y=df_trend['volume'], name='Volume (Ton)', marker_color='#1f77b4'))
        fig_trend.add_trace(go.Scatter(x=df_trend['tahun'], y=df_trend['nilai_triliun'], name='Nilai (Triliun Rp)', marker_color='#ff7f0e', yaxis='y2'))
        fig_trend.update_layout(xaxis=dict(title='Tahun'), yaxis=dict(title='Volume (Ton)'), yaxis2=dict(title='Nilai (Triliun Rp)', side='right', overlaying='y'))
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with col_b:
        st.subheader("Top 10 Kabupaten/Kota (Volume)")
        df_kab = df_filtered.groupby('kabupaten')['volume'].sum().nlargest(10).reset_index()
        fig_kab = px.bar(df_kab, y='kabupaten', x='volume', orientation='h', color='volume', color_continuous_scale='Blues')
        fig_kab.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_kab, use_container_width=True)

with tab2:
    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Top 10 Jenis Ikan (Nilai Tertinggi)")
        df_ikan = df_filtered.groupby('jenis_ikan')['nilai_juta'].sum().nlargest(10).reset_index()
        fig_ikan = px.bar(df_ikan, y='jenis_ikan', x='nilai_juta', orientation='h', color='nilai_juta', color_continuous_scale='Viridis')
        fig_ikan.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_ikan, use_container_width=True)
        
    with col_d:
        st.subheader("Proporsi Volume menurut Jenis Usaha")
        df_u = df_filtered.groupby('usaha')['volume'].sum().reset_index()
        fig_pie = px.pie(df_u, values='volume', names='usaha', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.subheader("Tabel Data Lengkap")
    st.dataframe(
        df_filtered[['tahun', 'kabupaten', 'kelompok', 'jenis_ikan', 'usaha', 'volume', 'nilai_juta', 'harga_per_kg']],
        column_config={
            "tahun": "Tahun",
            "kabupaten": "Kabupaten/Kota",
            "kelompok": "Kelompok",
            "jenis_ikan": "Jenis Ikan",
            "usaha": "Jenis Usaha",
            "volume": st.column_config.NumberColumn("Volume (Ton)", format="%.2f"),
            "nilai_juta": st.column_config.NumberColumn("Nilai (Juta Rp)", format="%.2f"),
            "harga_per_kg": st.column_config.NumberColumn("Harga (Rp/kg)", format="%.0f"),
        },
        use_container_width=True,
        hide_index=True
    )
