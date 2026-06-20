#!/usr/bin/env python3
import re
import socket
import sys
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

import yaml
from ncclient import manager


BASE_DIR = Path(__file__).resolve().parents[1]
VARS_FILE = BASE_DIR / "vars" / "vars_005D-12.yaml"
EVID_DIR = Path(__file__).resolve().parent / "evidencias"
RAW_XML_FILE = EVID_DIR / "rpc_reply_raw.xml"


def cargar_vars():
    if not VARS_FILE.exists():
        print(f"[FAIL] No existe archivo de variables: {VARS_FILE}")
        sys.exit(1)

    with open(VARS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def obtener(data, ruta, requerido=True, defecto=None):
    actual = data
    for clave in ruta:
        if isinstance(actual, dict) and clave in actual:
            actual = actual[clave]
        else:
            if requerido:
                print(f"[FAIL] Falta variable en vars: {'.'.join(ruta)}")
                sys.exit(1)
            return defecto
    return actual


def local_name(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def iter_local(root, nombre):
    for elem in root.iter():
        if local_name(elem.tag) == nombre:
            yield elem


def first_text(root, nombre):
    for elem in iter_local(root, nombre):
        if elem.text and elem.text.strip():
            return elem.text.strip()
    return None


def first_text_in(node, nombre):
    if node is None:
        return None
    for elem in node.iter():
        if local_name(elem.tag) == nombre and elem.text and elem.text.strip():
            return elem.text.strip()
    return None


def all_texts(node):
    if node is None:
        return []
    textos = []
    for elem in node.iter():
        if elem.text and elem.text.strip():
            textos.append(elem.text.strip())
    return textos


def buscar_interfaz(root, tipo, numero):
    numero = str(numero)
    for elem in iter_local(root, tipo):
        nombre = first_text_in(elem, "name")
        if str(nombre) == numero:
            return elem
    return None


def validar(label, esperado, obtenido):
    if str(esperado) == str(obtenido):
        print(f"[OK] {label}: esperado='{esperado}' obtenido='{obtenido}'")
        return True
    print(f"[FAIL] {label}: esperado='{esperado}' obtenido='{obtenido}'")
    return False


def main():
    EVID_DIR.mkdir(parents=True, exist_ok=True)

    data = cargar_vars()

    codigo = obtener(data, ["alumno", "codigo"])
    nombre = obtener(data, ["alumno", "nombre"])
    router_ip = obtener(data, ["router", "ip"])
    usuario = obtener(data, ["router", "usuario"])
    password = obtener(data, ["router", "password"])

    hostname_esperado = obtener(data, ["cliente", "hostname"])
    loopback_id = obtener(data, ["router", "loopback_id"])
    loopback_ip = obtener(data, ["router", "loopback_ip"])
    loopback_mask = obtener(data, ["router", "loopback_mask"])
    descripcion_wan = obtener(data, ["router", "descripcion_wan"])
    ntp_server = obtener(data, ["router", "ntp_server"])

    print("=== VALIDACION NETCONF ===")
    print("Script : validacion_netconf.py")
    print(f"Alumno : {codigo} - {nombre}")
    print(f"Fecha  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Host VM: {socket.gethostname()}")
    print(f"Router : {router_ip}")
    print("==========================")
    print()

    filtro_native = """
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    </native>
    """

    try:
        with manager.connect(
            host=router_ip,
            port=830,
            username=usuario,
            password=password,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
            timeout=60,
            device_params={"name": "csr"},
        ) as m:
            respuesta = m.get_config(source="running", filter=("subtree", filtro_native))
            raw_xml = respuesta.xml

    except Exception as e:
        print(f"[FAIL] Error conectando por NETCONF: {e}")
        sys.exit(1)

    RAW_XML_FILE.write_text(raw_xml, encoding="utf-8")

    print(f"[OK] XML crudo guardado en: {RAW_XML_FILE}")
    print(f"[OK] Tamano XML: {RAW_XML_FILE.stat().st_size} bytes")

    message_id_match = re.search(r'message-id="([^"]+)"', raw_xml)
    message_id = message_id_match.group(1) if message_id_match else "NO ENCONTRADO"

    uuid_ok = bool(
        re.match(
            r"^urn:uuid:[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
            message_id,
        )
    )

    if uuid_ok:
        print(f"[OK] message-id UUID valido: {message_id}")
    else:
        print(f"[FAIL] message-id UUID invalido o no encontrado: {message_id}")

    print()

    try:
        root = ET.fromstring(raw_xml.encode("utf-8"))
    except Exception as e:
        print(f"[FAIL] No se pudo parsear XML NETCONF: {e}")
        sys.exit(1)

    hostname_obtenido = first_text(root, "hostname")

    loopback_node = buscar_interfaz(root, "Loopback", loopback_id)
    loopback_textos = all_texts(loopback_node)

    loopback_ip_obtenida = loopback_ip if loopback_ip in loopback_textos or loopback_ip in raw_xml else "NO ENCONTRADA"
    loopback_mask_obtenida = loopback_mask if loopback_mask in loopback_textos or loopback_mask in raw_xml else "NO ENCONTRADA"

    wan_node = buscar_interfaz(root, "GigabitEthernet", "1")
    descripcion_wan_obtenida = first_text_in(wan_node, "description")

    ntp_obtenido = ntp_server if ntp_server in raw_xml else "NO ENCONTRADO"

    print("=== CRITERIOS DE CONFIGURACION ===")

    resultados = []
    resultados.append(validar("Hostname corporativo", hostname_esperado, hostname_obtenido))
    resultados.append(validar("IP Loopback", loopback_ip, loopback_ip_obtenida))
    resultados.append(validar("Mascara Loopback", loopback_mask, loopback_mask_obtenida))
    resultados.append(validar("Descripcion WAN", descripcion_wan, descripcion_wan_obtenida))
    resultados.append(validar("Servidor NTP", ntp_server, ntp_obtenido))

    ok = sum(resultados)
    total = len(resultados)

    print()
    print(f"Resultado validaciones: {ok}/{total} OK")

    if ok == total and uuid_ok:
        print("Resultado global: CONFORME")
    else:
        print("Resultado global: NO CONFORME")
        sys.exit(1)


if __name__ == "__main__":
    main()
