#!/usr/bin/env python3
import json
import socket
import sys
from datetime import datetime
from pathlib import Path

import requests
import urllib3
import yaml


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).resolve().parents[1]
VARS_FILE = BASE_DIR / "vars" / "vars_005D-12.yaml"
EVID_DIR = Path(__file__).resolve().parent / "evidencias"


def cargar_vars():
    if not VARS_FILE.exists():
        print(f"[FAIL] No existe archivo de variables: {VARS_FILE}")
        sys.exit(1)

    with open(VARS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def obtener(data, ruta):
    actual = data
    for clave in ruta:
        if isinstance(actual, dict) and clave in actual:
            actual = actual[clave]
        else:
            print(f"[FAIL] Falta variable en vars: {'.'.join(ruta)}")
            sys.exit(1)
    return actual


def guardar_json(nombre_archivo, data):
    EVID_DIR.mkdir(parents=True, exist_ok=True)
    ruta = EVID_DIR / nombre_archivo
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return ruta


def get_restconf(base_url, endpoint, usuario, password):
    headers = {
        "Accept": "application/yang-data+json",
        "Content-Type": "application/yang-data+json",
    }

    url = f"{base_url}{endpoint}"

    response = requests.get(
        url,
        headers=headers,
        auth=(usuario, password),
        verify=False,
        timeout=30,
    )

    if response.status_code not in [200, 201, 204]:
        print(f"[FAIL] Error RESTCONF GET {endpoint}")
        print(f"Status code: {response.status_code}")
        print(response.text)
        sys.exit(1)

    if not response.text.strip():
        return {}

    return response.json()


def texto_json(data):
    return json.dumps(data, ensure_ascii=False)


def validar(label, esperado, contenido):
    contenido_str = texto_json(contenido)

    if str(esperado) in contenido_str:
        print(f"[OK] {label}: encontrado '{esperado}'")
        return True

    print(f"[FAIL] {label}: no encontrado '{esperado}'")
    return False


def main():
    data = cargar_vars()

    codigo = obtener(data, ["alumno", "codigo"])
    nombre = obtener(data, ["alumno", "nombre"])

    router_ip = obtener(data, ["router", "ip"])
    usuario = obtener(data, ["router", "usuario"])
    password = obtener(data, ["router", "password"])

    hostname_esperado = obtener(data, ["cliente", "hostname"])
    loopback_id = obtener(data, ["router", "loopback_id"])
    loopback_ip = obtener(data, ["router", "loopback_ip"])
    descripcion_wan = obtener(data, ["router", "descripcion_wan"])
    ntp_server = obtener(data, ["router", "ntp_server"])

    base_url = f"https://{router_ip}/restconf/data"

    print("=== VALIDACION RESTCONF ===")
    print("Script : validacion_restconf.py")
    print(f"Alumno : {codigo} - {nombre}")
    print(f"Fecha  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Host VM: {socket.gethostname()}")
    print(f"Router : {router_ip}")
    print("===========================")
    print()

    endpoints = {
        "hostname": "/Cisco-IOS-XE-native:native/hostname",
        "loopback": f"/Cisco-IOS-XE-native:native/interface/Loopback={loopback_id}",
        "interfaces": "/Cisco-IOS-XE-native:native/interface",
        "ntp": "/Cisco-IOS-XE-native:native/ntp",
    }

    print("=== CONSULTAS RESTCONF ===")

    get_hostname = get_restconf(base_url, endpoints["hostname"], usuario, password)
    ruta_hostname = guardar_json("get_hostname.json", get_hostname)
    print(f"[OK] GET hostname guardado en {ruta_hostname}")

    get_loopback = get_restconf(base_url, endpoints["loopback"], usuario, password)
    ruta_loopback = guardar_json("get_loopback.json", get_loopback)
    print(f"[OK] GET loopback guardado en {ruta_loopback}")

    get_interfaces = get_restconf(base_url, endpoints["interfaces"], usuario, password)
    ruta_interfaces = guardar_json("get_interfaces.json", get_interfaces)
    print(f"[OK] GET interfaces guardado en {ruta_interfaces}")

    get_ntp = get_restconf(base_url, endpoints["ntp"], usuario, password)
    ruta_ntp = guardar_json("get_ntp.json", get_ntp)
    print(f"[OK] GET ntp guardado en {ruta_ntp}")

    print()
    print("=== CRITERIOS DE VALIDACION ===")

    resultados = []
    resultados.append(validar("Hostname corporativo", hostname_esperado, get_hostname))
    resultados.append(validar("IP Loopback", loopback_ip, get_loopback))
    resultados.append(validar("Descripcion WAN", descripcion_wan, get_interfaces))
    resultados.append(validar("Servidor NTP", ntp_server, get_ntp))

    ok = sum(resultados)
    total = len(resultados)

    print()
    print(f"Resultado validaciones: {ok}/{total} OK")

    if ok == total:
        print("Resultado global: CONFORME")
    else:
        print("Resultado global: NO CONFORME")
        sys.exit(1)


if __name__ == "__main__":
    main()
