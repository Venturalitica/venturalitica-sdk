# Referencia de Probes

El sistema de probes impulsa `vl.monitor()`. Cuando envuelves tu codigo en un context manager de monitor, 7 probes se activan automaticamente para capturar evidencia multimodal sobre tu entorno de ejecucion, linaje de datos y estado de cumplimiento normativo.

```python
with vl.monitor("training_run"):
    # Las 7 probes estan activas aqui
    model.fit(X, y)
    vl.enforce(data=df, policy="policy.oscal.yaml")
```

---

## Arquitectura de Probes

Todas las probes extienden `BaseProbe` e implementan:

- **`start()`** -- Se invoca cuando el context manager del monitor se abre
- **`stop()`** -- Se invoca cuando el context manager del monitor se cierra; devuelve un diccionario de resultados
- **`get_summary()`** -- Devuelve un resumen legible de una linea

Las probes estan disenadas para ser no invasivas: si una probe falla (por ejemplo, por una dependencia opcional ausente), se degrada silenciosamente sin interrumpir tu codigo.

---

## Referencia de Probes

### IntegrityProbe

**Proposito:** Genera una huella digital SHA-256 del entorno de ejecucion y detecta desviaciones.

**EU AI Act:** Articulo 15 (Precision, Robustez y Ciberseguridad)

**Que captura:**

| Campo | Descripcion |
| :--- | :--- |
| `fingerprint` | Hash SHA-256 de `{OS}-{Python version}-{CWD}` (primeros 12 caracteres) |
| `metadata.os` | Sistema operativo y version |
| `metadata.python` | Version de Python |
| `metadata.arch` | Arquitectura de CPU |
| `metadata.node` | Nombre de host de la maquina |
| `metadata.cwd` | Directorio de trabajo actual |
| `drift_detected` | `true` si la huella cambio entre start y stop |

**Ejemplo de salida:**
```
  [Security] Fingerprint: 89fbf3a21c04 | Integrity: Stable
```

**Por que importa:** Demuestra que el entorno no cambio durante la ejecucion. Si alguien sustituye el dataset o cambia el directorio de trabajo a mitad de ejecucion, la desviacion se detecta.

---

### HardwareProbe

**Proposito:** Registra el uso pico de RAM y el numero de CPUs.

**EU AI Act:** Articulo 15 (Precision, Robustez y Ciberseguridad)

**Que captura:**

| Campo | Descripcion |
| :--- | :--- |
| `peak_memory_mb` | Memoria pico RSS en megabytes |
| `cpu_count` | Numero de nucleos de CPU disponibles |

**Dependencia opcional:** `psutil` (se degrada correctamente si no esta instalado)

**Ejemplo de salida:**
```
  [Hardware] Peak Memory: 256.42 MB | CPUs: 8
```

---

### CarbonProbe

**Proposito:** Rastrea las emisiones de CO2 durante el entrenamiento usando CodeCarbon.

**EU AI Act:** Articulo 15 (Robustez -- reporte de impacto ambiental)

**Que captura:**

| Campo | Descripcion |
| :--- | :--- |
| `emissions_kg` | Emisiones de carbono estimadas en kilogramos de CO2 |

**Dependencia opcional:** `codecarbon` (muestra una advertencia si no esta instalado)

**Ejemplo de salida:**
```
  [Green AI] Carbon emissions: 0.000042 kgCO2
```

**Por que importa:** Algunos marcos regulatorios e informes ESG requieren la divulgacion del impacto de carbono para entrenamientos de IA intensivos en computo.

---

### BOMProbe

**Proposito:** Captura un SBOM (Software Bill of Materials) en tiempo de ejecucion.

**EU AI Act:** Articulo 13 (Transparencia e Informacion)

**Que captura:**

| Campo | Descripcion |
| :--- | :--- |
| `component_count` | Numero de paquetes Python en el entorno |
| `bom` | SBOM completo en formato JSON (compatible con CycloneDX) |
| `bom_path` | Ruta del archivo donde se guardo el SBOM |

**Donde se guarda:** `{session_dir}/bom.json` o `.venturalitica/bom.json`

**Ejemplo de salida:**
```
  [Supply Chain] BOM Captured: 142 components linked.
```

**Por que importa:** Se corresponde con los requisitos de transparencia del Articulo 13. El SBOM demuestra exactamente que versiones de librerias se utilizaron, habilitando la auditoria de vulnerabilidades en la cadena de suministro (escaneo de CVE).

---

### ArtifactProbe

**Proposito:** Rastrea artefactos de entrada y salida para el linaje de datos.

**EU AI Act:** Articulo 10 (Datos y Gobernanza de Datos)

**Parametros del constructor:**

