"""
Conexión a la base de datos MySQL
==================================
"""

import pandas as pd
from sqlalchemy import create_engine, text

# Configuración MySQL
MYSQL_CONFIG = {
    "user": "alen_depor",
    "password": "ik3QJOq6n",
    "host": "82.165.192.201",
    "database": "Dash_Negocio"
}

MYSQL_URL = f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"


def get_engine():
    """Crea y devuelve un engine de SQLAlchemy.

    future=True activa la API compatible con SQLAlchemy 2.0 (Connection.commit
    y protocolo que pandas 2.x espera en df.to_sql).
    """
    return create_engine(MYSQL_URL, future=True)


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


def get_pre_deportiendas_kpis():
    """KPIs pre-calculados de DéporTiendas."""
    return query_to_df("SELECT * FROM pre_deportiendas_kpis")


def get_pre_deportiendas_matchday():
    """Ventas matchday Riazor pre-calculadas (actual + anterior)."""
    return query_to_df("SELECT * FROM pre_deportiendas_matchday ORDER BY temporada, fecha")


def get_pre_deportiendas_por_tienda():
    """Facturación por tienda pre-calculada."""
    return query_to_df("SELECT * FROM pre_deportiendas_por_tienda ORDER BY total_sales DESC")


def get_pre_deportiendas_top_productos():
    """Top 10 productos por unidades vendidas."""
    return query_to_df("SELECT * FROM pre_deportiendas_top_productos ORDER BY uds_vendidas DESC")


def get_pre_deportiendas_producto_tienda():
    """Cruce producto-tienda pre-calculado."""
    return query_to_df("SELECT * FROM pre_deportiendas_producto_tienda ORDER BY uds_vendidas DESC")


def get_pre_deportiendas_canal():
    """Ventas por canal (online vs física)."""
    return query_to_df("SELECT * FROM pre_deportiendas_canal")


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
# FICHA POST-PARTIDO
# =============================================================================

def get_ficha_rivales_temp_actual():
    """Devuelve los rivales de liga regular 25/26 en orden CRONOLÓGICO (más antiguo → más reciente).

    Solo incluye partidos de competición oficial como local (excluye pretemporada
    con cutoff 15-agosto). Para cada rival:
      - id_partido si hay partido con ficha registrada (jugado), NULL si aún por jugar.
      - result si está disputado, NULL si no.
    """
    query = """
    SELECT
        p.t2_name,
        MIN(p.id) AS id_partido,
        MIN(p.schedule) AS schedule,
        MAX(CASE WHEN p.result IS NOT NULL AND p.result <> '' THEN p.result END) AS result,
        MAX(CASE WHEN f.id_partido IS NOT NULL THEN 1 ELSE 0 END) AS tiene_ficha
    FROM slv_partidos p
    LEFT JOIN pre_ficha_partido f ON p.id = f.id_partido
    WHERE p.t1_name = 'RC Deportivo'
      AND p.id_temporada = '2025'
      AND p.schedule >= '2025-08-15'
    GROUP BY p.t2_name
    ORDER BY MIN(p.schedule) ASC
    """
    return query_to_df(query)


def get_ficha_partido(id_partido: int):
    """Devuelve la fila de pre_ficha_partido para un partido concreto."""
    query = f"SELECT * FROM pre_ficha_partido WHERE id_partido = {int(id_partido)} LIMIT 1"
    return query_to_df(query)


# =============================================================================
# CUENTA DE EXPLOTACIÓN HOSTELERÍA
# =============================================================================

def get_cuenta_explotacion_raw():
    """Datos crudos (Silver) — granularidad mínima por (area, equipo, bloque,
    variable, dimension, clave, id_partido). Útil para cualquier agregación
    custom que se quiera hacer en el dashboard."""
    return query_to_df("SELECT * FROM slv_cuenta_explotacion")


