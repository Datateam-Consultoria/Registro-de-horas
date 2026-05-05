import streamlit as st
from supabase import create_client, Client
from backend_supabase import (
    obtener_personal, actualizar_empleado, insertar_empleado,
    obtener_actividades, actualizar_actividad, insertar_actividad,
    obtener_proyectos, actualizar_proyecto, insertar_proyecto,
)

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="Manager de catálogos", layout="centered")

# ========================
# HEADER
# ========================
col1, col2 = st.columns([1, 3])
with col1:
    st.image("Logo-Datateam.png", width=300)
with col2:
    st.markdown("<h1>Manager de catálogos</h1>", unsafe_allow_html=True)

st.markdown("---")

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
# HELPERS
# ========================
def fmt_fecha(val) -> str:
    return str(val)[:10] if val else "—"


# ========================
# CACHE Y RECARGA
# ========================
@st.cache_data
def load_personal():
    return obtener_personal(supabase)

@st.cache_data
def load_actividades():
    return obtener_actividades(supabase)

@st.cache_data
def load_proyectos():
    return obtener_proyectos(supabase)

def recargar_personal():    load_personal.clear()
def recargar_actividades(): load_actividades.clear()
def recargar_proyectos():   load_proyectos.clear()


# ========================
# TABS
# ========================
tab_personal, tab_actividades, tab_proyectos = st.tabs([
    "👤 Personal",
    "🏷️ Actividades",
    "📁 Proyectos",
])


