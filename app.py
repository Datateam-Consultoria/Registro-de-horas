import streamlit as st
from supabase import create_client, Client
from streamlit_searchbox import st_searchbox
from backend_supabase import (
    obtener_empleados_dict_y_lista,
    obtener_proyectos_dict_y_lista,
    obtener_actividades_dict_y_lista,
    insertar_registro_horas
)
from datetime import date, datetime, time, timedelta
import time as time_module

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="Registro de horas", layout="centered")

# ========================
# HEADER
# ========================
col1, col2 = st.columns([1, 3])
with col1:
    st.image("Logo-Datateam.png", width=300)
with col2:
    st.markdown("<h1>Registro de horas</h1>", unsafe_allow_html=True)

st.markdown("---")

# ========================
# SESSION STATE
# ========================
if "registros" not in st.session_state:
    st.session_state.registros = []
if "ultimo_resumen" not in st.session_state:
    st.session_state.ultimo_resumen = None

# ========================
# SUPABASE
# ========================
@st.cache_resource
def get_supabase_client() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = get_supabase_client()

# ========================
# CATALOGOS
# ========================
@st.cache_data
def cargar_catalogos():
    emp_d, emp_l = obtener_empleados_dict_y_lista(supabase)
    proy_d, proy_l = obtener_proyectos_dict_y_lista(supabase)
    act_d, act_l = obtener_actividades_dict_y_lista(supabase)
    return emp_d, emp_l, proy_d, proy_l, act_d, act_l

emp_d, emp_l, proy_d, proy_l, act_d, act_l = cargar_catalogos()
id_to_act  = {v: k for k, v in act_d.items()}
id_to_proy = {v: k for k, v in proy_d.items()}

# ========================
# CONSTANTES
# ========================
ID_PROYECTO   = 1   # actividad Proyecto
ID_ASIGNACION = 4   # actividad Asignacion (ajusta si tu BD usa otro id)
ID_SOPORTE    = 6   # actividad Soporte

# Actividades que muestran selector de proyecto (ids 1, 4 y 6)
ID_ACTIVIDADES_CON_PROYECTO = (1, 5, 6)

ID_PROYECTO_OTRO    = 20   # proyecto "Otro": habilita nombre manual
ID_PROYECTO_NINGUNO = 0    # excluido del selector; asignado automaticamente a actividades sin proyecto

# Lista de proyectos para el selector (sin el id 0)
proy_l_filtrada = [n for n, pid in proy_d.items() if pid != ID_PROYECTO_NINGUNO]

# ========================
# FECHAS DEFAULT LUNES - VIERNES
# ========================
today   = date.today()
lunes   = today - timedelta(days=today.weekday())
viernes = lunes + timedelta(days=4)

# ========================
# BUSCADOR EMPLEADO
# ========================
def buscar_nombres(s):
    if len(s) < 3:
        return []
    return [n for n in emp_l if s.lower() in n.lower()]

st.subheader("Nombre del empleado")
nombre      = st_searchbox(buscar_nombres, key="nombre")
id_empleado = emp_d.get(nombre) if nombre else None

# ========================
# CONTADOR TOTAL DE HORAS
# ========================
def calcular_horas_totales():
    total = 0
    for i, r in enumerate(st.session_state.registros):
        act_id = r["actividad_id"]
        if act_id == ID_SOPORTE:
            fecha  = st.session_state.get(f"f_{i}", today)
            h_i    = st.session_state.get(f"ti_{i}", time(9, 0))
            h_f    = st.session_state.get(f"tf_{i}", time(10, 0))
            inicio = datetime.combine(fecha, h_i)
            fin    = datetime.combine(fecha, h_f)
            if fin > inicio:
                total += (fin - inicio).total_seconds() / 3600
        else:
            total += st.session_state.get(f"h_{i}", 0)
    return total

# ========================
# AGREGAR ACTIVIDAD
# ========================
def agregar():
    val = st.session_state.sel_act
    if val != "Seleccionar...":
        st.session_state.registros.append({"actividad_id": act_d[val]})
        st.session_state.sel_act = "Seleccionar..."

