# Referencia de API

Venturalitica expone cinco simbolos publicos. Esta pagina documenta sus firmas exactas y comportamiento a partir de la v0.5.0.

---

## Funciones Principales

### `quickstart(scenario, verbose=True)`

Ejecuta una demostracion preconfigurada de auditoria de sesgo sobre un conjunto de datos estandar. Es la forma mas rapida de ver el SDK en accion.

```python
import venturalitica as vl

results = vl.quickstart("loan")
```

| Parametro | Tipo | Por defecto | Descripcion |
| :--- | :--- | :--- | :--- |
| `scenario` | `str` | *(requerido)* | Nombre del escenario predefinido: `"loan"`, `"hiring"`, `"health"`. |
| `verbose` | `bool` | `True` | Imprime la tabla estructurada de cumplimiento en la consola. |

**Retorna:** `List[ComplianceResult]`

!!! note
    `quickstart()` es un envoltorio de conveniencia. Internamente carga un conjunto de datos, resuelve una politica OSCAL incorporada y llama a `enforce()`. Es util para demos y experiencias de primer contacto.

---

### `enforce()`

El punto de entrada principal para auditar conjuntos de datos y modelos contra politicas OSCAL.

```python
def enforce(
    data=None,
    metrics=None,
    policy="risks.oscal.yaml",
    target="target",
    prediction="prediction",
    strict=False,
    **attributes,
) -> List[ComplianceResult]
```

| Parametro | Tipo | Por defecto | Descripcion |
| :--- | :--- | :--- | :--- |
| `data` | `DataFrame` o `None` | `None` | DataFrame de Pandas que contiene caracteristicas, objetivos y, opcionalmente, predicciones. |
| `metrics` | `Dict[str, float]` o `None` | `None` | Diccionario de metricas precalculadas. Usalo cuando ya hayas calculado tus metricas de forma externa. |
| `policy` | `str`, `Path` o `List` | `"risks.oscal.yaml"` | Ruta a uno o mas archivos de politica OSCAL. Pasa una lista para aplicar multiples politicas en una sola llamada. |
| `target` | `str` | `"target"` | Nombre de la columna que contiene las etiquetas de verdad fundamental. |
| `prediction` | `str` | `"prediction"` | Nombre de la columna que contiene las predicciones del modelo. |
| `strict` | `bool` | `False` | Si es `True`, las metricas faltantes, variables no vinculadas y errores de calculo generan excepciones en lugar de omitirse. Se activa automaticamente cuando `CI=true` o `VENTURALITICA_STRICT=true`. |
| `**attributes` | keyword args | | Mapeos para variables protegidas y dimensiones. Por ejemplo: `gender="Attribute9"`, `age="Attribute13"`. |

**Retorna:** `List[ComplianceResult]`

#### Dos Modos de Operacion

**Modo 1: Basado en DataFrame** (el mas comun). Pasa un DataFrame y deja que el SDK calcule las metricas automaticamente:

```python
results = vl.enforce(
    data=df,
    target="class",
    prediction="prediction",
    gender="Attribute9",     # mapea 'gender' abstracto -> columna 'Attribute9'
    age="Attribute13",       # mapea 'age' abstracto -> columna 'Attribute13'
    policy="data_policy.oscal.yaml",
)
```

**Modo 2: Metricas precalculadas**. Pasa un diccionario de valores ya calculados:

```python
results = vl.enforce(
    metrics={"accuracy_score": 0.92, "demographic_parity_diff": 0.07},
    policy="model_policy.oscal.yaml",
)
```

#### Vinculacion de Columnas

Al usar el modo DataFrame, el SDK resuelve los nombres de columna mediante un sistema de sinonimos (ver [Vinculacion de Columnas](column-binding.md)):

- `target` y `prediction` se resuelven primero a traves de los parametros explicitos, y luego mediante descubrimiento de sinonimos.
- `**attributes` (p.ej., `gender="Attribute9"`) se pasan directamente a las funciones de metricas como el parametro `dimension`.
- Si no se encuentra una columna, el SDK recurre a coincidencia en minusculas.

#### Cache de Resultados

`enforce()` almacena automaticamente los resultados en cache en `.venturalitica/results.json` y, si se ejecuta dentro de una sesion `monitor()`, en el directorio de evidencia especifico de la sesion. Ejecuta `venturalitica ui` para visualizar los resultados almacenados.

#### Multiples Politicas

Pasa una lista para aplicar varias politicas en una sola llamada:

