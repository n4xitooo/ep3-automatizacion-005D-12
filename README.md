# Informe Técnico de Compliance — EP3 DRY7122

## Objetivo del proyecto

El objetivo de este proyecto fue implementar un ciclo completo de automatización de red para la empresa AutoMotores del Sur SA, utilizando herramientas de automatización, validación y control de versiones. El trabajo consideró la captura del estado inicial del router, el aprovisionamiento automatizado de la configuración corporativa, la validación posterior mediante NETCONF y RESTCONF, y la generación de evidencias técnicas para certificar el cumplimiento de la configuración solicitada.

El resultado esperado fue dejar el router configurado, validado y documentado como conforme, manteniendo evidencia organizada en un repositorio GitHub.

## Alcance

El alcance del proyecto incluyó la creación del repositorio, la definición de variables corporativas, la captura del baseline inicial con Genie, el aprovisionamiento mediante Ansible, la validación mediante scripts Python usando NETCONF y RESTCONF, y la generación de un reporte final de compliance.

El trabajo se realizó sobre un router Cisco CSR1kv en ambiente de laboratorio. No se consideró configuración avanzada de enrutamiento, alta disponibilidad, monitoreo continuo ni integración con pipelines externos.

## Infraestructura utilizada

La infraestructura utilizada estuvo compuesta por una máquina virtual DEVASC y un router Cisco CSR1kv. La VM fue utilizada como estación de trabajo para ejecutar Git, pyATS/Genie, Ansible y scripts Python.

Elementos principales:

* VM DEVASC: labvm.
* Router: Cisco CSR1kv.
* IP de administración: 192.168.56.101.
* Usuario de acceso: cisco.
* Repositorio: ep3-automatizacion-005D-12.
* Código asignado: 005D-12.

## Tecnologías empleadas y justificación

Se utilizó Git y GitHub para mantener control de versiones y respaldar las evidencias generadas durante cada fase del proyecto.

pyATS/Genie se utilizó para capturar el baseline inicial del router, generar un snapshot final y comparar ambos estados mediante Genie Diff. Esto permitió documentar los cambios aplicados al dispositivo.

Ansible se utilizó para realizar el aprovisionamiento automatizado del router. El playbook fue construido usando variables externas para evitar valores hardcodeados y permitir una configuración reutilizable e idempotente.

NETCONF fue utilizado mediante la librería ncclient para validar la configuración activa del router en formato XML.

RESTCONF fue utilizado mediante la librería requests para consultar información del router en formato JSON, permitiendo una segunda validación independiente.

Python se utilizó para automatizar las validaciones y generar el certificado final de compliance.

## Configuración aplicada

La configuración corporativa aplicada al router fue la siguiente:

| Parámetro            | Valor                        |
| -------------------- | ---------------------------- |
| Empresa cliente      | AutoMotores del Sur SA       |
| Código alumno        | 005D-12                      |
| Hostname corporativo | RTR-AUTOSUR                  |
| IP de administración | 192.168.56.101               |
| Loopback de gestión  | 10.5.12.1                    |
| Máscara Loopback     | 255.255.255.0                |
| Descripción WAN      | Enlace-WAN-Calama            |
| Banner               | ACCESO RESTRINGIDO - AUTOSUR |
| Servidor NTP         | 208.67.222.222               |
| NETCONF              | Habilitado                   |
| RESTCONF             | Habilitado                   |
| HTTP secure-server   | Habilitado                   |

## Resultados de validación

Los resultados obtenidos fueron conformes en las fases principales del proyecto.

| Validación                    | Herramienta       | Resultado |
| ----------------------------- | ----------------- | --------- |
| Baseline inicial              | Genie             | CONFORME  |
| Aprovisionamiento inicial     | Ansible           | CONFORME  |
| Segunda ejecución idempotente | Ansible           | CONFORME  |
| Validación NETCONF            | Python + ncclient | CONFORME  |
| Validación RESTCONF           | Python + requests | CONFORME  |
| Snapshot final                | Genie             | CONFORME  |
| Diff baseline vs final        | Genie Diff        | CONFORME  |
| Certificado de compliance     | Python            | CONFORME  |

La segunda ejecución de Ansible finalizó con `changed=0` y `failed=0`, demostrando que el playbook es idempotente. Además, las validaciones NETCONF y RESTCONF confirmaron que los parámetros configurados coinciden con los valores corporativos esperados.

## Conclusiones

El proyecto permitió implementar un proceso completo de automatización de red, desde la captura inicial del estado del router hasta la generación de un certificado final de compliance. El uso de variables externas permitió evitar configuraciones hardcodeadas dentro del playbook, facilitando la reutilización y mantención del código.

Ansible permitió aplicar la configuración corporativa de manera controlada e idempotente. Las validaciones mediante NETCONF y RESTCONF comprobaron de forma independiente que el router quedó correctamente configurado. Finalmente, Genie permitió comparar el estado inicial y final del equipo, dejando evidencia de los cambios realizados.

Con base en las evidencias generadas, el router RTR-AUTOSUR queda en estado CONFORME para la empresa AutoMotores del Sur SA.
