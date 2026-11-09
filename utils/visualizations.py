import plotly.express as px
import plotly.graph_objects as go

def create_trend_chart(df):
    """Grafik tren tahunan volume vs nilai"""
    df_trend = df.groupby('tahun').agg({
        'volume': 'sum',
        'nilai_triliun': 'sum'
    }).reset_index()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_trend['tahun'],
        y=df_trend['volume'],
        name='Volume (Ton)',
        marker_color='#1f77b4'
    ))
    fig.add_trace(go.Scatter(
        x=df_trend['tahun'],
        y=df_trend['nilai_triliun'],
        name='Nilai (Triliun Rp)',
        marker_color='#ff7f0e',
        line=dict(width=3),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Tren Tahunan: Volume vs Nilai Ekonomi',
        xaxis=dict(title='Tahun'),
        yaxis=dict(title='Volume (Ton)', side='left'),
        yaxis2=dict(title='Nilai (Triliun Rp)', side='right', overlaying='y'),
        legend=dict(x=0, y=1.1),
        hovermode='x unified'
    )
    
    return fig

def create_top_kabupaten_chart(df, top_n=10):
    """Grafik top kabupaten/kota"""
    df_kab = df.groupby('kabupaten')['volume'].sum().nlargest(top_n).reset_index()
    
    fig = px.bar(
        df_kab, 
        y='kabupaten', 
        x='volume',
        orientation='h',
        title=f'Top {top_n} Kabupaten/Kota Penghasil Volume Tertinggi',
        labels={'volume': 'Volume (Ton)', 'kabupaten': 'Kabupaten/Kota'},
        color='volume',
        color_continuous_scale='Blues'
    )
    fig.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def create_top_ikan_chart(df, top_n=10):
    """Grafik top jenis ikan berdasarkan nilai"""
    df_ikan = df.groupby('jenis_ikan')['nilai_juta'].sum().nlargest(top_n).reset_index()
    
    fig = px.bar(
        df_ikan,
        y='jenis_ikan',
        x='nilai_juta',
        orientation='h',
        title=f'Top {top_n} Jenis Ikan Nilai Ekonomi Tertinggi',
        labels={'nilai_juta': 'Nilai (Juta Rp)', 'jenis_ikan': 'Jenis Ikan'},
        color='nilai_juta',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'})
    return fig

def create_pie_usaha_chart(df):
    """Grafik proporsi jenis usaha"""
    df_u = df.groupby('usaha')['volume'].sum().reset_index()
    
    fig = px.pie(
        df_u,
        values='volume',
        names='usaha',
        title='Proporsi Volume menurut Jenis Usaha',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    return fig

def create_scatter_harga_volume(df):
    """Scatter plot harga vs volume"""
    df_scatter = df.groupby('jenis_ikan').agg({
        'volume': 'sum',
        'harga_per_kg': 'mean'
    }).nlargest(10, 'volume').reset_index()
    
    fig = px.scatter(
        df_scatter,
        x='volume',
        y='harga_per_kg',
        text='jenis_ikan',
        title='Sebaran Harga vs Volume (10 Komoditas Utama)',
        labels={'volume': 'Volume (Ton)', 'harga_per_kg': 'Harga (Rp/kg)'},
        size='volume',
        color='harga_per_kg',
        color_continuous_scale='RdYlGn'
    )
    fig.update_traces(textposition='top center')
    return fig