# ========================
# RESUMEN DEL ULTIMO GUARDADO
# ========================
if st.session_state.ultimo_resumen:
    resumen = st.session_state.ultimo_resumen
    st.success("Registros guardados correctamente")
    with st.expander("Ver resumen de lo guardado", expanded=True):
        st.markdown(f"**Empleado:** {resumen['empleado']}")
        st.markdown(f"**Fecha de guardado:** {resumen['fecha_guardado']}")
        st.markdown(f"**Total de horas registradas:** {resumen['total_horas']:.2f}h")
        st.markdown("---")
        for idx, item in enumerate(resumen['items'], 1):
            st.markdown(f"**{idx}. {item['actividad']}**")
            cols = st.columns(3)
            with cols[0]:
                st.markdown(f"Proyecto: {item['proyecto']}")
            with cols[1]:
                st.markdown(f"Horas: {item['horas']:.2f}h")
            with cols[2]:
                st.markdown(f"Periodo: {item['periodo']}")
            if item['nombre_act']:
                st.markdown(f"Nombre actividad: {item['nombre_act']}")
            if item['descripcion']:
                st.markdown(f"Descripcion: {item['descripcion']}")
            if idx < len(resumen['items']):
                st.markdown("---")
    if st.button("Registrar mas horas"):
        st.session_state.ultimo_resumen = None
        st.rerun()
    st.stop()

# ========================
# FORM DINAMICO
# ========================
for i, r in enumerate(st.session_state.registros):

    st.markdown("---")
    act_id     = r["actividad_id"]
    act_nombre = id_to_act[act_id]
    st.markdown(f"### {act_nombre}")

    # -------- SOPORTE (id 6): fecha puntual + selector de proyecto --------
    if act_id == ID_SOPORTE:

        fecha = st.date_input("Fecha *", value=today, key=f"f_{i}")

        col1, col2 = st.columns(2)
        with col1:
            h_i = st.time_input("Inicio *", value=time(9, 0), key=f"ti_{i}", step=3600)
        with col2:
            h_f = st.time_input("Fin *", value=time(10, 0), key=f"tf_{i}", step=3600)

        inicio = datetime.combine(fecha, h_i)
        fin    = datetime.combine(fecha, h_f)

        horas = 0
        if fin > inicio:
            horas = (fin - inicio).total_seconds() / 3600
            st.info(f"Duracion: {round(horas, 2)}h")
        else:
            st.warning("La hora de fin debe ser mayor a la de inicio")

        proyecto    = st.selectbox("Proyecto *", proy_l_filtrada, key=f"p_{i}")
        proy_id_sel = proy_d.get(proyecto)

        if proy_id_sel == ID_PROYECTO_OTRO:
            nombre_act = st.text_input("Nombre actividad *", key=f"n_{i}")
        else:
            nombre_act = proyecto

        desc = st.text_input("Descripcion", key=f"d_{i}")

    # -------- IDs 1 y 4: rango de fechas + selector de proyecto --------
    elif act_id in ID_ACTIVIDADES_CON_PROYECTO:

        col1, col2 = st.columns(2)
        with col1:
            fi = st.date_input("Inicio *", value=lunes, key=f"fi_{i}")
        with col2:
            ff = st.date_input("Fin *", value=viernes, key=f"ff_{i}")

        proyecto    = st.selectbox("Proyecto *", proy_l_filtrada, key=f"p_{i}")
        proy_id_sel = proy_d.get(proyecto)
        horas       = st.number_input("Horas *", min_value=0.0, step=1.0, key=f"h_{i}")

        if proy_id_sel == ID_PROYECTO_OTRO:
            nombre_act = st.text_input("Nombre proyecto *", key=f"n_{i}")
        else:
            nombre_act = proyecto  # automatico

        desc = st.text_input("Descripcion", key=f"d_{i}")

        inicio = datetime.combine(fi, time(9, 0))
        fin    = datetime.combine(ff, time(18, 0))

    # -------- OTROS: proyecto siempre id 0, sin selector --------
    else:

        col1, col2 = st.columns(2)
        with col1:
            fi = st.date_input("Inicio *", value=lunes, key=f"fi_{i}")
        with col2:
            ff = st.date_input("Fin *", value=viernes, key=f"ff_{i}")

        # Proyecto fijo id 0, no se muestra selector
        proyecto    = id_to_proy.get(ID_PROYECTO_NINGUNO, "")
        proy_id_sel = ID_PROYECTO_NINGUNO

        horas      = st.number_input("Horas *", min_value=0.0, step=1.0, key=f"h_{i}")
        nombre_act = st.text_input("Nombre actividad *", key=f"n_{i}")
        desc       = st.text_input("Descripcion", key=f"d_{i}")

        inicio = datetime.combine(fi, time(9, 0))
        fin    = datetime.combine(ff, time(18, 0))

    # Persistir en session_state
    st.session_state.registros[i] = {
        "actividad_id": act_id,
        "proyecto":     proyecto,
        "proy_id":      proy_id_sel if act_id in ID_ACTIVIDADES_CON_PROYECTO else ID_PROYECTO_NINGUNO,
        "horas":        horas,
        "nombre":       nombre_act,
        "desc":         desc,
        "inicio":       inicio,
        "fin":          fin,
    }

    if st.button("Eliminar", key=f"del_{i}"):
        st.session_state.registros.pop(i)
        st.rerun()

