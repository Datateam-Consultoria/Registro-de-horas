from supabase import Client

def obtener_empleados_dict_y_lista(supabase: Client):
    response = supabase.table("personal").select("id_empleado, nombre").execute()
    data = response.data

    if not data:
        return {}, []

    dicc = {row["nombre"]: row["id_empleado"] for row in data}
    lista = [row["nombre"] for row in data]

    return dicc, lista

def obtener_proyectos_dict_y_lista(supabase: Client):
    response = supabase.table("proyectos").select("id_proyecto, nombre_proyecto").execute()
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
        "fin_actividad": fin
    }

    return supabase.table("registros_horas").insert(data).execute()
