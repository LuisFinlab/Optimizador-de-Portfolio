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

warnings.filterwarnings("ignore")

# ── CONFIGURACIÓN DE PÁGINA ──────────────────────────────────
st.set_page_config(
    page_title="Portfolio Optimizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── MARCA DE AGUA ───────────────────────────────────────────
def agregar_marca_agua():
    _logo = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wgARCAH0AfQDASIAAhEBAxEB/8QAGQABAAMBAQAAAAAAAAAAAAAAAAMEBQIB/8QAGAEBAQEBAQAAAAAAAAAAAAAAAAECAwT/2gAMAwEAAhADEAAAAsUbwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALkVPNXKULAAAAAAAAAAAAAAAAAAAAAAAAAAAB6eS2buNRTHLVbM0c7rgNwAAAAAAAAAAAAAAAAAAAAAAAAAAXoraUnvLYYoFPPvUe+A1AAAAE8FmOfNKTnvJa3hlRW6nTPgsAAk6aGLntZnWS1qtlDjvjpkDqSO1LC1feeslrRpmRTwdMhQAD3y/FPnbpZ1QG8y2KSW7JnXs28OOgM+nbqejAWAAAAAWdPJ1uW1O5QikO2AAAHXI3HHfn6c4utk9chvIAGlao3uG2XqY2nA64AAAbObq89I5HPWGmh9HMDvYrWuOxWza13I67YsVZI7AoAAAACbWydbltn6GfFMdsAAAAbPfHfn6QZWrldchvIAF2/Qv8dsfYx7Ix1yAAPTR4tY/PW2r2OeqeftYvXKzFrJ0OO/MixT7ZDeQAAAAAAJtbJ1uW2foZ8Ux2wAAABs98d+fpBlauV1yG8gAXb9C/wAdsfYx7Ix1yAAtVdTNjz5YqsamHfxbWZ3oS+SGKr95W5yOuAAAAAAAAJtbJ1uW2foZ8Ux2wAAAPTY6zuuO58y/7qZ7Q51KK5xVZPxZZv5E/PWhj26RyOmQAOtTMkzYFqwULtv3noMVHxmbnvB2wAAAAAAAABNrZOty2z9DPimO2AAHcmnm1bfrjsIAAAAc9Kj4nFXy2qn7bFXuccdkBBxU0u0oNHUrUdvMsrDpkAAAAAAAACbWydbltn6GfFMdsAJo9fN69OO0VSnvN3y1NLmV9XJ6Z66jak/dVF3vPS6nVO1jUnVagbTD6s2mMjZYlhb8eW1LsELUCyTYw9fnqWvYc9Ybvj0cwAAAAAAAAJtbK1eW2foUIpDtgTlq2efoz7OVvIdc68vPXn6R4+zjdMh0yABevUrvHbH2MqoB1wB1rVJueswdMgALtKSNgefpRo7OP2x4NwAAAAAAB75ciezQc93+KaI47DeeNCil0GfzmxRHbC7BNm6DPc9aFDxVTyzW64ATc2pbnVFy1erwil5bqdcLPk0t2GBz1S8vU+ueRYAm6mzbyi56vVYxS8t1OuAoAAAAAAsRxGkVGn4iN0rlN7ECRUaXwjT8RGk8rhPCeJozlPxEaT2okgjTcxG7kqBNyRpuSNII08J4njOEvUQJuajSCNJGAAAAAAOuRcU+s23HWVb9po7nrLJpKnq2vaaLXVNVr2oJvYCXa8RbXEAse1iW+K5bSqLaoJe65LimlsqyrXtQXIIiW+axZZapLnNUtiSmLdQQKAAAAAAAAWqskTecJZPIx3z5zU8TgsdwIk845JfOPTyxW6JofOC/DEl7546s7948O4uo6t8cc5O4JdJOfOo9Q9kvMY7rTQ2BQAAAAAAAAAAAAAAAAE/lnjGq/lviyv5aFX2x0U5+bRRTylOTiyReTIgitVdQKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIAAwAAACH777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777779T7777777777777777777777777777rS3/wC++++++++++++++++++++++++++7pDfe++u++7KW8+++jAFd+kKT/+++vM+ssr30++++++YZ++++6pc+++LG++++5R9+CHZf8AvvvvvqPfvvvvgfvvvoQ/vvvlb9pwzvvvvvvvvqFfvvvvofvvvgQ/vvq/HotaPvvvvvvvvqHfvvvuv+t9NSTvvvodmg1vvvvvvvvvvqNfvvqYgzwww8Q4osIQxEB/vvvvvvvvvqPfvvYRy1TT33OPc6rLPuY/vvvvvvvvvqPfuY3/AKN7774WL76H777stP77777777OAPO0vy0N536AEL/kLL77+EL/7777777PnfLPHHfXX3fXn/XHXHXXPnH777777774z4Mi4xx8yy2xzy97wy1y+xz/777777776vE1ggWWKb6JaGS/xHlHf7777777777777777754mnEGbpvf77777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777577777777777576L7777777/2gAMAwEAAgADAAAAEAgggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggj6Aggggggggggggggggggggggggggggzcowggggggggggggggggggggggggggizf4wQgkgggVLCgggv/uqgnfLywgglUQokly6QgggggrYQggglXUQggl7AgggjfQgj+EYwgggggvlgggggvqAggvqwgggyWBC/wAgggggggvvgggggnqAggvqwgglKIzCSQggggggggvtgggghypyACP7wggghR37wQggggggggvngggjb/wDP/wD/AHXvPPXf86bAgggggggggvlggkma3sokcIU/Q6EsgxnAQggggggggvlggnswtCwggmSAgtwgggdzQgggggggi8YAadI5vMIAnXry/jyAgkHf6wggggggjwghSziCghBDjDDjCABgjCjDgQggggggVcIyci0IA8sg8oAMwwgM0MQIIggggggggggxhmHCRkQTYMZMF5FMkKQggggggggggggggggghEmlhrcw4Qgggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggogggggggggggogngggggggv/EADkRAAEDAgIGBgkEAgMAAAAAAAEAAgMEESExEhMgQVHwEBQiMjOBBSMwYXGxweHxQFKh0YCRFUJD/9oACAECAQE/AP8ABySVkYu4qCbWgutb9dPWhvZjxKc9zjdxVCPVfrJZWRi7ip6p8uGQ6aMepHO/al1v/nbzRrZWmzgLrr8nAKF0rsZABsTyzR42BC6/JwCjq5pDotaEzSt2s+iV0zcWAFdfk4BNrpXGwAUesI7dtiaXVMLlDW6x4aRa/Q+CN5u4KeCCNhdbppR6lu3XgCQH3KkAMwvskAixRFjZejx2CffsVQtM4BUDQXk7NfJchgTSWkEJjg5ocN/RWTab9EZBRsL3BoUtIx7QBgQoWlsYaduv8QfBUfjDaf3iqDwz8foNis8Y87l6P7ztmBgnkdI7Ln6KRhY4tO5U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"
    st.markdown(f"""
    <style>
    .wm-logo {{
        position: fixed;
        bottom: 55px;
        right: 25px;
        z-index: 9999;
        opacity: 0.13;
        pointer-events: none;
    }}
    .wm-logo img {{
        width: 150px;
    }}
    .wm-footer {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(13, 27, 62, 0.88);
        color: #b8a96a;
        text-align: center;
        padding: 5px 0 6px 0;
        font-size: 12px;
        z-index: 9999;
        letter-spacing: 0.4px;
        font-family: sans-serif;
    }}
    .wm-footer a {{
        color: #b8a96a;
        text-decoration: none;
        margin: 0 10px;
    }}
    .wm-footer a:hover {{ color: #fff; }}
    </style>
    <div class="wm-logo">
        <img src="data:image/jpeg;base64,{_logo}" />
    </div>
    <div class="wm-footer">
        📧 <a href="mailto:lhaasesor@gmail.com">lhaasesor@gmail.com</a>
        &nbsp;·&nbsp;
        📸 <a href="https://www.instagram.com/lha.asesorfinanciero/" target="_blank">@lha.asesorfinanciero</a>
        &nbsp;·&nbsp;
        LHA — Agente y Operador CNV · Matrícula Nro 2593
    </div>
    """, unsafe_allow_html=True)

agregar_marca_agua()


st.title("📈 Optimizador de Portafolios — Markowitz")
st.caption("Análisis cuantitativo de riesgo y retorno con frontera eficiente")

# ── SIDEBAR: INPUTS DEL USUARIO ──────────────────────────────
with st.sidebar:
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
tickers = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()][:20]

