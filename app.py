import streamlit as st
import pandas as pd
from utils.database import load_perikanan_data
from utils import visualizations as viz

# Konfigurasi Halaman
st.set_page_config(
    page_title="Dashboard Perikanan Tangkap Jawa Barat",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🐟 Dashboard Potensi Perikanan Tangkap Jawa Barat")
st.markdown("**Periode 2022–2024** | Interaktif & Real-time")
st.markdown("---")

# Load Data
@st.cache_data
def get_filtered_data(df, years, kab, ikan, usaha):
    """Filter data dengan caching"""
    df_filtered = df.copy()
    if years:
        df_filtered = df_filtered[df_filtered['tahun'].isin(years)]
    if kab:
        df_filtered = df_filtered[df_filtered['kabupaten'].isin(kab)]
    if ikan:
        df_filtered = df_filtered[df_filtered['jenis_ikan'].isin(ikan)]
    if usaha != "Semua":
        df_filtered = df_filtered[df_filtered['usaha'] == usaha]
    return df_filtered

# Main App
def main():
    # Load data
    df_raw = load_perikanan_data()
    if df_raw is None:
        st.warning("⚠️ Data tidak tersedia. Periksa koneksi database.")
        return
    
    # Sidebar Filter
    with st.sidebar:
        st.header("🔍 Filter Data")
        st.markdown("---")
        
        # Filter Tahun
        years = sorted(df_raw['tahun'].unique())
        selected_years = st.multiselect("Tahun", years, default=years)
        
        # Filter Jenis Usaha
        usaha_list = ["Semua"] + sorted(df_raw['usaha'].unique())
        selected_usaha = st.selectbox("Jenis Usaha", usaha_list)
        
        # Filter Kabupaten
        kab_list = sorted(df_raw['kabupaten'].unique())
        selected_kab = st.multiselect("Kabupaten / Kota", kab_list, default=kab_list[:5])
        
        # Filter Jenis Ikan
        ikan_list = sorted(df_raw['jenis_ikan'].unique())
        selected_ikan = st.multiselect("Jenis Ikan", ikan_list)
        
        # Reset Filter Button
        if st.button("🔄 Reset Filter"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        
        # Export Data
        st.subheader(" Ekspor Data")
        df_temp = get_filtered_data(df_raw, selected_years, selected_kab, selected_ikan, selected_usaha)
        csv = df_temp.to_csv(index=False)
        st.download_button(
            label="Unduh CSV",
            data=csv,
            file_name="perikanan_jabar_2022_2024.csv",
            mime="text/csv"
        )
    
    # Filter Data
    df_filtered = get_filtered_data(df_raw, selected_years, selected_kab, selected_ikan, selected_usaha)
    
    if df_filtered.empty:
        st.warning("⚠️ Tidak ada data yang sesuai dengan filter.")
        return
    
    # KPI Metrics
    total_volume = df_filtered['volume'].sum()
    total_nilai_triliun = df_filtered['nilai_rp'].sum() / 1e12
    harga_avg = (df_filtered['nilai_rp'].sum() / (total_volume * 1000)) if total_volume > 0 else 0
    total_records = len(df_filtered)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(" Total Volume", f"{total_volume:,.0f} Ton")
    with col2:
        st.metric("💰 Total Nilai", f"Rp {total_nilai_triliun:,.2f} T")
    with col3:
        st.metric("️ Harga Rata-rata", f"Rp {harga_avg:,.0f}/kg")
    with col4:
        st.metric("📈 Total Data", f"{total_records:,} Record")
    
    st.markdown("---")
    
    # Visualisasi
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Tren & Wilayah", "🐠 Komoditas", "📊 Analisis", "📋 Data Rinci"])
    
    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            fig_trend = viz.create_trend_chart(df_filtered)
            st.plotly_chart(fig_trend, use_container_width=True)
        
        with col_b:
            fig_kab = viz.create_top_kabupaten_chart(df_filtered)
            st.plotly_chart(fig_kab, use_container_width=True)
    
    with tab2:
        col_c, col_d = st.columns(2)
        with col_c:
            fig_ikan = viz.create_top_ikan_chart(df_filtered)
            st.plotly_chart(fig_ikan, use_container_width=True)
        
        with col_d:
            fig_pie = viz.create_pie_usaha_chart(df_filtered)
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with tab3:
        fig_scatter = viz.create_scatter_harga_volume(df_filtered)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.markdown("### 📊 Distribusi Harga per Kelompok Ikan")
        df_box = df_filtered.groupby(['kelompok', 'jenis_ikan'])['harga_per_kg'].mean().reset_index()
        st.dataframe(df_box, use_container_width=True)
    
    with tab4:
        st.subheader("Tabel Data Lengkap")
        
        # Column configuration
        column_config = {
            "tahun": st.column_config.NumberColumn("Tahun", format="%d"),
            "kabupaten": "Kabupaten/Kota",
            "kelompok": "Kelompok",
            "jenis_ikan": "Jenis Ikan",
            "usaha": "Jenis Usaha",
            "volume": st.column_config.NumberColumn("Volume (Ton)", format="%.2f"),
            "nilai_juta": st.column_config.NumberColumn("Nilai (Juta Rp)", format="%.2f"),
            "harga_per_kg": st.column_config.NumberColumn("Harga (Rp/kg)", format="%.0f"),
        }
        
        st.dataframe(
            df_filtered[['tahun', 'kabupaten', 'kelompok', 'jenis_ikan', 'usaha', 'volume', 'nilai_juta', 'harga_per_kg']],
            column_config=column_config,
            use_container_width=True,
            hide_index=True
        )
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        <small>Dashboard Perikanan Tangkap Jawa Barat 2022–2024 | Data: Dinas Kelautan dan Perikanan Jabar</small>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()