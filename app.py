import streamlit as st
from backend_supabase import obtener_empleados_dict_y_lista

# ========================
# CONFIGURACIÓN
# ========================
st.set_page_config(page_title="Registro de horas", layout="centered")

# ========================
# ESTILOS (CSS)
# ========================
st.markdown("""
    <style>
    body {
        background-color: #0F1F4B;
    }
    .main {
        background-color: #0F1F4B;
        color: white;
    }
    h1 {
        color: #FFFFFF;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ========================
# LOGO
# ========================
col1, col2 = st.columns([1, 3])

with col1:
    st.image("Logo-Datateam.png", width=400)

with col2:
    st.markdown(
        """
        <div style="display: flex; align-items: center; height: 100%;">
            <h1 style="margin: 0;">Registro de horas</h1>
        </div>
        """,
        unsafe_allow_html=True
    )



# ========================
# CARGAR DATOS
# ========================
url = "https://aeqhmvnfqrudxukbhjzs.supabase.co"
key = "TU_API_KEY"

empleados_dict, nombres_lista = obtener_empleados_dict_y_lista(url, key)

# ========================
# AUTOCOMPLETE (SIMULADO)
# ========================
st.subheader("Nombre del empleado")

input_nombre = st.text_input("Escribe al menos 3 letras:")

opciones_filtradas = []

if len(input_nombre) >= 3:
    opciones_filtradas = [
        nombre for nombre in nombres_lista
        if input_nombre.lower() in nombre.lower()
    ]

# Dropdown dinámico
nombre_seleccionado = st.selectbox(
    "Selecciona tu nombre:",
    opciones_filtradas if opciones_filtradas else ["Sin resultados"]
)

# ========================
# MOSTRAR ID (DEBUG)
# ========================
if nombre_seleccionado and nombre_seleccionado != "Sin resultados":
    id_empleado = empleados_dict.get(nombre_seleccionado)
    st.success(f"ID empleado: {id_empleado}")
