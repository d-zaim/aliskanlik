import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import random 
# CSV dosyasını yükleyin
@st.cache_data
def load_data():
    data = pd.read_csv(r"C:\Users\ad_za\OneDrive\Masaüstü\Alışkanlık\Alışkanlık Takip\tum_veri_5h.csv")

    data['Tarih'] = pd.to_datetime(data['Tarih'])
    return data

data = load_data()

# Uygulama Başlığı
st.title("Alışkanlık Takip")

st.text('İçerik:\n1)Alışkanlıkların seri takibi\n2)Alışkanlıkların çizgi grafiği gösterimi\n3)Haftalara ve alışkanlıklara göre en iyiler')
# Kullanıcıları seçme
users = data['isim'].unique()
selected_user = st.selectbox("İsim Seçiniz:", users)

# Seçilen kişinin verileri
user_data = data[data['isim'] == selected_user]
user_data['Zincir'] = (user_data.iloc[:, 3:] > 0).sum(axis=1)

# 4 Alışkanlığın Haftalık Değişimleri
habit_columns = ['Egzersiz', 'Günlük rutin', 'Nafile ibadet', 'Bireysel']


# Tarih sütununu indeks yap
user_data.set_index('Tarih', inplace=True)

# Kutuların içerisine yazılacak gün numaralarını hazırlama
annot_data = user_data.index.strftime("%d").values  # Günleri alıyoruz
annot_matrix = np.tile(annot_data, (len(habit_columns), 1))  # Her alışkanlık için tekrar

# Haftaların başlangıç günlerini belirle
week_starts = user_data.index.to_series().dt.to_period("W").drop_duplicates().index  # Haftalık gruplama

# Heatmap için görselleştirme
st.subheader(f"{selected_user} - Alışkanlık Serileri/Zincirleri")
st.text('Bazen hata verebiliyor, sayfa yenilenince düzeliyor.')
plt.figure(figsize=(12, 6))
heatmap_data = user_data[habit_columns] > 0  # Alışkanlıklar başarılıysa True

ax = sns.heatmap(
    heatmap_data.T,  # Transpoze ederek günleri sütunlara dönüştürüyoruz
    cmap="Greens",  # Başarılı günler yeşil renk ile gösterilir
    cbar=False,  # Renk çubuğunu kaldır
    linewidths=0.5,
    linecolor='lightgrey',
    annot=annot_matrix,  # Gün numaralarını kutulara yaz
    fmt="",  # Sayı formatını düz tut
    annot_kws={"fontsize": 10, "color": "black"}  # Yazı stili
)
plt.title("Haftalar turuncu çizgi ile ayrılmıştır", fontsize=16)

# Haftaların başlangıcına dikey çizgiler ekle
for week_start in week_starts:
    ax.axvline(x=user_data.index.get_loc(week_start), color="orange", linestyle="-", linewidth=2)

# Tarihleri gün-ay formatına dönüştür ve ortala
xtick_positions = np.arange(len(user_data.index)) + 0.5  # Ticks'i kutunun ortasına kaydır
plt.xticks(
    ticks=xtick_positions,
    labels=user_data.index.strftime("%d-%m"),  # Tarih formatı: gün-ay
    rotation=90
)
plt.xlabel("Tarih (Gün-Ay)", fontsize=12)
plt.ylabel("Alışkanlıklar", fontsize=12)
plt.yticks(rotation=0)
st.pyplot(plt)

user_data.reset_index(inplace=True)

# Grafik 1: 4 Alışkanlığın Haftalık Performansı
st.subheader(f"{selected_user} - Alışkanlıklar Çizgi Grafiği")
st.text('Grafiğin sağ üstündeki alışkanlıklara tıklayarak\nistediğiniz alışkanlıkları gösterip kapatabilirsiniz.')
fig1 = go.Figure()
for habit in habit_columns:
    fig1.add_trace(go.Scatter(x=user_data['Tarih'], y=user_data[habit], mode='lines+markers', name=habit))

fig1.update_layout(
    title="",
    xaxis_title="Tarih",
    yaxis_title="Gerçekleştirme (1/0)",
    template="plotly_dark",
)
st.plotly_chart(fig1)

data = data.drop(data[data.isim == 'Toplam'].index)

