"""
Tabla de validación: Comparativa jornada a jornada entre temporada actual y anterior
====================================================================================
Entradas vendidas, no vendidas, cesiones vendidas, no vendidas, 
recaudación entradas, recaudación cesiones
"""
from database import get_ticketing_data, get_cesiones_data, get_recaudacion_cesiones, get_primeros_n_partidos_local
import pandas as pd
from datetime import datetime

INICIO_TEMP_ACTUAL = datetime(2025, 8, 1)
INICIO_TEMP_ANTERIOR = datetime(2024, 8, 1)

# ===================== TICKETING (ENTRADAS) =====================
df_tick = get_ticketing_data()
df_tick['schedule'] = pd.to_datetime(df_tick['schedule'], errors='coerce')

# Temporada actual
df_tick_act = df_tick[(df_tick['schedule'] >= INICIO_TEMP_ACTUAL) & (df_tick['t1_name'] == 'RC Deportivo')]
tick_act = df_tick_act.groupby(['id_partido', 't2_name', 'schedule', 'result']).agg({
    'n_publico': 'sum', 'norm_no_vend': 'sum', 'recaudacion': 'sum', 'rec_ces_vend': 'sum'
}).reset_index().sort_values('schedule')
n_actual = len(tick_act)

# Temporada anterior - primeros N partidos de liga (desde slv_partidos)
match_ids_ant = get_primeros_n_partidos_local(n_actual, '2024')
df_tick_ant = df_tick[df_tick['id_partido'].isin(match_ids_ant)]
tick_ant_all = df_tick_ant.groupby(['id_partido', 't2_name', 'schedule', 'result']).agg({
    'n_publico': 'sum', 'norm_no_vend': 'sum', 'recaudacion': 'sum', 'rec_ces_vend': 'sum'
}).reset_index().sort_values('schedule')
tick_ant = tick_ant_all  # All matches that have data within the first N league matches

# ===================== CESIONES =====================
df_ces = get_cesiones_data()
df_ces['schedule'] = pd.to_datetime(df_ces['schedule'], errors='coerce')
df_ces['cesion_vendida'] = df_ces['estado_mercado_secundario_v_d_b'] == 'V'
df_ces['cesion_disponible'] = df_ces['estado_mercado_secundario_v_d_b'] == 'D'

# Cesiones actual
df_ces_act = df_ces[(df_ces['schedule'] >= INICIO_TEMP_ACTUAL) & (df_ces['t1_name'] == 'RC Deportivo')]
ces_act = df_ces_act.groupby(['id_partido', 't2_name', 'schedule']).agg({
    'cesion_vendida': 'sum', 'cesion_disponible': 'sum', 'saldo_mercado_secundario': 'sum'
}).reset_index().sort_values('schedule')

# Cesiones anterior - primeros N partidos de liga (desde slv_partidos)
n_ces_actual = len(ces_act)
match_ids_ces_ant = get_primeros_n_partidos_local(n_ces_actual, '2024')
df_ces_ant = df_ces[df_ces['id_partido'].isin(match_ids_ces_ant)]
ces_ant_all = df_ces_ant.groupby(['id_partido', 't2_name', 'schedule']).agg({
    'cesion_vendida': 'sum', 'cesion_disponible': 'sum', 'saldo_mercado_secundario': 'sum'
}).reset_index().sort_values('schedule')
ces_ant = ces_ant_all

def fmt(val):
    return f"{val:,.0f}".replace(",", ".")

# ===================== IMPRIMIR TABLAS =====================
print("=" * 120)
print(f"TEMPORADA ACTUAL 25/26 — ENTRADAS (Ticketing) — {n_actual} partidos como local")
print("=" * 120)
print(f"{'J':>3} {'Fecha':>12} {'Rival':<22} {'Result':>7} {'Vendidas':>10} {'No Vend':>10} {'Recaud. Entr.':>14} {'Recaud. Ces.':>14}")
print("-" * 120)
for idx, r in tick_act.iterrows():
    j = tick_act.index.tolist().index(idx) + 1
    print(f"{j:>3} {r['schedule'].strftime('%Y-%m-%d'):>12} {r['t2_name']:<22} {r['result']:>7} {fmt(r['n_publico']):>10} {fmt(r['norm_no_vend']):>10} {fmt(r['recaudacion']):>14} {fmt(r['rec_ces_vend']):>14}")
