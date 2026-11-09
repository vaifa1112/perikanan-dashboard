import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
import urllib.parse

@st.cache_resource
def get_engine():
    """Membuat engine SQLAlchemy dengan caching"""
    try:
        # Ambil dari secrets Streamlit
        config = st.secrets["postgresql"]
        
        password = urllib.parse.quote_plus(config["password"])
        DATABASE_URL = f"postgresql://{config['user']}:{password}@{config['host']}:{config['port']}/{config['database']}"
        
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        st.error(f"❌ Gagal koneksi database: {e}")
        return None

@st.cache_data(ttl=300)
def load_perikanan_data():
    """Load data dari database dengan caching"""
    engine = get_engine()
    if engine is None:
        return None
    
    query = """
        SELECT 
            dk.nama_kabupaten_kota AS kabupaten,
            dj.kelompok_ikan AS kelompok,
            dj.nama_ikan AS jenis_ikan,
            du.jenis_usaha AS usaha,
            f.tahun,
            f.produksi_ton AS volume,
            f.nilai_produksi_ribu_rupiah AS nilai_ribu
        FROM fact_produksi_perikanan f
        JOIN dim_kab_kota dk ON f.id_kab_kota = dk.id_kab_kota
        JOIN dim_jenis_ikan dj ON f.id_jenis_ikan = dj.id_jenis_ikan
        JOIN dim_jenis_usaha du ON f.id_jenis_usaha = du.id_jenis_usaha
        WHERE f.tahun BETWEEN 2022 AND 2024
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
        st.error(f"❌ Gagal load data: {e}")
        return None