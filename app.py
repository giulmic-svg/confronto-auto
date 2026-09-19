import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------
# CONFIGURAZIONE PAGINA
# ---------------------------------------------------------
st.set_page_config(page_title="Confronto costi auto", layout="wide")
st.title("Confronto costi auto")

# ---------------------------------------------------------
# CSS — SIDEBAR LARGA 50% + INPUT SCROLLABILI
# ---------------------------------------------------------
st.markdown("""
<style>
/* Allarga la sidebar al 50% */
[data-testid="stSidebar"] {
    width: 50% !important;
    min-width: 50% !important;
}

/* Riquadro dati scrollabile */
.left-pane {
    height: 90vh;
    overflow-y: scroll;
    background-color: white;
    padding-right: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# FUNZIONI DI CALCOLO
# ---------------------------------------------------------

def calcola_costi_diesel(anni, km_annui, costo_carburante, consumo, ass, bollo, manut, val_iniziale, val_residuo):
    costo_carburante_annuo = km_annui * consumo / 100 * costo_carburante
    costi_fissi_annui = ass + bollo + manut
    ammortamento_annuo = (val_iniziale - val_residuo) / anni
    return [t * (costo_carburante_annuo + costi_fissi_annui + ammortamento_annuo) for t in range(anni + 1)]


def calcola_finanziamento(prezzo_auto, anticipo, num_rate, tasso_annuo):
    importo_finanziato = max(prezzo_auto - anticipo, 0)
    tasso_mensile = tasso_annuo / 100 / 12
    if tasso_mensile == 0:
        rata = importo_finanziato / num_rate
    else:
        rata = importo_finanziato * (tasso_mensile * (1 + tasso_mensile)**num_rate) / ((1 + tasso_mensile)**num_rate - 1)
    return rata * num_rate, rata


def calcola_costi_elettrica(auto, anni, km_annui, costo_corrente, perc_fv,
                            anticipo, costo_istruttoria, costo_wallbox,
                            num_rate, tasso_annuo):

    costo_corrente_eff = costo_corrente * (1 - perc_fv / 100)
    costo_energia_annuo = km_annui * auto["consumo"] / 100 * costo_corrente_eff
    costi_fissi_annui = auto["assicurazione"] + auto["bollo"] + auto["manutenzione"]
    ammortamento_annuo = (auto["prezzo"] - auto["valore_residuo"]) / anni

    costo_fin_totale, rata_mensile = calcola_finanziamento(auto["prezzo"], anticipo, num_rate, tasso_annuo)
    anni_fin = num_rate / 12
    costo_rate_annuo = rata_mensile * 12
    costi_iniziali = anticipo + costo_istruttoria + costo_wallbox

    costi = []
    for t in range(anni + 1):
        if t < anni_fin:
            costo_t = costi_iniziali + t * (costo_energia_annuo + costi_fissi_annui + ammortamento_annuo) + costo_rate_annuo * t
        else:
            costo_t = costi_iniziali + anni_fin * costo_rate_annuo + t * (costo_energia_annuo + costi_fissi_annui + ammortamento_annuo)
        costi.append(costo_t)

    return costi, costo_fin_totale

# ---------------------------------------------------------
# COLONNA SINISTRA — INPUT (SCROLLABILE)
# ---------------------------------------------------------

st.markdown('<div class="left-pane">', unsafe_allow_html=True)

st.header("Parametri generali")
anni = st.number_input("Arco temporale (anni)", 1, 30, 10)
km_annui = st.number_input("Km annui previsti", 1000, 50000, 15000)
costo_carburante = st.number_input("Costo carburante (€/litro)", 0.5, 5.0, 1.8)
costo_corrente = st.number_input("Costo corrente (€/kWh)", 0.05, 1.0, 0.25)
perc_fv = st.slider("Percentuale ricarica fotovoltaico (%)", 0, 100, 30)

st.header("Auto attuale (diesel)")
nome_diesel = st.text_input("Nome auto diesel", "La mia auto")
val_diesel = st.number_input("Valore iniziale (€)", 0, 100000, 20000)
cons_diesel = st.number_input("Consumo (litri/100 km)", 2.0, 15.0, 6.0)
ass_diesel = st.number_input("Assicurazione annua (€)", 0, 3000, 600)
bollo_diesel = st.number_input("Bollo annuo (€)", 0, 2000, 400)
manut_diesel = st.number_input("Manutenzione annua (€)", 0, 3000, 500)
val_residuo_diesel = st.number_input("Valore residuo (€)", 0, 50000, 8000)

st.header("Auto nuova (elettrica)")
auto_principale = {
    "nome": st.text_input("Nome auto elettrica principale", "Auto nuova"),
    "prezzo": st.number_input("Prezzo (€)", 10000, 100000, 35000),
    "consumo": st.number_input("Consumo (kWh/100 km)", 10, 30, 15),
    "assicurazione": st.number_input("Assicurazione (€)", 0, 3000, 500),
    "bollo": st.number_input("Bollo (€)", 0, 2000, 0),
    "manutenzione": st.number_input("Manutenzione (€)", 0, 3000, 400),
    "valore_residuo": st.number_input("Valore residuo (€)", 0, 50000, 15000)
}

st.header("Finanziamento auto nuova")
anticipo = st.number_input("Anticipo (€)", 0, 30000, 5000)
num_rate = st.number_input("Numero rate (mesi)", 1, 120, 60)
tasso_annuo = st.number_input("Tasso interessi annuo (%)", 0.0, 15.0, 5.0)
costo_istruttoria = st.number_input("Costo istruttoria (€)", 0, 2000, 300)
costo_wallbox = st.number_input("Costo wallbox (€)", 0, 5000, 1500)

st.header("Aggiungi altre auto elettriche")
num_extra = st.number_input("Quante auto aggiuntive vuoi?", 0, 10, 0)

autos_extra = []
for i in range(num_extra):
    st.subheader(f"Auto aggiuntiva {i+1}")
    auto = {
        "nome": st.text_input(f"Nome auto {i+1}", f"Auto {i+1}"),
        "prezzo": st.number_input(f"Prezzo auto {i+1} (€)", 10000, 100000, 30000),
        "consumo": st.number_input(f"Consumo auto {i+1} (kWh/100 km)", 10, 30, 14),
        "assicurazione": st.number_input(f"Assicurazione auto {i+1} (€)", 0, 3000, 450),
        "bollo": st.number_input(f"Bollo auto {i+1} (€)", 0, 2000, 0),
        "manutenzione": st.number_input(f"Manutenzione auto {i+1} (€)", 0, 3000, 350),
        "valore_residuo": st.number_input(f"Valore residuo auto {i+1} (€)", 0, 50000, 12000)
    }
    autos_extra.append(auto)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# CALCOLI
# ---------------------------------------------------------

costi_diesel = calcola_costi_diesel(
    anni, km_annui, costo_carburante, cons_diesel,
    ass_diesel, bollo_diesel, manut_diesel,
    val_diesel, val_residuo_diesel
)

costi_auto_principale, costo_fin_totale = calcola_costi_elettrica(
    auto_principale, anni, km_annui, costo_corrente, perc_fv,
    anticipo, costo_istruttoria, costo_wallbox,
    num_rate, tasso_annuo
)

# ---------------------------------------------------------
# SIDEBAR — GRAFICO FISSO + RIEPILOGO
# ---------------------------------------------------------

st.sidebar.header("Riepilogo completo")

tempo_pareggio = None
for t in range(anni + 1):
    if costi_auto_principale[t] < costi_diesel[t]:
        tempo_pareggio = t
        break

if tempo_pareggio is None:
    st.sidebar.write("**Tempo di pareggio:** Nessun pareggio nel periodo")
else:
    st.sidebar.write(f"**Tempo di pareggio:** {tempo_pareggio} anni")

costo_carburante_annuo = km_annui * cons_diesel / 100 * costo_carburante
costi_fissi_diesel = ass_diesel + bollo_diesel + manut_diesel

costo_corrente_eff = costo_corrente * (1 - perc_fv / 100)
costo_energia_annuo = km_annui * auto_principale["consumo"] / 100 * costo_corrente_eff
costi_fissi_elettrica = auto_principale["assicurazione"] + auto_principale["bollo"] + auto_principale["manutenzione"]

risparmio_annuo = (costo_carburante_annuo + costi_fissi_diesel) - (costo_energia_annuo + costi_fissi_elettrica)

st.sidebar.write(f"**Costo totale finanziamento:** {costo_fin_totale:,.0f} €")
st.sidebar.write(f"**Risparmio annuo medio:** {risparmio_annuo:,.0f} €")
st.sidebar.write(f"**Auto selezionata:** {auto_principale['nome']}")

# ---------------- GRAFICO ----------------
st.sidebar.header("Grafico dei costi nel tempo")

anni_list = list(range(anni + 1))

fig = go.Figure()
fig.add_trace(go.Scatter(x=anni_list, y=costi_diesel, mode='lines+markers', name=nome_diesel))
fig.add_trace(go.Scatter(x=anni_list, y=costi_auto_principale, mode='lines+markers', name=auto_principale["nome"]))

for auto in autos_extra:
    costi_extra, _ = calcola_costi_elettrica(
        auto, anni, km_annui, costo_corrente, perc_fv,
        anticipo, costo_istruttoria, costo_wallbox,
        num_rate, tasso_annuo
    )
    fig.add_trace(go.Scatter(x=anni_list, y=costi_extra, mode='lines+markers', name=auto["nome"]))

fig.update_layout(
    xaxis_title="Anni",
    yaxis_title="Costo cumulato (€)",
    hovermode="x unified",
    height=600
)

st.sidebar.plotly_chart(fig, use_container_width=True)
