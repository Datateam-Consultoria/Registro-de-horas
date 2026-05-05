from supabase import create_client, Client
import streamlit as st

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(url, key)

def obtener_empleados_dict_y_lista(url: str, key: str):

    response = supabase.table("personal").select("id_empleado, nombre").execute()

    data = response.data

    if not data:
        print("⚠️ No hay datos o no tienes permisos (RLS)")
        return {}, []

    # Diccionario: nombre -> id_empleado
    empleados_dict = {row["nombre"]: row["id_empleado"] for row in data}

    # Lista de nombres
    nombres_lista = [row["nombre"] for row in data]

    return empleados_dict, nombres_lista



empleados_dict, nombres_lista = obtener_empleados_dict_y_lista(url, key)

print(empleados_dict)
print(nombres_lista)