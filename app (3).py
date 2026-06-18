import streamlit as st
import math
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Calculadora Puente Warren - UNICA", layout="centered")

# Inicializar sesión
if 'ingresado' not in st.session_state:
    st.session_state.ingresado = False

# ============================
# PANTALLA DE HOME (INICIO)
# ============================
if not st.session_state.ingresado:
    # Logo esquina superior derecha
    try:
        logo_uni = Image.open("logo.png")
        col1, col2 = st.columns([4, 1])
        with col2: st.image(logo_uni, width=100)
    except: pass

    st.markdown("<h1 style='text-align: center;'>Proyecto Integrador</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Análisis Estructural: Armaduras Warren</h3>", unsafe_allow_html=True)
    st.markdown("---")

    # Imagen central
    try:
        img_central = Image.open("Gemini_Generated_Image_eui7skeui7skeui7.png")
        st.image(img_central, use_container_width=True)
    except:
        st.warning("⚠️ Sube la imagen 'Gemini_Generated_Image_eui7skeui7skeui7.png'")

    st.write("##")
    if st.button("INGRESAR A LA CALCULADORA", use_container_width=True):
        st.session_state.ingresado = True
        st.rerun()

# ============================
# PANTALLA DE LA CALCULADORA
# ============================
else:
    # Sidebar con logo y botón volver
    try:
        logo_side = Image.open("logo.png")
        st.sidebar.image(logo_side, width=80)
    except: pass

    if st.sidebar.button("⬅️ Volver al Inicio"):
        st.session_state.ingresado = False
        st.rerun()

    st.title("🏗️ Calculadora de Armadura Tipo Warren")
    st.caption("Análisis Estructural | Método de Secciones | UNICA")

    # --- LÓGICA DEL MOTOR (EXTRAÍDA DEL NOTEBOOK) ---
    class WarrenTruss:
        def __init__(self, L, H, panels, P_total):
            self.L, self.H, self.panels, self.P_total = L, H, panels, P_total
            self._analyze()

        def _analyze(self):
            L, H, n, Pt = self.L, self.H, self.panels, self.P_total
            d = L / n
            diag_len = math.hypot(d, H)
            sin_a = H / diag_len
            Ra = Rb = Pt / 2

            # Cortantes
            load_nodes = n - 1
            P_node = Pt / load_nodes if load_nodes > 0 else Pt
            V, shear = [], Ra
            for i in range(n):
                V.append(shear)
                if i < load_nodes: shear -= P_node

            members = []
            # Cordon Superior
            for i in range(n):
                x_mid = (i + 0.5) * d
                M = Ra * x_mid - sum(P_node * (j * d) for j in range(1, i + 1) if j * d < x_mid)
                members.append({"id": f"CS{i+1}", "name": f"Cordon Sup {i+1}", "type": "Compresión", "force": -M/H if H!=0 else 0, "length": d})
            # Cordon Inferior
            for i in range(n):
                x_right = (i + 1) * d
                M = Ra * x_right - sum(P_node * (j * d) for j in range(1, i + 1) if j * d < x_right)
                members.append({"id": f"CI{i+1}", "name": f"Cordon Inf {i+1}", "type": "Tensión", "force": M/H if H!=0 else 0, "length": d})
            # Diagonales
            for i in range(n):
                members.append({"id": f"D{i+1}", "name": f"Diagonal {i+1}", "type": "Var.", "force": V[i]/sin_a, "length": diag_len})

            self.results = {"Ra": Ra, "members": members, "d": d, "angle": math.degrees(math.atan2(H, d)), "P_node": P_node}

def evaluate_safety(members, mat, area_cm2):
    Fy = {"Acero A36": 250, "Acero A572": 345, "Aluminio 6061": 276}.get(mat, 250)
    adm = Fy / 1.67
    A_mm2 = area_cm2 * 100
    rows = []
    for m in members:
        stress = (abs(m["force"]) * 1000) / A_mm2
        status = "✅ SEGURO" if stress < adm else "❌ FALLA"
        color = "safe" if status == "✅ SEGURO" else "danger"
        rows.append({**m, "Esfuerzo (MPa)": round(stress, 2), "Admisible (MPa)": round(adm, 1), "Estado": status, "color": color})
    return rows, adm

    # Sidebar Entradas
    st.sidebar.header("Parámetros")
    with st.sidebar.form("input_form"):
        L = st.number_input("Longitud L (m)", value=20.0, step=1.0)
        H = st.number_input("Altura H (m)", value=3.0, step=0.5)
        n = st.slider("Paneles", 2, 12, 6)
        P = st.number_input("Carga P (kN)", value=500.0, step=50.0)
        A_cm2 = st.number_input("Área (cm²)", value=50.0, step=5.0)
        mat = st.selectbox("Material", ["Acero A36", "Acero A572", "Aluminio 6061"])
        btn = st.form_submit_button("CALCULAR ESTRUCTURA")

    if btn:
        truss = WarrenTruss(L, H, n, P)
        res = truss.results
        eval_rows, adm = evaluate_safety(res["members"], mat, A_cm2)

        t1, t2, t3 = st.tabs(["📊 Resumen", "📋 Tabla Detallada", "📈 Diagrama Warren"])

        with t1:
            verdict = "PELIGROSO" if any(x["Estado"] == "❌ FALLA" for x in eval_rows) else "SEGURO"
            if verdict == "SEGURO": st.success(f"### ESTADO: {verdict}")
            else: st.error(f"### ESTADO: {verdict}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Reacciones Ra/Rb", f"{res['Ra']} kN")
            c2.metric("Ángulo", f"{res['angle']:.1f}°")
            c3.metric("Carga p/ Nodo", f"{res['P_node']:.1f} kN")

            st.divider()
            st.subheader("💡 Recomendaciones")
            if verdict == "PELIGROSO":
                st.info(f"Aumentar área transversal o usar material con Fy > {mat}")
            if H/L < 0.1:
                st.warning("La altura es baja para esta longitud (relación H/L < 0.10)")

        with t2:
            df = pd.DataFrame(eval_rows)
            st.dataframe(df[["id", "name", "type", "force", "Esfuerzo (MPa)", "Admisible (MPa)", "Estado"]], use_container_width=True)

        with t3:
            fig, ax = plt.subplots(figsize=(10, 4))
            d = res["d"]
            for i in range(n):
                # Inferior (Azul)
                ax.plot([i*d, (i+1)*d], [0, 0], color='blue', lw=3)
                # Superior (Rojo)
                ax.plot([i*d, (i+1)*d], [H, H], color='red', lw=3)
                # Diagonales (Verde)
                if i % 2 == 0: ax.plot([i*d, (i+1)*d], [0, H], color='green', lw=2)
                else: ax.plot([i*d, (i+1)*d], [H, 0], color='green', lw=2)

            # Nodos
            for i in range(n+1):
                ax.scatter(i*d, 0, color='blue', zorder=5)
                ax.scatter(i*d, H, color='red', zorder=5)

            ax.set_aspect('equal')
            ax.axis('off')
            st.pyplot(fig)
            st.caption("Azul: Inf | Rojo: Sup | Verde: Diagonales")
