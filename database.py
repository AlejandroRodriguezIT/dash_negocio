"""
Conexión a la base de datos MySQL
==================================
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

# Configuración MySQL — usa variables de entorno en producción
MYSQL_CONFIG = {
    "user": os.environ.get("MYSQL_USER", "alen_depor"),
    "password": os.environ.get("MYSQL_PASSWORD", ""),
    "host": os.environ.get("MYSQL_HOST", "82.165.192.201"),
    "database": os.environ.get("MYSQL_DATABASE", "Dash_Negocio")
}

MYSQL_URL = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"


def get_engine():
    """Crea y devuelve un engine de SQLAlchemy."""
    return create_engine(MYSQL_URL)


def query_to_df(query: str) -> pd.DataFrame:
    """Ejecuta una query y devuelve un DataFrame."""
    engine = get_engine()
    return pd.read_sql(query, engine)


# =============================================================================
# QUERIES PREDEFINIDAS
# =============================================================================

def get_ticketing_data():
    """Obtiene datos de ticketing con información de partidos."""
    query = """
    SELECT 
        t.*,
        p.schedule,
        p.dia_semana,
        p.t1_name,
        p.t2_name,
        p.result,
        p.id_temporada
    FROM slv_ticketing t
    LEFT JOIN slv_partidos p ON t.id_partido = p.id
    WHERE p.id IS NOT NULL
    """
    return query_to_df(query)


def get_cesiones_data():
    """Obtiene datos de cesiones con información de partidos."""
    query = """
    SELECT 
        c.*,
        p.schedule,
        p.dia_semana,
        p.t1_name,
        p.t2_name,
        p.result,
        p.id_temporada
    FROM slv_cesiones c
    LEFT JOIN slv_partidos p ON c.id_partido = p.id
    WHERE p.id IS NOT NULL
    """
    return query_to_df(query)


def get_partidos_temporada(temporada: str = None):
    """Obtiene partidos de una temporada."""
    query = """
    SELECT * FROM slv_partidos
    WHERE equipo_depor = '1'
    """
    if temporada:
        query += f" AND id_temporada = '{temporada}'"
    query += " ORDER BY schedule DESC"
    return query_to_df(query)


def get_temporadas():
    """Obtiene lista de temporadas disponibles."""
    query = """
    SELECT DISTINCT id_temporada 
    FROM slv_partidos 
    WHERE id_temporada IS NOT NULL
    ORDER BY id_temporada DESC
    """
    return query_to_df(query)


def get_asistencias_data():
    """Obtiene datos de asistencias con información de partidos, abonos y socios."""
    query = """
    SELECT 
        a.clave_unica,
        a.hora_asistencia_abono,
        a.id_partido,
        a.condicion,
        ab.sector,
        ab.locality,
        ab.cardId,
        s.birthdate,
        s.gender,
        p.schedule,
        p.t2_name,
        p.t1_name,
        p.id_temporada,
        p.dia_semana,
        p.result,
        TIME(p.schedule) as hora_partido
    FROM slv_asistencias a
    JOIN slv_abonos ab ON a.clave_unica = ab.cardId
    JOIN slv_socios s ON ab.ownerId = s.id
    JOIN slv_partidos p ON a.id_partido = p.id
    WHERE ab.locality NOT IN ('SIN ASIENTO', 'CERO', 'AREA 1906')
    AND p.equipo_depor = '901'
    """
    return query_to_df(query)


def get_abonados_totales(temporada: str = '2025'):
    """Obtiene el total de abonados de una temporada (excluyendo SIN ASIENTO, CERO, AREA 1906)."""
    query = f"""
    SELECT COUNT(*) as total_abonados 
    FROM slv_abonos 
    WHERE id_temporada = '{temporada}' 
    AND locality NOT IN ('SIN ASIENTO', 'CERO', 'AREA 1906')
    """
    return query_to_df(query)


def get_abonados_por_sector(temporada: str = '2025'):
    """Obtiene abonados por sector de una temporada."""
    query = f"""
    SELECT sector, COUNT(*) as total 
    FROM slv_abonos 
    WHERE id_temporada = '{temporada}' 
    AND locality NOT IN ('SIN ASIENTO', 'CERO', 'AREA 1906')
    AND sector IN ('FONDO MARATHON', 'FONDO PABELLON', 'PREFERENCIA', 'TRIBUNA')
    GROUP BY sector
    """
    return query_to_df(query)


def get_abonados_por_sexo(temporada: str = '2025'):
    """Obtiene desglose de abonados por sexo."""
    query = f"""
    SELECT s.gender, COUNT(*) as total
    FROM slv_abonos ab
    JOIN slv_socios s ON ab.ownerId = s.id
    WHERE ab.id_temporada = '{temporada}'
    AND ab.locality NOT IN ('SIN ASIENTO', 'CERO', 'AREA 1906')
    GROUP BY s.gender
    """
    return query_to_df(query)


def get_recaudacion_cesiones():
    """Obtiene la recaudación por cesiones vendidas por partido."""
    query = """
    SELECT 
        t.id_partido,
        SUM(t.rec_ces_vend) as rec_ces_vend,
        p.schedule,
        p.t1_name,
        p.t2_name,
        p.id_temporada,
        p.dia_semana,
        p.result
    FROM slv_ticketing t
    LEFT JOIN slv_partidos p ON t.id_partido = p.id
    WHERE p.id IS NOT NULL
    GROUP BY t.id_partido, p.schedule, p.t1_name, p.t2_name, p.id_temporada, p.dia_semana, p.result
    """
    return query_to_df(query)


def get_primeros_n_partidos_local(n_partidos, temporada='2024'):
    """Obtiene los IDs de los primeros N partidos de liga como local para una temporada."""
    # Excluir pretemporada (antes del 15 de agosto)
    year = int(temporada)
    cutoff = f"{year}-08-15"
    query = f"""
    SELECT id FROM slv_partidos 
    WHERE t1_name = 'RC Deportivo' 
    AND id_temporada = '{temporada}'
    AND schedule >= '{cutoff}'
    ORDER BY schedule
    LIMIT {n_partidos}
    """
    df = query_to_df(query)
    return [int(x) for x in df['id'].tolist()]


# =============================================================================
# TABLAS PRE-CALCULADAS (para el dashboard optimizado)
# =============================================================================

def get_pre_entradas_partido():
    """Datos pre-calculados de entradas por partido (actual + anterior)."""
    return query_to_df("SELECT * FROM pre_entradas_partido ORDER BY temporada, schedule")


def get_pre_cesiones_partido():
    """Datos pre-calculados de cesiones por partido (actual + anterior)."""
    return query_to_df("SELECT * FROM pre_cesiones_partido ORDER BY temporada, schedule")


def get_pre_cesiones_recaudacion():
    """Recaudación pre-calculada por cesiones por partido."""
    return query_to_df("SELECT * FROM pre_cesiones_recaudacion ORDER BY temporada, schedule")


def get_pre_entradas_sector():
    """Desglose de entradas por sector y partido."""
    return query_to_df("SELECT * FROM pre_entradas_sector")


def get_pre_cesiones_sector():
    """Desglose de cesiones por sector y partido."""
    return query_to_df("SELECT * FROM pre_cesiones_sector")


def get_pre_hosteleria_partido():
    """Datos pre-calculados de hostelería por partido."""
    return query_to_df("SELECT * FROM pre_hosteleria_partido ORDER BY temporada, schedule")


def get_pre_hosteleria_producto():
    """Top productos de hostelería pre-calculados."""
    return query_to_df("SELECT * FROM pre_hosteleria_producto ORDER BY recaudacion DESC")


def get_pre_hosteleria_cantina():
    """Datos de hostelería por cantina pre-calculados."""
    return query_to_df("SELECT * FROM pre_hosteleria_cantina ORDER BY recaudacion DESC")


def get_pre_hosteleria_producto_cantina():
    """Cruce producto-cantina de hostelería pre-calculado."""
    return query_to_df("SELECT * FROM pre_hosteleria_producto_cantina ORDER BY cantidad DESC")


def get_pre_hosteleria_metodo_pago():
    """Datos de hostelería por método de pago y partido."""
    return query_to_df("SELECT * FROM pre_hosteleria_metodo_pago ORDER BY schedule")


def get_pre_asistencia_kpis():
    """KPIs pre-calculados de asistencia."""
    return query_to_df("SELECT * FROM pre_asistencia_kpis")


def get_pre_asistencia_sector():
    """Asistencia por sector pre-calculada."""
    return query_to_df("SELECT * FROM pre_asistencia_sector")


def get_pre_asistencia_consecutiva():
    """Asistencia consecutiva pre-calculada por jornada."""
    return query_to_df("SELECT * FROM pre_asistencia_consecutiva ORDER BY jornada_num")


def get_pre_asistencia_partido():
    """Espectadores vs abonados pre-calculados por partido."""
    return query_to_df("SELECT * FROM pre_asistencia_partido ORDER BY schedule")


def get_pre_asistencia_edad():
    """Distribución por edad pre-calculada."""
    return query_to_df("SELECT * FROM pre_asistencia_edad")


def get_partidos_local(temporada: str = '2025'):
    """Obtiene partidos donde RC Deportivo juega de local."""
    query = f"""
    SELECT id, schedule, t2_name, t1_name, id_temporada, dia_semana
    FROM slv_partidos 
    WHERE equipo_depor = '901' 
    AND id_temporada = '{temporada}'
    AND t1_name = 'RC Deportivo'
    ORDER BY schedule
    """
    return query_to_df(query)


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

def init_users_table():
    """Crea la tabla de usuarios si no existe e inserta admin por defecto."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS plataforma_usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario VARCHAR(100) UNIQUE NOT NULL,
                contrasena VARCHAR(255) NOT NULL,
                permisos VARCHAR(50) NOT NULL DEFAULT '0',
                nombre VARCHAR(200),
                rol VARCHAR(100),
                activo TINYINT(1) DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        # Insertar admin si no existe
        result = conn.execute(text("SELECT COUNT(*) AS cnt FROM plataforma_usuarios WHERE usuario = 'admin'"))
        if result.fetchone()[0] == 0:
            conn.execute(text(
                "INSERT INTO plataforma_usuarios (usuario, contrasena, permisos, nombre, rol) "
                "VALUES ('admin', 'admin', '0', 'Administrador', 'Dirección')"
            ))
        conn.commit()


def validate_user(usuario: str, contrasena: str):
    """Valida credenciales. Devuelve dict con info del usuario o None."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, usuario, permisos, nombre, rol FROM plataforma_usuarios "
            "WHERE usuario = :u AND contrasena = :p AND activo = 1"
        ), {"u": usuario, "p": contrasena})
        row = result.fetchone()
        if row:
            return {
                "id": row[0],
                "usuario": row[1],
                "permisos": row[2],
                "nombre": row[3],
                "rol": row[4],
            }
    return None