print("-" * 120)
print(f"{'TOTAL':>46} {fmt(tick_act['n_publico'].sum()):>10} {fmt(tick_act['norm_no_vend'].sum()):>10} {fmt(tick_act['recaudacion'].sum()):>14} {fmt(tick_act['rec_ces_vend'].sum()):>14}")
print(f"{'PROMEDIO':>46} {fmt(tick_act['n_publico'].mean()):>10} {fmt(tick_act['norm_no_vend'].mean()):>10} {fmt(tick_act['recaudacion'].mean()):>14} {fmt(tick_act['rec_ces_vend'].mean()):>14}")

print()
print("=" * 120)
print(f"TEMPORADA ANTERIOR 24/25 — ENTRADAS (Ticketing) — Primeros {len(tick_ant)} partidos con datos (de {len(tick_ant_all)} totales)")
print("=" * 120)
print(f"{'J':>3} {'Fecha':>12} {'Rival':<22} {'Result':>7} {'Vendidas':>10} {'No Vend':>10} {'Recaud. Entr.':>14} {'Recaud. Ces.':>14}")
print("-" * 120)
for idx, r in tick_ant.iterrows():
    j = tick_ant.index.tolist().index(idx) + 1
    print(f"{j:>3} {r['schedule'].strftime('%Y-%m-%d'):>12} {r['t2_name']:<22} {r['result']:>7} {fmt(r['n_publico']):>10} {fmt(r['norm_no_vend']):>10} {fmt(r['recaudacion']):>14} {fmt(r['rec_ces_vend']):>14}")
print("-" * 120)
print(f"{'TOTAL':>46} {fmt(tick_ant['n_publico'].sum()):>10} {fmt(tick_ant['norm_no_vend'].sum()):>10} {fmt(tick_ant['recaudacion'].sum()):>14} {fmt(tick_ant['rec_ces_vend'].sum()):>14}")
if len(tick_ant) > 0:
    print(f"{'PROMEDIO':>46} {fmt(tick_ant['n_publico'].mean()):>10} {fmt(tick_ant['norm_no_vend'].mean()):>10} {fmt(tick_ant['recaudacion'].mean()):>14} {fmt(tick_ant['rec_ces_vend'].mean()):>14}")

print()
print("=" * 100)
print(f"TEMPORADA ACTUAL 25/26 — CESIONES — {n_ces_actual} partidos como local")
print("=" * 100)
print(f"{'J':>3} {'Fecha':>12} {'Rival':<22} {'Ces. Vendidas':>14} {'Ces. No Vend':>14} {'Saldo':>12}")
print("-" * 100)
for idx, r in ces_act.iterrows():
    j = ces_act.index.tolist().index(idx) + 1
    print(f"{j:>3} {r['schedule'].strftime('%Y-%m-%d'):>12} {r['t2_name']:<22} {fmt(r['cesion_vendida']):>14} {fmt(r['cesion_disponible']):>14} {fmt(r['saldo_mercado_secundario']):>12}")
print("-" * 100)
print(f"{'TOTAL':>39} {fmt(ces_act['cesion_vendida'].sum()):>14} {fmt(ces_act['cesion_disponible'].sum()):>14} {fmt(ces_act['saldo_mercado_secundario'].sum()):>12}")
print(f"{'PROMEDIO':>39} {fmt(ces_act['cesion_vendida'].mean()):>14} {fmt(ces_act['cesion_disponible'].mean()):>14} {fmt(ces_act['saldo_mercado_secundario'].mean()):>12}")