| Parametro | Tipo | Descripcion |
| :--- | :--- | :--- |
| `inputs` | `List[str]` o `None` | Rutas a archivos de entrada (datasets, configuraciones) |
| `outputs` | `List[str]` o `None` | Rutas a archivos de salida (modelos, graficos) |

**Que captura:**

| Campo | Descripcion |
| :--- | :--- |
| `inputs` | Instantanea de los artefactos de entrada al inicio (nombre, hash, metadatos) |
| `outputs` | Instantanea de los artefactos de salida al finalizar |

**Uso:**

```python
with vl.monitor("training",
                inputs=["data/train.csv"],
                outputs=["models/credit_model.pkl"]):
    model.fit(X, y)
```

**Ejemplo de salida:**
```
  [Artifacts] Inputs: 1 | Outputs: 1 (Deep Integration)
```

---

### HandshakeProbe

**Proposito:** Verifica si `vl.enforce()` fue invocado dentro de la sesion del monitor.

**EU AI Act:** Articulo 9 (Sistema de Gestion de Riesgos)

**Que captura:**

| Campo | Descripcion |
| :--- | :--- |
| `is_compliant` | `true` si `enforce()` fue invocado en algun momento |
| `newly_enforced` | `true` si `enforce()` fue invocado durante esta sesion (no antes) |

**Ejemplo de salida (sin enforcement detectado):**
```
  [Handshake] Nudge: No policy enforcement detected yet. Run `vl.enforce()` to ensure compliance.
```

**Ejemplo de salida (enforcement detectado):**
```
  [Handshake] Policy enforced verifyable audit trail present.
```

**Por que importa:** Promueve el flujo de trabajo de cumplimiento. Si un desarrollador usa `monitor()` para entrenamiento pero olvida invocar `enforce()`, la probe Handshake le recuerda que debe aplicar la politica de cumplimiento.

---

### TraceProbe

**Proposito:** Captura evidencia logica de ejecucion, incluyendo analisis de codigo AST, marcas de tiempo y contexto de invocacion.

**EU AI Act:** Articulos 10 y 11 (Gobernanza de Datos y Documentacion Tecnica)

**Parametros del constructor:**

| Parametro | Tipo | Descripcion |
| :--- | :--- | :--- |
| `run_name` | `str` | Nombre para este trace (usado en el nombre del archivo) |
| `label` | `str` o `None` | Etiqueta opcional de categorizacion |

**Que captura:**

| Campo | Descripcion |
| :--- | :--- |
| `name` | Nombre de la ejecucion |
| `label` | Etiqueta opcional |
| `timestamp` | Marca de tiempo ISO-8601 al finalizar la sesion |
| `duration_seconds` | Tiempo de ejecucion en reloj de pared |
| `success` | `true` si no se lanzo ninguna excepcion |
| `code_context.file` | Nombre del script del usuario que invoco `monitor()` |
| `code_context.analysis` | Analisis AST del script (llamadas a funciones, imports, estructura) |

**Donde se guarda:** `{session_dir}/trace_{run_name}.json` o `.venturalitica/trace_{run_name}.json`

**Ejemplo de salida:**
```
  [Trace] Context: train_model.py | Evidence saved to .venturalitica/trace_credit_model_v1.json
```

**Por que importa:** El archivo de trace es el artefacto de evidencia principal. Demuestra no solo los resultados, sino COMO se calcularon -- que script se ejecuto, cuanto tiempo tomo y si finalizo exitosamente.

---

## Estructura del Directorio de Evidencia

Despues de una sesion de `monitor()`, la evidencia se guarda en:

```
.venturalitica/
  results.json              # resultados de enforce() (acumulativos)
  trace_{run_name}.json     # salida de TraceProbe
  bom.json                  # salida de BOMProbe
  sessions/
    {session_id}/
      results.json          # resultados de enforce() especificos de la sesion
      trace_{run_name}.json # trace especifico de la sesion
      bom.json              # SBOM especifico de la sesion
```

El Dashboard lee estos archivos para poblar la Fase 3 (Verificar y Evaluar).

---

## Dependencias de las Probes

| Probe | Requerida | Dependencia opcional |
| :--- | :--- | :--- |
| IntegrityProbe | Incluida | -- |
| HardwareProbe | Incluida | `psutil` (para datos de memoria/CPU) |
| CarbonProbe | Incluida | `codecarbon` (para rastreo de emisiones) |
| BOMProbe | Incluida | -- |
| ArtifactProbe | Incluida | -- |
| HandshakeProbe | Incluida | -- |
| TraceProbe | Incluida | -- |

Instalar dependencias opcionales:

```bash
pip install psutil codecarbon
```
