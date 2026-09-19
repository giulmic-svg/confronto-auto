import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Confronto Auto Diesel vs Elettriche", layout="wide")

# -----------------------------
# Funzioni di calcolo
# -----------------------------

def calcola_costi_diesel(anni, km_annui, costo_carburante, consumo, ass, bollo, manut, val_iniziale, val_residuo):
    costo_carburante_annuo = km_annui * consumo / 100 * costo_carburante
    costi_fissi_annui = ass + bollo + manut
    ammortamento_annuo = (val_iniziale - val_residuo) / anni

    costi = []
    for t in range(anni + 1):
        costo_t = t * (costo_carburante_annuo + costi_fissi_annui + ammortamento_annuo)
        costi.append(costo_t)
    return costi


def calcola_finanziamento(prezzo_auto, anticipo, num_rate, tasso_annuo):
    importo_finanziato = max(prezzo_auto - anticipo, 0)
    tasso_mensile = tasso_annuo / 100 / 12

    if tasso_mensile == 0:
        rata = importo_finanziato / num_rate
    else:
        rata = importo_finanziato * (tasso_mensile * (1 + tasso_mensile)**num_rate) / ((1 + tasso_mensile)**num_rate - 1)

    costo_totale = rata * num_rate
    return costo_totale


def calcola_costi_elettrica(auto, anni, km_annui, costo_corrente, perc_fv,
                            anticipo, costo_istruttoria, costo_wallbox,
                            num_rate, tasso_annuo):

    costo_corrente_eff = costo_corrente * (1 - perc_fv / 100)

    costo_energia_annuo = km_annui * auto["consumo"] / 100 * costo_corrente_eff
    costi_fissi_annui = auto["assicurazione"] + auto["bollo"] + auto["manutenzione"]
    ammortamento_annuo = (auto["prezzo"] - auto["valore_residuo"]) / anni

    costo_fin_totale = calcola_finanziamento(auto["prezzo"], anticipo, num_rate, tasso_annuo)
    costo_fin_annuo = costo_fin_totale / anni

    costi_iniziali = anticipo + costo_istruttoria + costo_wallbox

    costi = []
    for t in range(anni + 1):
        costo_t = costi_iniziali + t * (costo_energia_annuo + costi_fissi_annui + ammortamento_annuo + costo_fin_annuo)
        costi.append(costo_t)

    return costi, costo_fin_totale


# -----------------------------
# Interfaccia Streamlit
# -----------------------------

st.title("Confronto costi auto diesel vs auto elettriche")

col1, col2, col3 = st.columns([1.2, 1, 2])

# -----------------------------
# Colonna 1 – Input
# -----------------------------

with col1:
    st.header("Parametri generali")
    anni = st.number_input("Arco temporale (anni)", 1, 30, 10)
    km_annui = st.number_input("Km annui previsti", 1000, 50000, 15000)
    costo_carburante = st.number_input("Costo carburante (€/litro)", 0.5, 5.0, 1.8)
    costo_corrente = st.number_input("Costo corrente (€/kWh)", 0.05, 1.0, 0.25)
    perc_fv = st.slider("Percentuale ricarica fotovoltaico (%)", 0, 100, 30)

    st.header("Auto attuale (diesel)")
    val_diesel = st.number_input("Valore iniziale (€)", 0, 100000, 20000)
    cons_diesel = st.number_input("Consumo (litri/100 km)", 2.0, 15.0, 6.0)
    ass_diesel = st.number_input("Assicurazione annua (€)", 0, 3000, 600)
    bollo_diesel = st.number_input("Bollo annuo (€)", 0, 2000, 400)
    manut_diesel = st.number_input("Manutenzione annua (€)", 0, 3000, 500)
    val_residuo_diesel = st.number_input("Valore residuo (€)", 0, 50000, 8000)

    st.header("Finanziamento auto nuova")
    anticipo = st.number_input("Anticipo (€)", 0, 30000, 5000)
    num_rate = st.number_input("Numero rate (mesi)", 1, 120, 60)
    tasso_annuo = st.number_input("Tasso interessi annuo (%)", 0.0, 15.0, 5.0)
    costo_istruttoria = st.number_input("Costo istruttoria (€)", 0, 2000, 300)
    costo_wallbox = st.number_input("Costo wallbox (€)", 0, 5000, 1500)

    st.header("Auto elettriche")
    default_autos = [
        {"nome": "Elettrica A", "prezzo": 35000, "rata_finale": 10000, "consumo": 15,
         "assicurazione": 500, "bollo": 0, "manutenzione": 400, "valore_residuo": 15000},
        {"nome": "Elettrica B", "prezzo": 30000, "rata_finale": 8000, "consumo": 14,
         "assicurazione": 450, "bollo": 0, "manutenzione": 350, "valore_residuo": 12000},
        {"nome": "Elettrica C", "prezzo": 40000, "rata_finale": 12000, "consumo": 17,
         "assicurazione": 550, "bollo": 0, "manutenzione": 450, "valore_residuo": 18000},
    ]

    autos = []
    for auto in default_autos:
        st.subheader(auto["nome"])
        auto["prezzo"] = st.number_input(f"Prezzo {auto['nome']} (€)", 10000, 100000, auto["prezzo"])
        auto["consumo"] = st.number_input(f"Consumo {auto['nome']} (kWh/100 km)", 10, 30, auto["consumo"])
        auto["assicurazione"] = st.number_input(f"Assicurazione {auto['nome']} (€)", 0, 3000, auto["assicurazione"])
        auto["bollo"] = st.number_input(f"Bollo {auto['nome']} (€)", 0, 2000, auto["bollo"])
        auto["manutenzione"] = st.number_input(f"Manutenzione {auto['nome']} (€)", 0, 3000, auto["manutenzione"])
        auto["valore_residuo"] = st.number_input(f"Valore residuo {auto['nome']} (€)", 0, 50000, auto["valore_residuo"])
        autos.append(auto)