data['Tarih'] = pd.to_datetime(data['Tarih'])
data.set_index('Tarih', inplace=True)


from datetime import timedelta

# Haftaları isimlendirme fonksiyonu
def name_weeks(data):
    grouped = data.groupby(data.index.to_period("W"))  # Haftalara göre gruplama
    week_names = []
    for i, (week, group) in enumerate(grouped, start=1):
        start_date = group.index.min().strftime("%d-%m")
        end_date = group.index.max().strftime("%d-%m")
        week_names.append(f"{i}. Hafta ({start_date}  --  {end_date})")
    return week_names, list(grouped)

# Haftaları adlandır ve grupla
week_names, weekly_groups = name_weeks(data)

# Haftalara göre veri hazırlığı
def get_weekly_data(week_index, data):
    selected_week_data = weekly_groups[week_index][1]
    return selected_week_data.groupby("isim")[habit_columns].sum()

# Her bir kullanıcı için toplam skorların hesaplanması
total_scores = data.groupby("isim")[habit_columns].sum()
total_scores["Skor"] = total_scores.sum(axis=1)

# Tüm haftalar için toplam veriyi hazırlama
def get_all_weeks_data(data):
    all_scores = data.groupby("isim")[habit_columns].sum()
    all_scores["Skor"] = all_scores.sum(axis=1)  # Skor sütunu ekle
    return all_scores.sort_values("Skor", ascending=False).astype(int)

# Haftalık ve alışkanlık seçimleri
st.header("Sıralamalar")
selected_habit = st.selectbox("Alışkanlık Seçin:", ["Tüm Alışkanlıklar", *habit_columns])
selected_week = st.selectbox("Hafta Seçin:", ["Tüm Haftalar"] + week_names)

# Maksimum skor hesaplama fonksiyonu
def calculate_max_score(total_days, total_habits):
    return total_days * total_habits

# Tabloları oluşturma
if selected_week == "Tüm Haftalar":
    total_days = data.reset_index()["Tarih"].nunique()  # Tüm haftalardaki toplam gün sayısı
    if selected_habit == "Tüm Alışkanlıklar":
        max_score = calculate_max_score(total_days, len(habit_columns))  # Tüm haftalar, tüm alışkanlıklar
        table_data = total_scores[["Skor"]].reset_index().sort_values('Skor',ascending=False)
        table_data["Başarı Yüzdesi"] = (table_data["Skor"] / max_score * 100).round(2)
    else:
        max_score = calculate_max_score(total_days, 1)  # Tüm haftalar, 1 alışkanlık
        table_data = total_scores[[selected_habit]].reset_index().rename(columns={selected_habit: "Skor"}).sort_values('Skor',ascending=False)
        table_data["Başarı Yüzdesi"] = (table_data["Skor"] / max_score * 100).round(2)
else:
    selected_week_index = week_names.index(selected_week)
    selected_week_data = get_weekly_data(selected_week_index, data)
    total_days_week = 7  # Belirli haftadaki toplam gün sayısı
    
    if selected_habit == "Tüm Alışkanlıklar":
        max_score = calculate_max_score(total_days_week, len(habit_columns))  # Belirli hafta, tüm alışkanlıklar
        weekly_scores = selected_week_data.sum(axis=1).sort_values(ascending=False)
        table_data = pd.DataFrame({"İsim": weekly_scores.index, "Skor": weekly_scores.values})
        table_data["Başarı Yüzdesi"] = (table_data["Skor"] / max_score * 100).round(2)
    else:
        max_score = calculate_max_score(total_days_week, 1)  # Belirli hafta, 1 alışkanlık
        weekly_scores = selected_week_data[selected_habit].sort_values(ascending=False)
        table_data = pd.DataFrame({"İsim": weekly_scores.index, "Skor": weekly_scores.values})
        table_data["Başarı Yüzdesi"] = (weekly_scores.values / max_score * 100).round(2)

# İndeksi 1’den başlat
table_data.index = range(1, len(table_data) + 1)
table_data.Skor = table_data.Skor.astype(int)
table_data["Başarı Yüzdesi"] = table_data["Başarı Yüzdesi"].astype(float).round(2)

# Tabloyu göster
st.subheader(f"{selected_week} - {selected_habit}")
st.table(table_data)
