# ============================================================
#  MARKOWITZ PORTFOLIO OPTIMIZER — Streamlit App
#  Para correr local: streamlit run app.py
#  Para deploy: subir a GitHub + Streamlit Community Cloud
# ============================================================

import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy.optimize import minimize
from scipy import stats
import warnings
import datetime
import base64
from io import BytesIO

warnings.filterwarnings("ignore")

# ── CONFIGURACIÓN DE PÁGINA ──────────────────────────────────
st.set_page_config(
    page_title="Portfolio Optimizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 Optimizador de Portafolios — Markowitz")
st.caption("Análisis cuantitativo de riesgo y retorno con frontera eficiente")

# ── SIDEBAR: INPUTS DEL USUARIO ──────────────────────────────
with st.sidebar:
    # Logo LHA en el sidebar
    logo_b64 = logo_a_base64("logo_sidebar.png")
    if logo_b64:
        st.markdown(
            f'<div style="text-align:center; padding: 8px 0 4px 0;">'
            f'<img src="data:image/png;base64,{logo_b64}" '
            f'style="width:160px; opacity:0.92;"></div>',
            unsafe_allow_html=True
        )
        st.divider()
    st.header("⚙️ Parámetros")

    tickers_raw = st.text_input(
        "Tickers (separados por coma)",
        value="KO,MELI,GGAL,BMA,HD,META",
        help="Máximo 20 activos recomendado. Ej: AAPL,MSFT,GOOGL"
    )

    anios = st.slider(
        "Años de historia", min_value=1, max_value=15, value=5,
        help="Más años = más datos, pero puede incluir regímenes de mercado distintos"
    )

    rf = st.number_input(
        "Tasa libre de riesgo anual (%)",
        min_value=0.0, max_value=20.0, value=2.0, step=0.5,
        help="Usá la tasa del bono del Tesoro USA a 10 años"
    ) / 100

    retorno_objetivo = st.number_input(
        "Retorno objetivo anual (%)",
        min_value=1.0, max_value=100.0, value=22.0, step=1.0,
        help="El optimizador buscará el portafolio con mínimo riesgo para este retorno"
    ) / 100

    peso_max = st.slider(
        "Concentración máxima por activo (%)",
        min_value=10, max_value=100, value=100, step=5,
        help="Limita cuánto puede poner el optimizador en un solo activo"
    ) / 100

    correr = st.button("🚀 Analizar", type="primary", use_container_width=True)

    st.divider()
    st.caption("💡 El código corre en el servidor. Los usuarios no tienen acceso al código fuente.")

# ── CONSTANTES ───────────────────────────────────────────────
# ── FUNCIÓN WATERMARK ────────────────────────────────────────
def agregar_watermark(ax, logo_path="logo_watermark.png", alpha=0.12):
    """Agrega el logo LHA como watermark centrado en el gráfico."""
    try:
        from PIL import Image as PILImage
        import matplotlib.image as mpimg
        logo = mpimg.imread(logo_path)
        ax_pos = ax.get_position()
        fig = ax.get_figure()
        fig_w, fig_h = fig.get_size_inches()
        # Posición centrada en el axes
        logo_ax = fig.add_axes(
            [ax_pos.x0 + ax_pos.width*0.25,
             ax_pos.y0 + ax_pos.height*0.25,
             ax_pos.width*0.5,
             ax_pos.height*0.5],
            zorder=0
        )
        logo_ax.imshow(logo, aspect="equal", alpha=alpha)
        logo_ax.axis("off")
        logo_ax.set_navigate(False)
    except Exception:
        pass   # Si falla el watermark, el gráfico igual se muestra

