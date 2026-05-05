import streamlit as st
import pandas as pd
import altair as alt
from supabase import create_client, Client
from datetime import date, timedelta
from backend_supabase import (
    obtener_personal, actualizar_empleado, insertar_empleado,
    obtener_actividades, actualizar_actividad, insertar_actividad,
    obtener_proyectos, actualizar_proyecto, insertar_proyecto,
    obtener_registros_horas, obtener_registros_semana_actual,
)

# ========================
# CONFIG
# ========================
st.set_page_config(page_title="Manager de catálogos", layout="wide")

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

@st.cache_data(ttl=60)
def load_registros():
    return obtener_registros_horas(supabase)

@st.cache_data(ttl=60)
def load_registros_semana():
    return obtener_registros_semana_actual(supabase)

def recargar_personal():    load_personal.clear()
def recargar_actividades(): load_actividades.clear()
def recargar_proyectos():   load_proyectos.clear()


# ========================
# TABS
# ========================
tab_registros, tab_personal, tab_actividades, tab_proyectos = st.tabs([
    "📊 Registros de horas",
    "👤 Personal",
    "🏷️ Actividades",
    "📁 Proyectos",
])


# ================================================================
# TAB REGISTROS DE HORAS
# ================================================================
with tab_registros:

    # ---- Gráfica de barras: horas de esta semana ----
    today = date.today()
    lunes = today - timedelta(days=today.weekday())
    domingo = lunes + timedelta(days=6)

    st.markdown(f"### Horas esta semana &nbsp; <span style='font-size:0.85rem;color:gray'>{lunes.strftime('%d/%m/%Y')} — {domingo.strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)

    agrupar_por = st.radio(
        "Agrupar por",
        options=["Proyecto", "Tipo de actividad", "Empleado"],
        horizontal=True,
        key="reg_agrupar",
    )

    raw_semana = load_registros_semana()

    if not raw_semana:
        st.info("No hay registros para esta semana.")
    else:
        # Normalizar filas (los joins devuelven dicts anidados)
        filas_semana = []
        for r in raw_semana:
            filas_semana.append({
                "empleado":   (r.get("personal") or {}).get("nombre", "Sin nombre"),
                "actividad":  (r.get("actividades") or {}).get("nombre_tipo", "Sin actividad"),
                "proyecto":   (r.get("proyectos") or {}).get("nombre_proyecto", "Sin proyecto"),
                "horas":      float(r.get("horas_actividad") or 0),
            })

        df_semana = pd.DataFrame(filas_semana)

        col_map = {
            "Proyecto":           "proyecto",
            "Tipo de actividad":  "actividad",
            "Empleado":           "empleado",
        }
        col_agrup = col_map[agrupar_por]

        df_chart = (
            df_semana.groupby(col_agrup, as_index=False)["horas"]
            .sum()
            .sort_values("horas", ascending=False)
        )

        chart = (
            alt.Chart(df_chart)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X(f"{col_agrup}:N", sort="-y", title=agrupar_por, axis=alt.Axis(labelAngle=-30)),
                y=alt.Y("horas:Q", title="Horas"),
                color=alt.Color(f"{col_agrup}:N", legend=None),
                tooltip=[
                    alt.Tooltip(f"{col_agrup}:N", title=agrupar_por),
                    alt.Tooltip("horas:Q", title="Horas", format=".2f"),
                ],
            )
            .properties(height=320)
        )

        st.altair_chart(chart, use_container_width=True)
        st.markdown(f"**Total semana:** {df_semana['horas'].sum():.2f}h")

    st.markdown("---")

    # ---- Tabla de todos los registros ----
    st.markdown("### Todos los registros")

    if st.button("🔄 Actualizar", key="reg_refresh"):
        load_registros.clear()
        load_registros_semana.clear()
        st.rerun()

    raw = load_registros()

    if not raw:
        st.info("No hay registros.")
    else:
        filas = []
        for r in raw:
            inicio = r.get("inicio_actividad", "")
            fin    = r.get("fin_actividad", "")
            filas.append({
                "Fecha":        fmt_fecha(r.get("fecha_registro")),
                "Empleado":     (r.get("personal") or {}).get("nombre", "—"),
                "Actividad":    (r.get("actividades") or {}).get("nombre_tipo", "—"),
                "Proyecto":     (r.get("proyectos") or {}).get("nombre_proyecto", "—"),
                "Nombre act.":  r.get("nombre_actividad", ""),
                "Descripción":  r.get("desc_actividad", ""),
                "Horas":        float(r.get("horas_actividad") or 0),
                "Inicio":       str(inicio)[:16].replace("T", " ") if inicio else "—",
                "Fin":          str(fin)[:16].replace("T", " ") if fin else "—",
            })

        df = pd.DataFrame(filas)

        # Filtros rápidos
        fc1, fc2, fc3 = st.columns(3)
        empleados_opts = ["Todos"] + sorted(df["Empleado"].unique().tolist())
        proyectos_opts = ["Todos"] + sorted(df["Proyecto"].unique().tolist())
        actividad_opts = ["Todos"] + sorted(df["Actividad"].unique().tolist())

        fil_emp  = fc1.selectbox("Empleado",   empleados_opts, key="fil_emp")
        fil_proy = fc2.selectbox("Proyecto",   proyectos_opts, key="fil_proy")
        fil_act  = fc3.selectbox("Actividad",  actividad_opts, key="fil_act")

        df_fil = df.copy()
        if fil_emp  != "Todos": df_fil = df_fil[df_fil["Empleado"]  == fil_emp]
        if fil_proy != "Todos": df_fil = df_fil[df_fil["Proyecto"]  == fil_proy]
        if fil_act  != "Todos": df_fil = df_fil[df_fil["Actividad"] == fil_act]

        st.markdown(f"**{len(df_fil)} registro(s) — {df_fil['Horas'].sum():.2f}h en total**")

        st.dataframe(
            df_fil,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Horas": st.column_config.NumberColumn(format="%.2f"),
            },
        )


# ================================================================
# TAB PERSONAL
# ================================================================
with tab_personal:

    datos = load_personal()

    if "per_estado" not in st.session_state:
        st.session_state.per_estado = {
            row["id_empleado"]: {"nombre": row["nombre"], "activo": row["activo"]}
            for row in datos
        }

    st.markdown("### Empleados")
    hcols = st.columns([3, 1, 1])
    hcols[0].markdown("**Nombre**")
    hcols[1].markdown("**Activo**")
    hcols[2].markdown("**Alta**")
    st.markdown("<hr style='margin:4px 0 8px 0'>", unsafe_allow_html=True)

    cambios_per = {}

    for row in datos:
        rid   = row["id_empleado"]
        orig  = {"nombre": row["nombre"], "activo": row["activo"]}
        estado = st.session_state.per_estado.get(rid, orig.copy())

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

        st.session_state.per_estado[rid] = {"nombre": nuevo_nombre, "activo": nuevo_activo}

        if nuevo_nombre.strip() != orig["nombre"] or nuevo_activo != orig["activo"]:
            cambios_per[rid] = {"nombre": nuevo_nombre.strip(), "activo": nuevo_activo}

    if cambios_per:
        st.info(f"✏️ {len(cambios_per)} registro(s) con cambios sin guardar.")

    st.markdown("---")

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
    st.markdown("**Nombre**")
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