fecha_fin    = datetime.date.today()
fecha_inicio = fecha_fin - datetime.timedelta(days=int(anios * 365.25))

with st.spinner("📡 Descargando datos históricos..."):
    raw = yf.download(tickers, start=fecha_inicio, end=fecha_fin,
                      auto_adjust=True, progress=False)
    if isinstance(raw.columns, pd.MultiIndex):
        precios = raw["Close"]
    else:
        precios = raw[["Close"]]
        precios.columns = tickers

    # ✅ FIX 1: ZeroDivisionError — verificar que hay datos antes de filtrar
    total_dias = len(precios)
    if total_dias == 0:
        st.error("❌ No se pudieron obtener datos históricos. "
                 "Verificá que los tickers sean válidos (ej: AAPL, MSFT) "
                 "o intentá con otro período.")
        st.stop()

    validos = [t for t in precios.columns
               if precios[t].dropna().__len__() / total_dias >= 0.8
               and precios[t].dropna().__len__() > 30]

    descartados = [t for t in precios.columns if t not in validos]
    if descartados:
        st.warning(f"⚠️ Activos descartados por datos insuficientes: {', '.join(descartados)}")

    if len(validos) < 2:
        st.error("❌ Se necesitan al menos 2 activos válidos. Revisá los tickers.")
        st.stop()

    precios  = precios[validos].ffill().dropna()
    tickers  = validos
    retornos = np.log(precios / precios.shift(1)).dropna()

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
    plt.tight_layout()
    st.pyplot(fig); plt.close()

    st.subheader("Resumen de métricas")
    # ✅ FIX 2: use_container_width reemplazado por width='stretch'
    st.dataframe(tabla_resumen, width='stretch', hide_index=True)

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
    # ✅ FIX 2: use_container_width reemplazado por width='stretch'
    st.dataframe(df_var, width='stretch', hide_index=True)

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

    # ✅ FIX 3: applymap deprecado → reemplazado por map (pandas >= 2.1)
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
        df_st.style.map(colorear, subset=cols_num),
        width='stretch', hide_index=True
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
        df_cr.style.map(colorear, subset=cols_cr),
        width='stretch', hide_index=True
    )
    st.caption("Basado en la caída del SPY en el peor día de cada crisis. Solo efecto beta.")

# ── FOOTER ───────────────────────────────────────────────────
st.divider()
st.caption("⚠️ Este análisis es solo educativo y no constituye asesoramiento financiero. "
           "Retornos pasados no garantizan resultados futuros.")
