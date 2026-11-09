import streamlit as st
from utils.database import get_engine
from sqlalchemy import text

st.title(" Database Debug Tool")

if st.button("Test Connection"):
    engine = get_engine()
    if engine:
        try:
            with engine.connect() as conn:
                st.success("✅ Koneksi berhasil!")
                
                # Cek tabel
                tables = ['fact_produksi_perikanan', 'dim_kab_kota', 'dim_jenis_ikan', 'dim_jenis_usaha']
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    st.info(f" {table}: {result} rows")
        except Exception as e:
            st.error(f"❌ Error: {e}")