def get_pre_cuenta_pl_area():
    """P&L (ingresos/coste_total/resultado/margen_pct) por área, equipo,
    dimensión, clave e id_partido."""
    return query_to_df("SELECT * FROM pre_cuenta_pl_area ORDER BY area, dimension, clave")


def get_pre_cuenta_kpis_global():
    """KPIs globales agregados de TODAS las áreas (1 fila)."""
    return query_to_df("SELECT * FROM pre_cuenta_kpis_global")


def get_pre_cuenta_costes_area():
    """Desglose de costes (personal, food, beverage, mercadería, varios,
    mantenimiento) por área, equipo, dimensión, clave e id_partido."""
    return query_to_df("SELECT * FROM pre_cuenta_costes_area ORDER BY area, dimension, clave")


def get_pre_cuenta_productos_partido():
    """Unidades vendidas de productos por área, equipo, dimensión, clave,
    id_partido y nombre de producto."""
    return query_to_df("SELECT * FROM pre_cuenta_productos_partido "
                       "ORDER BY area, producto, unidades DESC")


def get_pre_cuenta_mensual_area():
    """Serie temporal mensual de ingresos/costes/resultado por área."""
    return query_to_df("SELECT * FROM pre_cuenta_mensual_area")


def get_pre_rentabilidad_operativa():
    """Rentabilidad operativa (%) por área × dimensión (temporada / mes)."""
    return query_to_df("SELECT * FROM pre_rentabilidad_operativa "
                       "ORDER BY area, dimension DESC, clave")


def get_pre_costes_desglose():
    """Costes desglosados por categoría (servicio_total / personal / food /
    beverage / varios), área, equipo, dimensión, clave e id_partido."""
    return query_to_df("SELECT * FROM pre_costes_desglose "
                       "ORDER BY area, categoria, dimension, clave")


# =============================================================================
# MUSEO RCD
# =============================================================================

def get_museo_kpis():
    """KPIs globales del museo."""
    return query_to_df("SELECT * FROM agg_museo_kpis WHERE id = 1")


def get_museo_diario():
    """Agregación diaria del museo por tipo de producto."""
    return query_to_df("SELECT * FROM agg_museo_diario ORDER BY fecha")


def get_museo_producto():
    """Agregación por tipo de producto."""
    return query_to_df("SELECT * FROM agg_museo_producto")


def get_museo_horario():
    """Agregación por franja horaria."""
    return query_to_df("SELECT * FROM agg_museo_horario ORDER BY hora_tour")


def get_museo_dia_semana():
    """Agregación por día de la semana."""
    return query_to_df("SELECT * FROM agg_museo_dia_semana ORDER BY dia_num")


def get_museo_canal():
    """Agregación por canal (plataforma)."""
    return query_to_df("SELECT * FROM agg_museo_canal ORDER BY pedidos DESC")


def get_museo_metodo_pago():
    """Agregación por método de pago."""
    return query_to_df("SELECT * FROM agg_museo_metodo_pago ORDER BY pedidos DESC")


def get_museo_heatmap():
    """Heatmap hora × día de semana."""
    return query_to_df("SELECT * FROM agg_museo_heatmap ORDER BY dia_num, hora_tour")


def get_museo_partidos_local():
    """Partidos locales del RC Deportivo desde apertura del museo (2026-02-18)."""
    return query_to_df("""
        SELECT DATE(schedule) as fecha, t2_name as rival
        FROM slv_partidos
        WHERE t1_name = 'RC Deportivo'
        AND schedule >= '2026-02-18'
        ORDER BY schedule
    """)


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

def init_users_table():
    """Crea la tabla de usuarios si no existe e inserta admin por defecto."""
    engine = get_engine()
    with engine.begin() as conn:
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


def validate_user(usuario: str, contrasena: str):
    """Valida credenciales. Devuelve dict con info del usuario o None."""
    engine = get_engine()
    with engine.begin() as conn:
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
