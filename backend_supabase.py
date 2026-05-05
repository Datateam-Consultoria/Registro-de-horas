from supabase import Client
from datetime import date, timedelta


# ========================
# PERSONAL
# ========================

def obtener_personal(supabase: Client):
    res = supabase.table("personal").select("id_empleado, nombre, email, activo, fecha_creacion").order("nombre").execute()
    return res.data or []


def actualizar_empleado(supabase: Client, id_empleado: int, nuevo_nombre: str, nuevo_email: str, activo: bool):
    supabase.table("personal").update({
        "nombre": nuevo_nombre,
        "email":  nuevo_email,
        "activo": activo,
    }).eq("id_empleado", id_empleado).execute()


def insertar_empleado(supabase: Client, nombre: str, email: str = ""):
    supabase.table("personal").insert({
        "nombre": nombre,
        "email":  email,
        "activo": True,
    }).execute()


# ========================
# ACTIVIDADES
# ========================

def obtener_actividades(supabase: Client):
    res = supabase.table("actividades").select("id_tipo_actividad, nombre_tipo").order("nombre_tipo").execute()
    return res.data or []


def actualizar_actividad(supabase: Client, id_tipo_actividad: int, nuevo_nombre: str):
    supabase.table("actividades").update({"nombre_tipo": nuevo_nombre}).eq("id_tipo_actividad", id_tipo_actividad).execute()


def insertar_actividad(supabase: Client, nombre: str):
    supabase.table("actividades").insert({"nombre_tipo": nombre}).execute()


# ========================
# PROYECTOS
# ========================

def obtener_proyectos(supabase: Client):
    res = supabase.table("proyectos").select("id_proyecto, nombre_proyecto, activo, fecha_creacion").order("nombre_proyecto").execute()
    return res.data or []


def actualizar_proyecto(supabase: Client, id_proyecto: int, nuevo_nombre: str, activo: bool):
    supabase.table("proyectos").update({"nombre_proyecto": nuevo_nombre, "activo": activo}).eq("id_proyecto", id_proyecto).execute()


def insertar_proyecto(supabase: Client, nombre: str):
    supabase.table("proyectos").insert({"nombre_proyecto": nombre, "activo": True}).execute()


# ========================
# REGISTROS DE HORAS
# ========================

def obtener_registros_horas(supabase: Client):
    res = (
        supabase.table("registros_horas")
        .select(
            "id_registro, fecha_registro, horas_actividad, nombre_actividad, desc_actividad, "
            "inicio_actividad, fin_actividad, "
            "personal(nombre), "
            "actividades(nombre_tipo), "
            "proyectos(nombre_proyecto)"
        )
        .order("fecha_registro", desc=True)
        .execute()
    )
    return res.data or []


def obtener_registros_semana_actual(supabase: Client):
    today = date.today()
    lunes = today - timedelta(days=today.weekday())
    domingo = lunes + timedelta(days=6)
    res = (
        supabase.table("registros_horas")
        .select(
            "id_registro, fecha_registro, horas_actividad, nombre_actividad, "
            "personal(nombre), "
            "actividades(nombre_tipo), "
            "proyectos(nombre_proyecto)"
        )
        .gte("fecha_registro", lunes.isoformat())
        .lte("fecha_registro", domingo.isoformat())
        .execute()
    )
    return res.data or []


# ========================
# HELPERS (otros módulos)
# ========================

def obtener_empleados_dict_y_lista(supabase: Client):
    response = supabase.table("personal").select("id_empleado, nombre").eq("activo", True).execute()
    data = response.data
    if not data:
        return {}, []
    dicc = {row["nombre"]: row["id_empleado"] for row in data}
    lista = [row["nombre"] for row in data]
    return dicc, lista


def obtener_proyectos_dict_y_lista(supabase: Client):
    response = supabase.table("proyectos").select("id_proyecto, nombre_proyecto").eq("activo", True).execute()
    data = response.data
    if not data:
        return {}, []
    dicc = {row["nombre_proyecto"]: row["id_proyecto"] for row in data}
    lista = [row["nombre_proyecto"] for row in data]
    return dicc, lista


def obtener_actividades_dict_y_lista(supabase: Client):
    response = supabase.table("actividades").select("id_tipo_actividad, nombre_tipo").execute()
    data = response.data
    if not data:
        return {}, []
    dicc = {row["nombre_tipo"]: row["id_tipo_actividad"] for row in data}
    lista = [row["nombre_tipo"] for row in data]
    return dicc, lista


def insertar_registro_horas(
    supabase,
    id_empleado,
    id_tipo_actividad,
    id_proyecto,
    fecha_registro,
    horas,
    nombre,
    descripcion,
    inicio,
    fin
):
    data = {
        "id_empleado": id_empleado,
        "id_tipo_actividad": id_tipo_actividad,
        "id_proyecto": id_proyecto,
        "fecha_registro": fecha_registro,
        "horas_actividad": horas,
        "nombre_actividad": nombre,
        "desc_actividad": descripcion,
        "inicio_actividad": inicio,
        "fin_actividad": fin,
    }
    return supabase.table("registros_horas").insert(data).execute()
