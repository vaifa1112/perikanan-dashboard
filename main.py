import urllib.parse
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text

app = FastAPI()

# 1. Konfigurasi CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Setup Koneksi Database PostgreSQL
db_user = "postgres"
db_pass = urllib.parse.quote_plus("userv")  # Password kamu
db_host = "localhost"
db_port = "5432"
db_name = "perikanan_tangkap"  # Nama database sesuai DBeaver

DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DATABASE_URL)

# 3. Endpoint API
@app.get("/api/perikanan")
def get_perikanan_data():
    # Query disesuaikan dengan tabel dim_kab_kota, dim_jenis_ikan, dim_jenis_usaha
    query = text("""
        SELECT 
            dk.nama_kabupaten_kota AS k,
            dj.kelompok_ikan AS g,
            dj.nama_ikan AS j,
            du.jenis_usaha AS u,
            f.tahun AS y,
            f.produksi_ton AS v,
            f.nilai_produksi_ribu_rupiah AS n
        FROM fact_produksi_perikanan f
        JOIN dim_kab_kota dk ON f.id_kab_kota = dk.id_kab_kota
        JOIN dim_jenis_ikan dj ON f.id_jenis_ikan = dj.id_jenis_ikan
        JOIN dim_jenis_usaha du ON f.id_jenis_usaha = du.id_jenis_usaha;
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query).fetchall()
        
    kab_set, grp_set, jns_set, ush_set = set(), set(), set(), set()
    rows = []
    
    for row in result:
        # Nilai di fact dalam ribuan rupiah, dikonversi ke satuan penuh (Rp)
        nilai_rp = row.n * 1000 if row.n else 0
        volume = row.v if row.v else 0
        
        # Harga per kg = Nilai (Rp) / Volume (kg) -> Volume (ton) * 1000
        harga = (nilai_rp / (volume * 1000)) if volume > 0 else 0
        
        kab_set.add(row.k)
        grp_set.add(row.g)
        jns_set.add(row.j)
        ush_set.add(row.u)
        
        # Nilai dikirim dalam satuan Rp Juta agar sesuai format dashboard
        nilai_juta = nilai_rp / 1_000_000
        
        rows.append([
            row.y, 
            row.k, 
            row.g, 
            row.j, 
            row.u, 
            round(volume, 2), 
            round(nilai_juta, 2), 
            round(harga, 2)
        ])
        
    return {
        "k": sorted(list(kab_set)),
        "g": sorted(list(grp_set)),
        "j": sorted(list(jns_set)),
        "u": sorted(list(ush_set)),
        "r": rows
    }