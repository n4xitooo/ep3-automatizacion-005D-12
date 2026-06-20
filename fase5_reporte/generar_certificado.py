#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import socket
import sys
import yaml


BASE_DIR = Path(__file__).resolve().parents[1]
FASE5_DIR = Path(__file__).resolve().parent
EVID_DIR = FASE5_DIR / "evidencias"

VARS_FILE = BASE_DIR / "vars" / "vars_005D-12.yaml"

NETCONF_OUTPUT = BASE_DIR / "fase3_validacion_netconf" / "evidencias" / "output_validacion_netconf.txt"
RESTCONF_OUTPUT = BASE_DIR / "fase4_validacion_restconf" / "evidencias" / "output_validacion_restconf.txt"

SNAPSHOT_FINAL_DIR = EVID_DIR / "snapshot_final_005D-12"
DIFF_DIR = EVID_DIR / "diff_005D-12"

CERT_FILE = EVID_DIR / "certificado_compliance_005D-12.txt"
DIFF_TXT = EVID_DIR / "diff_baseline_final.txt"


def cargar_yaml(ruta):
    if not ruta.exists():
        print(f"[FAIL] No existe archivo requerido: {ruta}")
        sys.exit(1)

    with open(ruta, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def leer_texto(ruta):
    if not ruta.exists():
        return ""
    return ruta.read_text(encoding="utf-8", errors="ignore")


def archivos_no_vacios(directorio):
    if not directorio.exists():
        return []
    return [p for p in directorio.rglob("*") if p.is_file() and p.stat().st_size > 0]


def consolidar_diff():
    archivos = archivos_no_vacios(DIFF_DIR)
    partes = []

    for archivo in archivos:
        try:
            contenido = archivo.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            contenido = ""

        if contenido.strip():
            partes.append("=" * 80)
            partes.append(f"ARCHIVO DIFF: {archivo.relative_to(EVID_DIR)}")
            partes.append("=" * 80)
            partes.append(contenido)
            partes.append("")

    texto_final = "\n".join(partes).strip()

    if not texto_final:
        texto_final = "NO SE DETECTARON DIFERENCIAS O EL DIRECTORIO DIFF ESTA VACIO."

    DIFF_TXT.write_text(texto_final + "\n", encoding="utf-8")
    return texto_final


def estado_bool(valor):
    if valor:
        return "CONFORME"
    return "NO CONFORME"


def obtener(data, ruta):
    actual = data
    for clave in ruta:
        if isinstance(actual, dict) and clave in actual:
            actual = actual[clave]
        else:
            print(f"[FAIL] Falta variable en vars_005D-12.yaml: {'.'.join(ruta)}")
            sys.exit(1)
    return actual


def main():
    EVID_DIR.mkdir(parents=True, exist_ok=True)

    data = cargar_yaml(VARS_FILE)

    codigo = obtener(data, ["alumno", "codigo"])
    nombre = obtener(data, ["alumno", "nombre"])
    empresa = obtener(data, ["cliente", "empresa"])
    hostname = obtener(data, ["cliente", "hostname"])

    router_ip = obtener(data, ["router", "ip"])
    loopback_ip = obtener(data, ["router", "loopback_ip"])
    loopback_mask = obtener(data, ["router", "loopback_mask"])
    descripcion_wan = obtener(data, ["router", "descripcion_wan"])
    banner = obtener(data, ["router", "banner"])
    ntp_server = obtener(data, ["router", "ntp_server"])

    netconf_text = leer_texto(NETCONF_OUTPUT)
    restconf_text = leer_texto(RESTCONF_OUTPUT)

    netconf_ok = (
        "Resultado validaciones: 5/5 OK" in netconf_text
        and "Resultado global: CONFORME" in netconf_text
    )

    restconf_ok = (
        "Resultado validaciones: 4/4 OK" in restconf_text
        and "Resultado global: CONFORME" in restconf_text
    )

    snapshot_files = archivos_no_vacios(SNAPSHOT_FINAL_DIR)
    diff_files = archivos_no_vacios(DIFF_DIR)
    diff_text = consolidar_diff()

    snapshot_ok = SNAPSHOT_FINAL_DIR.exists() and len(snapshot_files) >= 3
    diff_ok = DIFF_DIR.exists() and len(diff_files) > 0 and "NO SE DETECTARON" not in diff_text

    compliance_ok = netconf_ok and restconf_ok and snapshot_ok and diff_ok

    certificado = f"""
================================================================================
CERTIFICADO DE COMPLIANCE — EP3 DRY7122
================================================================================

Fecha de emision : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Host VM          : {socket.gethostname()}

DATOS DEL ALUMNO
--------------------------------------------------------------------------------
Codigo           : {codigo}
Nombre           : {nombre}

DATOS DEL CLIENTE
--------------------------------------------------------------------------------
Empresa cliente  : {empresa}
Router IP        : {router_ip}
Hostname final   : {hostname}

CONFIGURACION CORPORATIVA VALIDADA
--------------------------------------------------------------------------------
Hostname         : {hostname}
Loopback gestion : {loopback_ip} {loopback_mask}
Descripcion WAN  : {descripcion_wan}
Banner acceso    : {banner}
Servidor NTP     : {ntp_server}

EVIDENCIAS GENERADAS
--------------------------------------------------------------------------------
Snapshot final   : {SNAPSHOT_FINAL_DIR}
Archivos snapshot: {len(snapshot_files)}
Diff baseline    : {DIFF_DIR}
Archivos diff    : {len(diff_files)}
Diff consolidado : {DIFF_TXT}
NETCONF output   : {NETCONF_OUTPUT}
RESTCONF output  : {RESTCONF_OUTPUT}

RESULTADOS DE VALIDACION
--------------------------------------------------------------------------------
NETCONF          : {estado_bool(netconf_ok)}
RESTCONF         : {estado_bool(restconf_ok)}
SNAPSHOT FINAL   : {estado_bool(snapshot_ok)}
GENIE DIFF       : {estado_bool(diff_ok)}

RESULTADO GLOBAL DE COMPLIANCE
--------------------------------------------------------------------------------
COMPLIANCE       : {estado_bool(compliance_ok)}

CONCLUSION
--------------------------------------------------------------------------------
El router {hostname} fue aprovisionado mediante Ansible y validado mediante
NETCONF, RESTCONF y Genie Diff. Las evidencias indican que el dispositivo cumple
con la configuracion corporativa definida para {empresa}.

================================================================================
""".strip()

    CERT_FILE.write_text(certificado + "\n", encoding="utf-8")

    print(certificado)
    print()
    print(f"[OK] Certificado generado: {CERT_FILE}")
    print(f"[OK] Diff consolidado generado: {DIFF_TXT}")

    if compliance_ok:
        print("[OK] Resultado final Fase 5: CONFORME")
    else:
        print("[FAIL] Resultado final Fase 5: NO CONFORME")
        sys.exit(1)


if __name__ == "__main__":
    main()