print()
print("=" * 100)
print(f"TEMPORADA ANTERIOR 24/25 — CESIONES — Primeros {len(ces_ant)} partidos (de {len(ces_ant_all)} totales)")
print("=" * 100)
print(f"{'J':>3} {'Fecha':>12} {'Rival':<22} {'Ces. Vendidas':>14} {'Ces. No Vend':>14} {'Saldo':>12}")
print("-" * 100)
for idx, r in ces_ant.iterrows():
    j = ces_ant.index.tolist().index(idx) + 1
    print(f"{j:>3} {r['schedule'].strftime('%Y-%m-%d'):>12} {r['t2_name']:<22} {fmt(r['cesion_vendida']):>14} {fmt(r['cesion_disponible']):>14} {fmt(r['saldo_mercado_secundario']):>12}")
print("-" * 100)
print(f"{'TOTAL':>39} {fmt(ces_ant['cesion_vendida'].sum()):>14} {fmt(ces_ant['cesion_disponible'].sum()):>14} {fmt(ces_ant['saldo_mercado_secundario'].sum()):>12}")
if len(ces_ant) > 0:
    print(f"{'PROMEDIO':>39} {fmt(ces_ant['cesion_vendida'].mean()):>14} {fmt(ces_ant['cesion_disponible'].mean()):>14} {fmt(ces_ant['saldo_mercado_secundario'].mean()):>12}")

# ===================== RESUMEN COMPARATIVO =====================
print()
print("=" * 80)
print("RESUMEN COMPARATIVO")
print("=" * 80)
print(f"{'Métrica':<35} {'25/26':>15} {'24/25':>15} {'Diferencia':>12}")
print("-" * 80)

def pct_diff(a, b):
    if b > 0:
        return f"{((a-b)/b)*100:+.1f}%"
    return "N/A"

metrics = [
    ("Entradas vendidas (total)", tick_act['n_publico'].sum(), tick_ant['n_publico'].sum()),
    ("Entradas vendidas (promedio)", tick_act['n_publico'].mean(), tick_ant['n_publico'].mean()),
    ("Entradas no vendidas (total)", tick_act['norm_no_vend'].sum(), tick_ant['norm_no_vend'].sum()),
    ("Recaudación entradas (total)", tick_act['recaudacion'].sum(), tick_ant['recaudacion'].sum()),
    ("Recaudación entradas (promedio)", tick_act['recaudacion'].mean(), tick_ant['recaudacion'].mean()),
    ("Recaudación cesiones (total)", tick_act['rec_ces_vend'].sum(), tick_ant['rec_ces_vend'].sum()),
    ("Recaudación cesiones (promedio)", tick_act['rec_ces_vend'].mean(), tick_ant['rec_ces_vend'].mean()),
    ("Cesiones vendidas (total)", ces_act['cesion_vendida'].sum(), ces_ant['cesion_vendida'].sum()),
    ("Cesiones vendidas (promedio)", ces_act['cesion_vendida'].mean(), ces_ant['cesion_vendida'].mean()),
    ("Cesiones no vendidas (total)", ces_act['cesion_disponible'].sum(), ces_ant['cesion_disponible'].sum()),
    ("Saldo cesiones (total)", ces_act['saldo_mercado_secundario'].sum(), ces_ant['saldo_mercado_secundario'].sum()),
]

for label, val_act, val_ant in metrics:
    print(f"{label:<35} {fmt(val_act):>15} {fmt(val_ant):>15} {pct_diff(val_act, val_ant):>12}")

print()
print(f"NOTA: Ticketing temp. anterior tiene datos de {len(tick_ant)} partidos (faltan {n_actual - len(tick_ant)} de los {n_actual} esperados)")
print(f"NOTA: Cesiones temp. anterior tiene datos de {len(ces_ant)} partidos (faltan {n_ces_actual - len(ces_ant)} de los {n_ces_actual} esperados)")

# Listar partidos sin datos de ticketing en temp anterior
print()
print("Partidos temp. anterior 24/25 SIN datos de ticketing:")
all_home_24 = """
Real Oviedo (2024-08-17)
Racing (2024-10-27)  
Real Sporting (2024-11-24)
Real Zaragoza (2024-12-07)
""".strip()
print(all_home_24)