def logo_a_base64(path):
    """Convierte imagen a base64 para mostrar en Streamlit."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None
DIAS_TRADING = 252
UMBRAL_CORR  = 0.80
N_SIMS       = 6000

COLORES_ACTIVOS = [
    "#3498db","#e74c3c","#2ecc71","#f39c12","#9b59b6",
    "#1abc9c","#e67e22","#34495e","#e91e63","#00bcd4",
    "#8bc34a","#ff5722","#607d8b","#795548","#cddc39"
]

# ── FUNCIONES DE CÁLCULO ─────────────────────────────────────
def retorno_p(w, ret): return np.dot(w, ret.mean()) * DIAS_TRADING
def volatilidad_p(w, ret):
    cov = ret.cov() * DIAS_TRADING
    return np.sqrt(np.dot(w.T, np.dot(cov, w)))
def sharpe_p(w, ret, rf): 
    v = volatilidad_p(w, ret)
    return (retorno_p(w, ret) - rf) / v if v > 0 else 0
def metricas_p(w, ret, rf):
    r = retorno_p(w, ret)
    v = volatilidad_p(w, ret)
    return {"retorno": r, "volatilidad": v, "sharpe": (r-rf)/v if v>0 else 0}

def cagr_p(w, ret):
    rd = ret.dot(w)
    return np.exp(rd.sum()) ** (DIAS_TRADING / len(rd)) - 1

def ret12m_p(w, ret):
    r12 = ret.iloc[-min(252, len(ret)):]
    return np.exp(r12.dot(w).sum()) - 1

def beta_p(w, ret, bm_ret):
    rp = ret.dot(w)
    aln = pd.concat([rp, bm_ret.squeeze()], axis=1, join="inner")
    aln.columns = ["p","b"]
    cov = aln.cov()
    return cov.loc["p","b"] / cov.loc["b","b"]

# ── LÓGICA PRINCIPAL ─────────────────────────────────────────
if not correr:
    st.info("👈 Configurá los parámetros en el panel izquierdo y presioná **Analizar**.")
    st.stop()

# ── 1. DESCARGA Y LIMPIEZA DE DATOS ──────────────────────────
#
#  Soporta dos tipos de tickers:
#  - Internacionales: KO, META, GGAL  → yfinance directo en USD
#  - Argentinos locales: GGAL.BA, PAMP.BA → yfinance en ARS → convertir a USD via CCL
#
#  CCL = GD30C.BA (precio en ARS) ÷ GD30 (precio en USD)

tickers_raw_lista = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()][:20]

fecha_fin    = datetime.date.today()
fecha_inicio = fecha_fin - datetime.timedelta(days=int(anios * 365.25))

# ── PASO A: Calcular tipo de cambio CCL si hay tickers .BA ───
tickers_ba   = [t for t in tickers_raw_lista if t.endswith(".BA")]
tickers_usd  = [t for t in tickers_raw_lista if not t.endswith(".BA")]
ccl_serie    = None

if tickers_ba:
    with st.spinner("💱 Calculando tipo de cambio CCL (GD30C÷GD30)..."):
        try:
            raw_gd30c = yf.download("GD30C.BA", start=fecha_inicio, end=fecha_fin,
                                     auto_adjust=True, progress=False)
            raw_gd30  = yf.download("GD30",     start=fecha_inicio, end=fecha_fin,
                                     auto_adjust=True, progress=False)

            # Extraer Series limpias
            gd30c = (raw_gd30c["Close"].iloc[:,0]
                     if isinstance(raw_gd30c.columns, pd.MultiIndex)
                     else raw_gd30c["Close"]).squeeze()
            gd30  = (raw_gd30["Close"].iloc[:,0]
                     if isinstance(raw_gd30.columns, pd.MultiIndex)
                     else raw_gd30["Close"]).squeeze()

            # CCL = precio ARS ÷ precio USD del mismo bono
            ccl_df   = pd.concat([gd30c, gd30], axis=1, join="inner")
            ccl_df.columns = ["gd30c","gd30"]
            ccl_serie = (ccl_df["gd30c"] / ccl_df["gd30"]).ffill()

            ccl_actual = ccl_serie.iloc[-1]
            st.info(f"💱 CCL calculado: ${ccl_actual:,.1f} ARS/USD "
                    f"(último dato: {ccl_serie.index[-1].date()})")
        except Exception as e:
            st.error(f"❌ No se pudo calcular el CCL: {e}. "
                     "Verificá que GD30C.BA y GD30 estén disponibles en yfinance.")
            st.stop()

# ── PASO B: Descargar precios de todos los tickers ────────────
with st.spinner("📡 Descargando datos históricos..."):

    dict_precios = {}   # ticker → Serie de precios en USD

    # Tickers internacionales (USD directo)
    if tickers_usd:
        raw_usd = yf.download(tickers_usd, start=fecha_inicio, end=fecha_fin,
                               auto_adjust=True, progress=False)
        if isinstance(raw_usd.columns, pd.MultiIndex):
            precios_usd = raw_usd["Close"]
        else:
            precios_usd = raw_usd[["Close"]]
            precios_usd.columns = tickers_usd

        for t in tickers_usd:
            if t in precios_usd.columns:
                dict_precios[t] = precios_usd[t]

    # Tickers argentinos (.BA → ARS → USD via CCL)
    for t_ba in tickers_ba:
        try:
            raw_ba = yf.download(t_ba, start=fecha_inicio, end=fecha_fin,
                                  auto_adjust=True, progress=False)
            if raw_ba.empty:
                st.warning(f"⚠️ {t_ba}: sin datos en yfinance, se descarta.")
                continue

            precio_ars = (raw_ba["Close"].iloc[:,0]
                          if isinstance(raw_ba.columns, pd.MultiIndex)
                          else raw_ba["Close"]).squeeze()

            # Alinear CCL con los precios del activo
            ccl_aligned = ccl_serie.reindex(precio_ars.index).ffill().bfill()

            # Convertir ARS → USD
            precio_usd = precio_ars / ccl_aligned
            dict_precios[t_ba] = precio_usd

        except Exception as e:
            st.warning(f"⚠️ {t_ba}: error al descargar ({e}), se descarta.")

    if len(dict_precios) < 2:
        st.error("❌ Se necesitan al menos 2 activos válidos. "
                 "Revisá los tickers. Locales argentinos usan sufijo .BA (ej: GGAL.BA)")
        st.stop()

    # Armar DataFrame unificado en USD
    precios_df = pd.DataFrame(dict_precios).ffill().dropna()

    # Filtrar activos con cobertura mínima del 80%
    total_dias = len(precios_df)
    validos = [t for t in precios_df.columns
               if precios_df[t].dropna().__len__() / total_dias >= 0.8
               and precios_df[t].dropna().__len__() > 30]

    descartados = [t for t in precios_df.columns if t not in validos]
    if descartados:
        st.warning(f"⚠️ Activos descartados por datos insuficientes: {', '.join(descartados)}")

    if len(validos) < 2:
        st.error("❌ Menos de 2 activos válidos tras el filtro. Revisá los tickers.")
        st.stop()

    precios  = precios_df[validos].ffill().dropna()
    tickers  = validos
    retornos = np.log(precios / precios.shift(1)).dropna()

    # Mostrar resumen de activos cargados
    n_ba  = sum(1 for t in tickers if t.endswith(".BA"))
    n_usd = len(tickers) - n_ba
    st.caption(f"📊 {len(tickers)} activos cargados en USD — "
               f"{n_usd} internacionales · {n_ba} argentinos (via CCL)")

# ── 2. BENCHMARKS ─────────────────────────────────────────────
with st.spinner("📡 Descargando benchmarks SPY y QQQ..."):
    benchmarks = {}
    for bm in ["SPY","QQQ"]:
        try:
            raw_bm = yf.download(bm, start=fecha_inicio, end=fecha_fin,
                                  auto_adjust=True, progress=False)
            bm_data = (raw_bm["Close"].iloc[:,0]
                       if isinstance(raw_bm.columns, pd.MultiIndex)
                       else raw_bm["Close"]).squeeze()
            bm_ret  = np.log(bm_data / bm_data.shift(1)).dropna().squeeze()
            benchmarks[bm] = {
                "precios": bm_data, "retornos": bm_ret,
                "retorno_anual":     bm_ret.mean() * DIAS_TRADING,
                "volatilidad_anual": bm_ret.std()  * np.sqrt(DIAS_TRADING),
                "sharpe": (bm_ret.mean()*DIAS_TRADING - rf) / (bm_ret.std()*np.sqrt(DIAS_TRADING)),
                "cagr":   (bm_data.iloc[-1]/bm_data.iloc[0])**(DIAS_TRADING/len(bm_data))-1,
                "retorno_12m": (bm_data.squeeze().iloc[-1] /
                                bm_data.squeeze().iloc[-min(252,len(bm_data)):].iloc[0]) - 1
            }
        except Exception:
            pass

# ── 3. OPTIMIZACIÓN ───────────────────────────────────────────
with st.spinner("⚙️ Optimizando portafolios..."):
    n = len(tickers)
    np.random.seed(42)
    limites     = tuple((0, peso_max) for _ in range(n))
    rest_suma1  = [{"type":"eq","fun": lambda w: np.sum(w)-1}]
    w0          = np.array([1/n]*n)

    # Monte Carlo
    sim_r, sim_v, sim_s, sim_w = [np.zeros(N_SIMS) for _ in range(3)], \
                                  np.zeros(N_SIMS), np.zeros(N_SIMS), \
                                  np.zeros((N_SIMS, n))
    sim_r = np.zeros(N_SIMS); sim_v = np.zeros(N_SIMS); sim_s = np.zeros(N_SIMS)
    for i in range(N_SIMS):
        w = np.random.dirichlet(np.ones(n))
        sim_r[i] = retorno_p(w, retornos)
        sim_v[i] = volatilidad_p(w, retornos)
        sim_s[i] = sharpe_p(w, retornos, rf)

    # Máx Sharpe
    res_s = minimize(lambda w: -sharpe_p(w,retornos,rf), w0,
                     method="SLSQP", bounds=limites, constraints=rest_suma1,
                     options={"maxiter":1000,"ftol":1e-9})
    pesos_sharpe   = res_s.x
    met_sharpe     = metricas_p(pesos_sharpe, retornos, rf)

    # Mín Volatilidad
    res_v = minimize(lambda w: volatilidad_p(w,retornos), w0,
                     method="SLSQP", bounds=limites, constraints=rest_suma1,
                     options={"maxiter":1000,"ftol":1e-9})
    pesos_minvol   = res_v.x
    met_minvol     = metricas_p(pesos_minvol, retornos, rf)

    # Retorno Objetivo
    ret_max = sim_r.max()
    ret_min = met_minvol["retorno"]
    ro_ef   = max(min(retorno_objetivo, ret_max*0.98), ret_min)
    if retorno_objetivo > ret_max:
        st.warning(f"⚠️ Retorno objetivo {retorno_objetivo*100:.1f}% supera el máximo posible "
                   f"({ret_max*100:.1f}%). Usando {ro_ef*100:.1f}%.")
    res_o = minimize(lambda w: volatilidad_p(w,retornos), pesos_sharpe,
                     method="SLSQP", bounds=limites,
                     constraints=rest_suma1 + [
                         {"type":"eq","fun": lambda w: retorno_p(w,retornos)-ro_ef}],
                     options={"maxiter":1000,"ftol":1e-9})
    pesos_objetivo = res_o.x if res_o.success else pesos_sharpe.copy()
    met_objetivo   = metricas_p(pesos_objetivo, retornos, rf)

    # Frontera Eficiente
    fe_rets, fe_vols = [], []
    for rt in np.linspace(ret_min, ret_max*0.995, 50):
        r = minimize(lambda w: volatilidad_p(w,retornos), w0,
                     method="SLSQP", bounds=limites,
                     constraints=rest_suma1+[
                         {"type":"eq","fun":lambda w,r=rt: retorno_p(w,retornos)-r}],
                     options={"maxiter":500,"ftol":1e-8})
        if r.success:
            fe_rets.append(rt); fe_vols.append(volatilidad_p(r.x,retornos))
    fe_rets = np.array(fe_rets); fe_vols = np.array(fe_vols)

    # Estadísticas individuales
    estadisticas = pd.DataFrame({
        "Retorno anual (%)":     (retornos.mean()*DIAS_TRADING*100).round(2),
        "Volatilidad anual (%)": (retornos.std()*np.sqrt(DIAS_TRADING)*100).round(2),
        "CAGR (%)": (((precios.iloc[-1]/precios.iloc[0])**(DIAS_TRADING/len(precios))-1)*100).round(2),
    })

    # Tabla resumen
    matriz_corr = retornos.corr().round(2)
    filas = []
    for nom, pw, met in [
        ("Sharpe Óptimo", pesos_sharpe, met_sharpe),
        ("Mínima Volatilidad", pesos_minvol, met_minvol),
        (f"Objetivo {retorno_objetivo*100:.1f}%", pesos_objetivo, met_objetivo),
    ]:
        bspy = beta_p(pw,retornos,benchmarks["SPY"]["retornos"]) if "SPY" in benchmarks else np.nan
        bqqq = beta_p(pw,retornos,benchmarks["QQQ"]["retornos"]) if "QQQ" in benchmarks else np.nan
        filas.append({"Portfolio":nom,
                      "Retorno (%)":round(met["retorno"]*100,2),
                      "Vol (%)":round(met["volatilidad"]*100,2),
                      "Sharpe":round(met["sharpe"],2),
                      "CAGR (%)":round(cagr_p(pw,retornos)*100,2),
                      "Ret 12m (%)":round(ret12m_p(pw,retornos)*100,2),
                      "Beta SPY":round(bspy,2), "Beta QQQ":round(bqqq,2)})
    for bm_nom, bmd in benchmarks.items():
        filas.append({"Portfolio":bm_nom,
                      "Retorno (%)":round(bmd["retorno_anual"]*100,2),
                      "Vol (%)":round(bmd["volatilidad_anual"]*100,2),
                      "Sharpe":round(bmd["sharpe"],2),
                      "CAGR (%)":round(bmd["cagr"]*100,2),
                      "Ret 12m (%)":round(bmd["retorno_12m"]*100,2),
                      "Beta SPY":1.0 if bm_nom=="SPY" else np.nan,
                      "Beta QQQ":1.0 if bm_nom=="QQQ" else np.nan})
    tabla_resumen = pd.DataFrame(filas)

# ── MÉTRICAS RÁPIDAS EN HEADER ────────────────────────────────
st.success(f"✅ Análisis completado — {len(tickers)} activos · {anios} años de historia")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Sharpe Óptimo",     f"{met_sharpe['sharpe']:.2f}",
          f"Ret {met_sharpe['retorno']*100:.1f}%")
c2.metric("Mín. Volatilidad",  f"{met_minvol['volatilidad']*100:.1f}%",
          f"Sharpe {met_minvol['sharpe']:.2f}")
c3.metric(f"Objetivo {retorno_objetivo*100:.0f}%",
          f"{met_objetivo['retorno']*100:.1f}%",
          f"Vol {met_objetivo['volatilidad']*100:.1f}%")
c4.metric("SPY Sharpe",
          f"{benchmarks['SPY']['sharpe']:.2f}" if 'SPY' in benchmarks else "N/A",
          f"Ret {benchmarks['SPY']['retorno_anual']*100:.1f}%" if 'SPY' in benchmarks else "")

st.divider()

# ── PESTAÑAS ─────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🎯 Markowitz", "⚖️ Pesos", "📊 CAGR & Rendimientos",
    "🔗 Correlación", "⚠️ VaR", "🔥 Stress Test"
])

# ══════════════════════════════════════════════════════
# TAB 1 — MARKOWITZ
# ══════════════════════════════════════════════════════
with tab1:
    st.subheader("Espacio de Portafolios (Markowitz)")
    st.caption("Cada punto es un portafolio aleatorio. El color indica su Ratio de Sharpe.")

    fig, ax = plt.subplots(figsize=(11, 6))
    sc = ax.scatter(sim_v, sim_r, c=sim_s, cmap="viridis",
                    alpha=0.45, s=7, zorder=1)
    plt.colorbar(sc, ax=ax, label="Sharpe Ratio")
    if len(fe_vols):
        ax.plot(fe_vols, fe_rets, "#2980b9", lw=2.5, zorder=2, label="Frontera Eficiente")
    cml_x = np.linspace(0, met_sharpe["volatilidad"]*1.3, 100)
    cml_y = rf + (met_sharpe["retorno"]-rf)/met_sharpe["volatilidad"] * cml_x
    ax.plot(cml_x, cml_y, "red", ls="--", lw=1.5, alpha=0.7, label="CML")
    ax.scatter(met_sharpe["volatilidad"],   met_sharpe["retorno"],
               marker="*",s=280,color="#f4d03f",zorder=5,
               edgecolors="black",lw=0.5,label="Máx Sharpe")
    ax.scatter(met_minvol["volatilidad"],   met_minvol["retorno"],
               marker="o",s=140,color="#e74c3c",zorder=5,
               edgecolors="black",lw=0.5,label="Mín Volatilidad")
    ax.scatter(met_objetivo["volatilidad"], met_objetivo["retorno"],
               marker="X",s=180,color="#27ae60",zorder=5,
               edgecolors="black",lw=0.5,label=f"Objetivo {retorno_objetivo*100:.1f}%")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f"{x:.0%}"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f"{x:.0%}"))
    ax.set_xlabel("Volatilidad anual"); ax.set_ylabel("Retorno anual")
    ax.legend(fontsize=9); ax.grid(True, alpha=0.25)
    agregar_watermark(ax)
    plt.tight_layout()
    st.pyplot(fig); plt.close()

    st.subheader("Resumen de métricas")
    st.dataframe(tabla_resumen, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════
# TAB 2 — PESOS
# ══════════════════════════════════════════════════════
with tab2:
    st.subheader("Composición de cada portafolio")

    def grafico_pesos(pesos, titulo, met, colores):
        pct = pesos * 100
        idx = np.argsort(pct)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, max(3.5, len(tickers)*0.6)),
                                        gridspec_kw={"width_ratios":[3,1]})
        ticks_ord  = [tickers[i] for i in idx]
        vals_ord   = [pct[i] for i in idx]
        cols_ord   = [colores[i % len(colores)] for i in idx]
        bars = ax1.barh(ticks_ord, vals_ord, color=cols_ord, edgecolor="white", lw=0.5)
        for bar in bars:
            v = bar.get_width()
            if v > 0.5:
                ax1.text(v+0.3, bar.get_y()+bar.get_height()/2,
                         f"{v:.1f}%", va="center", fontsize=9,
                         color=bar.get_facecolor(), fontweight="bold")
        ax1.set_xlim(0,105); ax1.set_title(titulo, fontsize=12, fontweight="bold")
        ax1.set_xlabel("Peso (%)"); ax1.grid(axis="x", alpha=0.3)
        ax1.spines[["top","right"]].set_visible(False)
        activos_t = sorted([(t,p,colores[tickers.index(t)%len(colores)])
                             for t,p in zip(tickers,pct) if p>0.1],
                           key=lambda x: -x[1])
        ax2.axis("off")
        if activos_t:
            tbl = ax2.table(
                cellText=[[t, f"{p:.2f}"] for t,p,_ in activos_t],
                colLabels=["Activo","Peso (%)"], cellLoc="center", loc="center")
            tbl.auto_set_font_size(False); tbl.set_fontsize(9); tbl.scale(1,1.5)
            tbl[0,0].set_facecolor("#2c3e50"); tbl[0,1].set_facecolor("#3498db")
            tbl[0,0].set_text_props(color="white",fontweight="bold")
            tbl[0,1].set_text_props(color="white",fontweight="bold")
            for ri,(_,_,c) in enumerate(activos_t):
                for ci in range(2): tbl[ri+1,ci].set_facecolor(c+"33")
        plt.figtext(0.02, 0.01,
                    f"Sharpe: {met['sharpe']:.2f}  Retorno: {met['retorno']*100:.2f}%  "
                    f"Vol: {met['volatilidad']*100:.2f}%", fontsize=9, color="#555")
        agregar_watermark(ax1)
        plt.tight_layout()
        return fig

    col1, col2 = st.columns(2)
    with col1:
        fig = grafico_pesos(pesos_sharpe, "Portfolio Óptimo Sharpe", met_sharpe, COLORES_ACTIVOS)
        st.pyplot(fig); plt.close()
    with col2:
        fig = grafico_pesos(pesos_minvol, "Portfolio Mínima Volatilidad", met_minvol, COLORES_ACTIVOS)
        st.pyplot(fig); plt.close()

    fig = grafico_pesos(pesos_objetivo, f"Portfolio Objetivo {retorno_objetivo*100:.1f}%",
                        met_objetivo, COLORES_ACTIVOS)
    st.pyplot(fig); plt.close()

# ══════════════════════════════════════════════════════
# TAB 3 — CAGR & RENDIMIENTOS ACUMULADOS
# ══════════════════════════════════════════════════════
with tab3:
    st.subheader("CAGR comparativo")

    cats, vals, cols_b = [], [], []
    for t in tickers:
        cats.append(t); vals.append(estadisticas.loc[t,"CAGR (%)"]); cols_b.append("#2980b9")
    for nom, pw in [("Sharpe Óptimo",pesos_sharpe),
                    ("Mín. Volatilidad",pesos_minvol),
                    (f"Objetivo {retorno_objetivo*100:.1f}%",pesos_objetivo)]:
        rd = retornos.dot(pw)
        cats.append(nom)
        vals.append((np.exp(rd.sum())**(DIAS_TRADING/len(rd))-1)*100)
        cols_b.append("#e67e22")
    for bm,bmd in benchmarks.items():
        cats.append(bm); vals.append(bmd["cagr"]*100); cols_b.append("#27ae60")

    fig, ax = plt.subplots(figsize=(13,5))
    bars = ax.bar(cats, vals, color=cols_b, edgecolor="white", lw=0.5)
    for bar,v in zip(bars,vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2,
                f"{v:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("CAGR (%)"); ax.grid(axis="y", alpha=0.3)
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels(cats, rotation=30, ha="right", fontsize=9)
    ax.spines[["top","right"]].set_visible(False)
    ax.legend(handles=[mpatches.Patch(color=c,label=l) for c,l in
                        [("#2980b9","Activo"),("#e67e22","Portfolio"),("#27ae60","Benchmark")]],
              fontsize=9)
    agregar_watermark(ax)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    st.subheader("Rendimientos acumulados")
    fig, ax = plt.subplots(figsize=(13,6))
    for pw,nom,col,ls,lw in [
        (pesos_sharpe,  "Sharpe Óptimo",  "#2980b9","-",2.5),
        (pesos_minvol,  "Mín. Volatilidad","#e67e22","-",2.0),
        (pesos_objetivo,f"Objetivo {retorno_objetivo*100:.1f}%","#27ae60","-",2.0),
    ]:
        rd = retornos.dot(pw)
        ax.plot(rd.index, (np.exp(rd.cumsum())-1)*100, label=nom, color=col, ls=ls, lw=lw)
    for bm,col,ls in [("SPY","#e74c3c","--"),("QQQ","#9b59b6","--")]:
        if bm in benchmarks:
            brd = benchmarks[bm]["retornos"].reindex(retornos.index).fillna(0)
            ax.plot(brd.index, (np.exp(brd.cumsum())-1)*100, label=bm, color=col, ls=ls, lw=1.8)
    ax.axhline(0, color="gray", ls=":", lw=0.8, alpha=0.5)
    ax.set_ylabel("Retorno acumulado (%)"); ax.set_xlabel("Fecha")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f"{x:.0f}%"))
    ax.legend(fontsize=10); ax.grid(True, alpha=0.2)
    ax.spines[["top","right"]].set_visible(False)
    agregar_watermark(ax)
    plt.tight_layout(); st.pyplot(fig); plt.close()

# ══════════════════════════════════════════════════════
# TAB 4 — CORRELACIÓN
# ══════════════════════════════════════════════════════
with tab4:
    st.subheader("Matriz de correlación entre activos")
    fig, ax = plt.subplots(figsize=(max(6, len(tickers)*1.0), max(5, len(tickers)*0.85)))
    sns.heatmap(matriz_corr, annot=True, fmt=".2f", cmap="RdBu_r",
                vmin=-1, vmax=1, center=0, square=True, linewidths=0.5,
                ax=ax, cbar_kws={"label":"Correlación","shrink":0.8},
                annot_kws={"size":10})
    for i in range(len(tickers)):
        for j in range(len(tickers)):
            if i != j and matriz_corr.iloc[i,j] > UMBRAL_CORR:
                ax.add_patch(plt.Rectangle((j,i),1,1,
                             fill=False, edgecolor="red", lw=2.5, zorder=3))
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    agregar_watermark(ax, alpha=0.08)
    plt.tight_layout(); st.pyplot(fig); plt.close()

    pares = [(tickers[i],tickers[j],matriz_corr.iloc[i,j])
             for i in range(len(tickers)) for j in range(i+1,len(tickers))
             if matriz_corr.iloc[i,j] > UMBRAL_CORR]
    if pares:
        st.error(f"❌ Diversificación insuficiente — pares con correlación > {UMBRAL_CORR:.0%}:")
        for t1,t2,c in pares:
            st.write(f"  • **{t1} — {t2}**: correlación {c:.2f}")
    else:
        st.success(f"✅ Diversificación OK: ningún par supera {UMBRAL_CORR:.0%}.")

# ══════════════════════════════════════════════════════
# TAB 5 — VaR
# ══════════════════════════════════════════════════════
with tab5:
    st.subheader("Value at Risk (VaR) 95%")
    st.caption("El VaR responde: con 95% de confianza, ¿cuánto puedo perder en 1 día como máximo?")

    port_var = {
        "Sharpe Óptimo":    pesos_sharpe,
        "Mínima Volatilidad": pesos_minvol,
        f"Objetivo {retorno_objetivo*100:.1f}%": pesos_objetivo,
        "SPY": None,
    }
    res_var = {}
    for nom, pw in port_var.items():
        if pw is not None:
            rd = retornos.dot(pw)
        elif "SPY" in benchmarks:
            rd = benchmarks["SPY"]["retornos"].reindex(retornos.index).dropna()
        else:
            continue
        v1d  = abs(np.percentile(rd, 5)) * 100
        res_var[nom] = {"rd": rd, "v1d": v1d, "v10d": v1d*np.sqrt(10)}

    # Tabla VaR
    df_var = pd.DataFrame({
        "Portfolio":       list(res_var.keys()),
        "VaR 1 día (%)":  [round(v["v1d"],2)  for v in res_var.values()],
        "VaR 10 días (%)": [round(v["v10d"],2) for v in res_var.values()],
    })
    st.dataframe(df_var, use_container_width=True, hide_index=True)

    # Histogramas
    n_p   = len(res_var)
    n_c   = 2
    n_r   = (n_p+1)//2
    cols_h = ["#2980b9","#e74c3c","#27ae60","#e67e22"]
    fig, axes = plt.subplots(n_r, n_c, figsize=(13, n_r*4))
    axes = axes.flatten()
    for idx,(nom,dat) in enumerate(res_var.items()):
        ax  = axes[idx]
        ret = dat["rd"]*100
        var = dat["v1d"]
        col = cols_h[idx%len(cols_h)]
        ax.hist(ret, bins=60, density=True, color=col, alpha=0.6,
                edgecolor="white", lw=0.3)
        kde_x = np.linspace(ret.min(), ret.max(), 300)
        ax.plot(kde_x, stats.gaussian_kde(ret)(kde_x), color=col, lw=1.8)
        ax.axvline(-var, color=col, ls="--", lw=2)
        ylim = ax.get_ylim()[1]
        ax.text(-var-0.1, ylim*0.82, f"VaR\n{var:.2f}%",
                ha="right", fontsize=9, color=col, fontweight="bold")
        ax.set_title(f"Rend. diario & VaR: {nom}", fontsize=10, fontweight="bold")
        ax.set_xlabel("Retorno diario (%)"); ax.set_ylabel("Densidad")
        ax.grid(True, alpha=0.2); ax.spines[["top","right"]].set_visible(False)
    for idx in range(n_p, len(axes)):
        axes[idx].set_visible(False)
    plt.tight_layout(); st.pyplot(fig); plt.close()

# ══════════════════════════════════════════════════════
# TAB 6 — STRESS TEST
# ══════════════════════════════════════════════════════
with tab6:
    st.subheader("Stress Testing")
    st.caption("Estimación de pérdidas usando beta como medida de sensibilidad al mercado.")

    def obtener_beta(nom):
        fila = tabla_resumen[tabla_resumen["Portfolio"]==nom]
        if fila.empty: return 1.0
        b = fila["Beta SPY"].values[0]
        return b if not pd.isna(b) else 1.0

    noms_st = ["Sharpe Óptimo","Mínima Volatilidad",
               f"Objetivo {retorno_objetivo*100:.1f}%","SPY"]
    betas_st = {n: obtener_beta(n) for n in noms_st}
    betas_st["SPY"] = 1.0

    # Caídas hipotéticas
    st.markdown("#### Caídas hipotéticas del SPY")
    caidas = [-0.05,-0.10,-0.20]
    filas_st = []
    for nom in noms_st:
        fila = {"Portfolio": nom}
        for c in caidas:
            fila[f"SPY {c*100:.0f}%"] = f"{betas_st[nom]*c*100:.2f}%"
        filas_st.append(fila)
    df_st = pd.DataFrame(filas_st)

    # Estilo con colores
    def colorear(val):
        try:
            v = float(val.replace("%",""))
            intensity = min(abs(v)/25, 1.0)
            r = 255; g = int(255*(1-intensity*0.65)); b = int(255*(1-intensity*0.65))
            return f"background-color: rgb({r},{g},{b})"
        except Exception:
            return ""

    cols_num = [c for c in df_st.columns if c != "Portfolio"]
    st.dataframe(
        df_st.style.applymap(colorear, subset=cols_num),
        use_container_width=True, hide_index=True
    )
    st.caption("Caída estimada = beta × caída SPY. Más rojo = mayor pérdida estimada.")

    # Crisis históricas
    st.markdown("#### Crisis históricas")
    CRISIS = {"Crisis 2008 (Lehman)": -0.09, "COVID-19 Crash": -0.12}
    filas_cr = []
    for nom in noms_st:
        fila = {"Portfolio": nom}
        for cn, cv in CRISIS.items():
            fila[cn] = f"{betas_st[nom]*cv*100:.2f}%"
        filas_cr.append(fila)
    df_cr = pd.DataFrame(filas_cr)
    cols_cr = [c for c in df_cr.columns if c != "Portfolio"]
    st.dataframe(
        df_cr.style.applymap(colorear, subset=cols_cr),
        use_container_width=True, hide_index=True
    )
    st.caption("Basado en la caída del SPY en el peor día de cada crisis. Solo efecto beta.")

# ── FOOTER ───────────────────────────────────────────────────
st.divider()
logo_b64_footer = logo_a_base64("logo_sidebar.png")
if logo_b64_footer:
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:12px; opacity:0.5;">'
        f'<img src="data:image/png;base64,{logo_b64_footer}" style="height:36px;">'
        f'<span style="font-size:11px; color:gray;">LHA · Portfolio Optimizer</span>'
        f'</div>',
        unsafe_allow_html=True
    )
st.caption("⚠️ Este análisis es solo educativo y no constituye asesoramiento financiero. "
           "Retornos pasados no garantizan resultados futuros.")