```python
results = vl.enforce(
    data=df,
    target="class",
    policy=["data_policy.oscal.yaml", "model_policy.oscal.yaml"],
    gender="Attribute9",
)
```

---

### `monitor(name, label=None, inputs=None, outputs=None)`

Un gestor de contexto que registra telemetria multimodal durante el entrenamiento o la evaluacion. Captura automaticamente evidencia de hardware, carbono, seguridad y auditoria.

```python
@contextmanager
def monitor(
    name="Training Task",
    label=None,
    inputs=None,
    outputs=None,
)
```

| Parametro | Tipo | Por defecto | Descripcion |
| :--- | :--- | :--- | :--- |
| `name` | `str` | `"Training Task"` | Nombre legible para esta sesion de monitoreo. Se usa en los nombres de archivos de traza. |
| `label` | `str` o `None` | `None` | Etiqueta opcional para categorizacion (p.ej., `"pre-training"`, `"validation"`). |
| `inputs` | `List[str]` o `None` | `None` | Rutas a artefactos de entrada (conjuntos de datos, configuraciones) para el rastreo de linaje de datos. |
| `outputs` | `List[str]` o `None` | `None` | Rutas a artefactos de salida (modelos, graficos) para el rastreo de linaje. |

#### Uso

```python
with vl.monitor("credit_model_v1"):
    model.fit(X_train, y_train)
    vl.enforce(data=df, policy="policy.oscal.yaml", target="class")
```

#### Sondas Recopiladas

`monitor()` inicializa 7 sondas automaticamente. Consulta la [Referencia de Sondas](probes.md) para mas detalles.

| Sonda | Que Captura | Articulo de la Ley de IA de la UE |
| :--- | :--- | :--- |
| `IntegrityProbe` | Huella digital SHA-256 del entorno, deteccion de deriva | Art. 15 |
| `HardwareProbe` | Pico de RAM, numero de CPUs | Art. 15 |
| `CarbonProbe` | Emisiones de CO2 via CodeCarbon | Art. 15 |
| `BOMProbe` | Lista de Materiales de Software (SBOM) | Art. 13 |
| `ArtifactProbe` | Linaje de datos de entrada/salida | Art. 10 |
| `HandshakeProbe` | Si `enforce()` fue llamado dentro de la sesion | Art. 9 |
| `TraceProbe` | Analisis AST del codigo, marcas de tiempo, contexto de llamada | Art. 11 |

La evidencia se guarda en `.venturalitica/` o en un directorio especifico de la sesion.

---

### `wrap(model, policy)` -- Experimental

!!! danger "VISTA PREVIA"
    Esta funcion es experimental y su API podria cambiar.

Audita transparentemente tu modelo durante flujos de trabajo estandar de Scikit-Learn, interceptando `.fit()` y `.predict()`.

| Parametro | Tipo | Descripcion |
| :--- | :--- | :--- |
| `model` | `object` | Cualquier clasificador o regresor compatible con Scikit-learn. |
| `policy` | `str` | Ruta a la politica OSCAL para evaluacion. |

**Retorna:** `AssuranceWrapper` (preserva la API original del modelo: `.fit()`, `.predict()`, etc.)

```python
wrapped = vl.wrap(LogisticRegression(), policy="model_policy.oscal.yaml")
wrapped.fit(X_train, y_train)
preds = wrapped.predict(X_test)  # La auditoria se ejecuta automaticamente
```

---

## Clase de Utilidad

### `PolicyManager`

Acceso programatico a la carga y manipulacion de politicas OSCAL.

```python
from venturalitica import PolicyManager
```

---

## Tipos de Datos

### `ComplianceResult`

Cada llamada a `enforce()` retorna una lista de instancias del dataclass `ComplianceResult`:

| Campo | Tipo | Descripcion |
| :--- | :--- | :--- |
| `control_id` | `str` | El identificador del control en la politica (p.ej., `"credit-data-bias"`). |
| `description` | `str` | Descripcion legible del control. |
| `metric_key` | `str` | La funcion de metrica utilizada (p.ej., `"disparate_impact"`). |
| `actual` | `float` | El valor calculado de la metrica. |
| `threshold` | `float` | El umbral definido en la politica. |
| `operator` | `str` | Operador de comparacion (`">"`, `"<"`, `">="`, `"<="`, `"=="`, `"gt"`, `"lt"`). |
| `passed` | `bool` | Si el control fue aprobado. |

```python
for r in results:
    print(f"{r.control_id}: {r.actual:.3f} {'PASS' if r.passed else 'FAIL'}")
```