# ================================================================
# TAB PERSONAL
# ================================================================
with tab_personal:

    datos = load_personal()

    # Inicializar estado editable solo si no existe o si los datos cambiaron
    if "per_estado" not in st.session_state:
        st.session_state.per_estado = {
            row["id_empleado"]: {"nombre": row["nombre"], "activo": row["activo"]}
            for row in datos
        }

    # Encabezado
    st.markdown("### Empleados")
    hcols = st.columns([3, 1, 1])
    hcols[0].markdown("**Nombre**")
    hcols[1].markdown("**Activo**")
    hcols[2].markdown("**Alta**")
    st.markdown("<hr style='margin:4px 0 8px 0'>", unsafe_allow_html=True)

    cambios_per = {}

    for row in datos:
        rid     = row["id_empleado"]
        orig    = {"nombre": row["nombre"], "activo": row["activo"]}
        estado  = st.session_state.per_estado.get(rid, orig.copy())

        rcols = st.columns([3, 1, 1])

        nuevo_nombre = rcols[0].text_input(
            label="nombre", value=estado["nombre"],
            key=f"per_nombre_{rid}", label_visibility="collapsed",
        )
        nuevo_activo = rcols[1].checkbox(
            label="activo", value=estado["activo"],
            key=f"per_activo_{rid}", label_visibility="collapsed",
        )
        rcols[2].markdown(fmt_fecha(row.get("fecha_creacion")))

        # Actualizar estado en vivo
        st.session_state.per_estado[rid] = {"nombre": nuevo_nombre, "activo": nuevo_activo}

        # Detectar cambio respecto al valor original en BD
        if nuevo_nombre.strip() != orig["nombre"] or nuevo_activo != orig["activo"]:
            cambios_per[rid] = {"nombre": nuevo_nombre.strip(), "activo": nuevo_activo}

    # Indicador de cambios pendientes
    if cambios_per:
        st.info(f"✏️ {len(cambios_per)} registro(s) con cambios sin guardar.")

    st.markdown("---")

    # Agregar nuevo empleado
    with st.expander("➕ Agregar empleado"):
        nuevo_nombre_per = st.text_input("Nombre", key="per_nuevo_nombre")
        if st.button("Agregar", key="per_agregar_btn"):
            if not nuevo_nombre_per.strip():
                st.error("El nombre no puede estar vacío.")
            else:
                try:
                    insertar_empleado(supabase, nuevo_nombre_per.strip())
                    st.success(f"'{nuevo_nombre_per.strip()}' agregado.")
                    recargar_personal()
                    st.session_state.pop("per_estado", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # Botón guardar global
    if st.button("💾 Guardar cambios", key="per_guardar", use_container_width=True,
                 disabled=len(cambios_per) == 0):
        errores = [rid for rid, c in cambios_per.items() if not c["nombre"]]
        if errores:
            st.error(f"{len(errores)} registro(s) tienen el nombre vacío.")
        else:
            try:
                for rid, c in cambios_per.items():
                    actualizar_empleado(supabase, rid, c["nombre"], c["activo"])
                st.success(f"✅ {len(cambios_per)} registro(s) guardados correctamente.")
                recargar_personal()
                st.session_state.pop("per_estado", None)
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")


# ================================================================
# TAB ACTIVIDADES
# ================================================================
with tab_actividades:

    datos = load_actividades()

    if "act_estado" not in st.session_state:
        st.session_state.act_estado = {
            row["id_tipo_actividad"]: {"nombre": row["nombre_tipo"]}
            for row in datos
        }

    st.markdown("### Actividades")
    hcols = st.columns([4])
    hcols[0].markdown("**Nombre**")
    st.markdown("<hr style='margin:4px 0 8px 0'>", unsafe_allow_html=True)

    cambios_act = {}

    for row in datos:
        rid    = row["id_tipo_actividad"]
        orig   = {"nombre": row["nombre_tipo"]}
        estado = st.session_state.act_estado.get(rid, orig.copy())

        nuevo_nombre = st.text_input(
            label="nombre", value=estado["nombre"],
            key=f"act_nombre_{rid}", label_visibility="collapsed",
        )

        st.session_state.act_estado[rid] = {"nombre": nuevo_nombre}

        if nuevo_nombre.strip() != orig["nombre"]:
            cambios_act[rid] = {"nombre": nuevo_nombre.strip()}

    if cambios_act:
        st.info(f"✏️ {len(cambios_act)} registro(s) con cambios sin guardar.")

    st.markdown("---")

    with st.expander("➕ Agregar actividad"):
        nuevo_nombre_act = st.text_input("Nombre", key="act_nuevo_nombre")
        if st.button("Agregar", key="act_agregar_btn"):
            if not nuevo_nombre_act.strip():
                st.error("El nombre no puede estar vacío.")
            else:
                try:
                    insertar_actividad(supabase, nuevo_nombre_act.strip())
                    st.success(f"'{nuevo_nombre_act.strip()}' agregado.")
                    recargar_actividades()
                    st.session_state.pop("act_estado", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.button("💾 Guardar cambios", key="act_guardar", use_container_width=True,
                 disabled=len(cambios_act) == 0):
        errores = [rid for rid, c in cambios_act.items() if not c["nombre"]]
        if errores:
            st.error(f"{len(errores)} registro(s) tienen el nombre vacío.")
        else:
            try:
                for rid, c in cambios_act.items():
                    actualizar_actividad(supabase, rid, c["nombre"])
                st.success(f"✅ {len(cambios_act)} registro(s) guardados correctamente.")
                recargar_actividades()
                st.session_state.pop("act_estado", None)
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")


# ================================================================
# TAB PROYECTOS
# ================================================================
with tab_proyectos:

    datos = load_proyectos()

    if "proy_estado" not in st.session_state:
        st.session_state.proy_estado = {
            row["id_proyecto"]: {"nombre": row["nombre_proyecto"], "activo": row["activo"]}
            for row in datos
        }

    st.markdown("### Proyectos")
    hcols = st.columns([3, 1, 1])
    hcols[0].markdown("**Nombre**")
    hcols[1].markdown("**Activo**")
    hcols[2].markdown("**Alta**")
    st.markdown("<hr style='margin:4px 0 8px 0'>", unsafe_allow_html=True)

    cambios_proy = {}

    for row in datos:
        rid    = row["id_proyecto"]
        orig   = {"nombre": row["nombre_proyecto"], "activo": row["activo"]}
        estado = st.session_state.proy_estado.get(rid, orig.copy())

        rcols = st.columns([3, 1, 1])

        nuevo_nombre = rcols[0].text_input(
            label="nombre", value=estado["nombre"],
            key=f"proy_nombre_{rid}", label_visibility="collapsed",
        )
        nuevo_activo = rcols[1].checkbox(
            label="activo", value=estado["activo"],
            key=f"proy_activo_{rid}", label_visibility="collapsed",
        )
        rcols[2].markdown(fmt_fecha(row.get("fecha_creacion")))

        st.session_state.proy_estado[rid] = {"nombre": nuevo_nombre, "activo": nuevo_activo}

        if nuevo_nombre.strip() != orig["nombre"] or nuevo_activo != orig["activo"]:
            cambios_proy[rid] = {"nombre": nuevo_nombre.strip(), "activo": nuevo_activo}

    if cambios_proy:
        st.info(f"✏️ {len(cambios_proy)} registro(s) con cambios sin guardar.")

    st.markdown("---")

    with st.expander("➕ Agregar proyecto"):
        nuevo_nombre_proy = st.text_input("Nombre", key="proy_nuevo_nombre")
        if st.button("Agregar", key="proy_agregar_btn"):
            if not nuevo_nombre_proy.strip():
                st.error("El nombre no puede estar vacío.")
            else:
                try:
                    insertar_proyecto(supabase, nuevo_nombre_proy.strip())
                    st.success(f"'{nuevo_nombre_proy.strip()}' agregado.")
                    recargar_proyectos()
                    st.session_state.pop("proy_estado", None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.button("💾 Guardar cambios", key="proy_guardar", use_container_width=True,
                 disabled=len(cambios_proy) == 0):
        errores = [rid for rid, c in cambios_proy.items() if not c["nombre"]]
        if errores:
            st.error(f"{len(errores)} registro(s) tienen el nombre vacío.")
        else:
            try:
                for rid, c in cambios_proy.items():
                    actualizar_proyecto(supabase, rid, c["nombre"], c["activo"])
                st.success(f"✅ {len(cambios_proy)} registro(s) guardados correctamente.")
                recargar_proyectos()
                st.session_state.pop("proy_estado", None)
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar: {e}")