# ========================
# CONTADOR HORAS TOTAL
# ========================
if st.session_state.registros:
    total_horas = calcular_horas_totales()
    st.markdown("---")
    st.metric(label="Total de horas registradas", value=f"{total_horas:.2f}h")

# ========================
# SELECTOR AGREGAR ACTIVIDAD
# ========================
st.selectbox(
    "Agregar actividad",
    ["Seleccionar..."] + act_l,
    key="sel_act",
    on_change=agregar
)

# ========================
# GUARDAR
# ========================
if st.button("Guardar", use_container_width=True):

    errores = []

    if not nombre:
        errores.append("Selecciona tu nombre")

    if not st.session_state.registros:
        errores.append("Agrega al menos un registro antes de guardar")

    for i, r in enumerate(st.session_state.registros):
        act_id         = r["actividad_id"]
        act_nombre_val = id_to_act[act_id]
        prefijo        = f"Actividad '{act_nombre_val}'"

        if r["horas"] == 0:
            if act_id == ID_SOPORTE:
                errores.append(f"{prefijo}: la hora de fin debe ser mayor a la de inicio")
            else:
                errores.append(f"{prefijo}: las horas deben ser mayores a 0")

        # Nombre actividad obligatorio cuando el proyecto es "Otro" o cuando la actividad lo requiere
        if act_id in (ID_PROYECTO, ID_ASIGNACION):
            if r.get("proy_id") == ID_PROYECTO_OTRO and not r.get("nombre", "").strip():
                errores.append(f"{prefijo}: el campo 'Nombre actividad' es obligatorio cuando el proyecto es 'Otro'")
        else:
            if not r.get("nombre", "").strip():
                errores.append(f"{prefijo}: el campo 'Nombre actividad' es obligatorio")

        if act_id != ID_SOPORTE:
            if r["inicio"] > r["fin"]:
                errores.append(f"{prefijo}: la fecha de inicio no puede ser posterior a la de fin")

    if errores:
        for e in errores:
            st.error(f"{e}")
        st.stop()

    # Barra de carga
    progress_bar  = st.progress(0, text="Guardando registros...")
    total_reg     = len(st.session_state.registros)
    items_resumen = []

    try:
        for idx, r in enumerate(st.session_state.registros):
            insertar_registro_horas(
                supabase,
                id_empleado,
                r["actividad_id"],
                r["proy_id"],
                str(r["fin"].date()),
                r["horas"],
                r["nombre"],
                r["desc"],
                r["inicio"].isoformat(),
                r["fin"].isoformat()
            )

            act_nombre_val = id_to_act[r["actividad_id"]]

            if r["actividad_id"] == ID_SOPORTE:
                periodo = r["inicio"].strftime("%d/%m/%Y %H:%M") + " - " + r["fin"].strftime("%H:%M")
            else:
                periodo = r["inicio"].strftime("%d/%m/%Y") + " al " + r["fin"].strftime("%d/%m/%Y")

            items_resumen.append({
                "actividad":   act_nombre_val,
                "proyecto":    r["proyecto"] if r["proyecto"] else "Sin proyecto",
                "horas":       r["horas"],
                "nombre_act":  r["nombre"] if r["nombre"] != r["proyecto"] else "",
                "descripcion": r["desc"],
                "periodo":     periodo,
            })

            progress = int(((idx + 1) / total_reg) * 100)
            progress_bar.progress(progress, text=f"Guardando {idx + 1} de {total_reg}...")
            time_module.sleep(0.3)

        progress_bar.progress(100, text="Guardado completamente")
        time_module.sleep(0.5)
        progress_bar.empty()

        st.session_state.ultimo_resumen = {
            "empleado":       nombre,
            "fecha_guardado": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "total_horas":    sum(item["horas"] for item in items_resumen),
            "items":          items_resumen,
        }
        st.session_state.registros = []
        st.rerun()

    except Exception as e:
        progress_bar.empty()
        st.error(f"Error al guardar: {e}")