# -----------------------------
# Colonna 2 – Riepilogo
# -----------------------------

with col2:
    st.header("Riepilogo confronto")

    nomi_auto = [a["nome"] for a in autos]
    auto_sel_nome = st.selectbox("Auto elettrica da confrontare", nomi_auto)

    auto_sel = next(a for a in autos if a["nome"] == auto_sel_nome)

    costi_diesel = calcola_costi_diesel(
        anni, km_annui, costo_carburante, cons_diesel,
        ass_diesel, bollo_diesel, manut_diesel,
        val_diesel, val_residuo_diesel
    )

    costi_elettrica, costo_fin_totale = calcola_costi_elettrica(
        auto_sel, anni, km_annui, costo_corrente, perc_fv,
        anticipo, costo_istruttoria, costo_wallbox,
        num_rate, tasso_annuo
    )

    st.write(f"**Costo totale finanziamento:** {costo_fin_totale:,.0f} €")

    tempo_pareggio = None
    for t in range(anni + 1):
        if costi_elettrica[t] < costi_diesel[t]:
            tempo_pareggio = t
            break

    if tempo_pareggio is None:
        st.write("**Tempo di pareggio:** Nessun pareggio nel periodo")
    else:
        st.write(f"**Tempo di pareggio:** {tempo_pareggio} anni")

    # Risparmio annuo medio
    costo_carburante_annuo = km_annui * cons_diesel / 100 * costo_carburante
    costi_fissi_diesel = ass_diesel + bollo_diesel + manut_diesel

    costo_corrente_eff = costo_corrente * (1 - perc_fv / 100)
    costo_energia_annuo = km_annui * auto_sel["consumo"] / 100 * costo_corrente_eff
    costi_fissi_elettrica = auto_sel["assicurazione"] + auto_sel["bollo"] + auto_sel["manutenzione"]

    risparmio_annuo = (costo_carburante_annuo + costi_fissi_diesel) - (costo_energia_annuo + costi_fissi_elettrica)
    st.write(f"**Risparmio annuo medio:** {risparmio_annuo:,.0f} €")

# -----------------------------
# Colonna 3 – Grafico
# -----------------------------

with col3:
    st.header("Grafico dei costi nel tempo")

    fig, ax = plt.subplots(figsize=(8, 5))

    anni_list = list(range(anni + 1))

    ax.plot(anni_list, costi_diesel, label="Diesel", color="black")

    for auto in autos:
        costi_auto, _ = calcola_costi_elettrica(
            auto, anni, km_annui, costo_corrente, perc_fv,
            anticipo, costo_istruttoria, costo_wallbox,
            num_rate, tasso_annuo
        )
        ax.plot(anni_list, costi_auto, label=auto["nome"])

    ax.set_xlabel("Anni")
    ax.set_ylabel("Costo cumulato (€)")
    ax.grid(True)
    ax.legend()

    st.pyplot(fig)
