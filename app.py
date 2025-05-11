
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

from optimizer import get_best_route
from data_config import cities, city_coords, hourly_risk_matrix, hourly_speed_matrix, fuel_consumption_matrix
from visualizer import create_animated_map

st.set_page_config(layout="wide", page_title="Akıllı Rota Planlayıcı")

st.title("🚛 Akıllı ve Sürdürülebilir Rota Planlayıcı")

if "show_results" not in st.session_state:
    st.session_state.show_results = False
    st.session_state.sonuc = None
    st.session_state.saved_scenarios = []

with st.sidebar:
    st.header("⚙️ Optimizasyon Ayarları")
    pop_size = st.slider("Popülasyon Büyüklüğü", 50, 300, 100, 10)
    generations = st.slider("Nesil Sayısı", 100, 2000, 300, 100)
    max_risk = st.slider("Maksimum Toplam Risk", 0.1, 2.0, 1.2, 0.1)
    hedef = st.radio("Amaç Fonksiyonu", ["süre", "emisyon", "risk", "tümü"])
    hesapla = st.button("🚀 Rota Hesapla")

if hesapla:
    with st.spinner("🔄 En iyi rota hesaplanıyor..."):
        result = get_best_route(pop_size=pop_size, generations=generations, hedef=hedef, max_risk=max_risk)
        if result:
            st.session_state.sonuc = result
            st.session_state.show_results = True
        else:
            st.error("❌ Hiçbir geçerli rota bulunamadı. Lütfen risk sınırını veya nesil sayısını artırın.")
            st.session_state.show_results = False

if st.session_state.show_results and st.session_state.sonuc:
    route, total_time, total_fuel, total_co2, total_risk, log = st.session_state.sonuc

    tabs = st.tabs([
        "🗺️ Harita", "📊 Dağılım", "📈 İstatistik", "🎞️ Animasyon", 
        "📁 Senaryo Kaydet", "🕒 Gantt", "📊 Karşılaştırma"
    ])

    with tabs[0]:
        st.subheader("🗺️ Rota Haritası")
        m = folium.Map(location=[41.0, 28.95], zoom_start=11)
        for i in range(len(route) - 1):
            from_city = cities[route[i]]
            to_city = cities[route[i + 1]]
            coords = [city_coords[from_city], city_coords[to_city]]
            folium.PolyLine(coords, tooltip=f"{log[i]['travel_min']} dk", color='blue').add_to(m)
            folium.Marker(city_coords[from_city], popup=from_city).add_to(m)
        st_folium(m, width=900, height=500)

    with tabs[1]:
        st.subheader("📊 Parametre Dağılımları")
        col1, col2 = st.columns(2)
        col1.plotly_chart(px.histogram(x=hourly_risk_matrix.flatten(), nbins=30, title="Risk Dağılımı"), use_container_width=True)
        col2.plotly_chart(px.histogram(x=hourly_speed_matrix.flatten(), nbins=30, title="Hız Dağılımı"), use_container_width=True)

    with tabs[2]:
        st.subheader("📈 Rota İstatistikleri")
        col1, col2, col3 = st.columns(3)
        col1.metric("Toplam Süre", f"{int(total_time)} dk")
        col2.metric("Toplam Emisyon", f"{total_co2:.2f} kg CO₂")
        col3.metric("Toplam Risk", f"{total_risk:.2f}")
        st.dataframe(pd.DataFrame(log), use_container_width=True)

    with tabs[3]:
        st.subheader("🎞️ Animasyonlu Rota")
        animated_map = create_animated_map(route, log)
        st_folium(animated_map, width=900, height=500)

    with tabs[4]:
        st.subheader("📁 Senaryo Kaydet")
        senaryo_adi = st.text_input("Senaryo Adı")
        if st.button("💾 Senaryoyu Kaydet"):
            st.session_state.saved_scenarios.append({
                "isim": senaryo_adi,
                "süre": total_time,
                "emisyon": total_co2,
                "risk": total_risk
            })
            st.success(f"✅ '{senaryo_adi}' senaryosu kaydedildi.")
        if st.session_state.saved_scenarios:
            st.dataframe(pd.DataFrame(st.session_state.saved_scenarios))

    with tabs[5]:
        st.subheader("🕒 Gantt Şeması")
        gantt_data = []
        t = 0
        for entry in log:
            gantt_data.append(dict(Tip="Yolculuk", Durak=entry["to"], Start=t, End=t + entry["travel_min"]))
            t += entry["travel_min"]
            if entry["wait"] > 0:
                gantt_data.append(dict(Tip="Bekleme", Durak=entry["to"], Start=t, End=t + entry["wait"]))
                t += entry["wait"]
            if entry["service"] > 0:
                gantt_data.append(dict(Tip="Servis", Durak=entry["to"], Start=t, End=t + entry["service"]))
                t += entry["service"]
        df_gantt = pd.DataFrame(gantt_data)
        fig = px.timeline(df_gantt, x_start="Start", x_end="End", y="Durak", color="Tip", title="Zaman Akışı")
        st.plotly_chart(fig, use_container_width=True)

    with tabs[6]:
        st.subheader("📊 Senaryo Karşılaştırma")
        if st.session_state.saved_scenarios:
            df = pd.DataFrame(st.session_state.saved_scenarios)
            fig = px.bar(df, x="isim", y=["süre", "emisyon", "risk"], barmode="group", title="Senaryolar Karşılaştırması")
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("🔍 Rota hesaplamak için lütfen ayarları yapın ve '🚀 Rota Hesapla' butonuna tıklayın.")
