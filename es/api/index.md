# Referencia de API

Venturalítica proporciona una interfaz simple y unificada para la gobernanza de IA.

______________________________________________________________________

## 🚀 Funciones Principales

### `quickstart(scenario, verbose=True)`

Ejecuta una demostración de auditoría de sesgo preconfigurada en un conjunto de datos estándar.

| Parámetro  | Tipo   | Descripción                                                 |
| ---------- | ------ | ----------------------------------------------------------- |
| `scenario` | `str`  | Escenario predefinido: `'loan'`, `'hiring'`, `'health'`.    |
| `verbose`  | `bool` | Si imprimir el reporte de tabla estructurado en la consola. |

**Retorna:** `List[ComplianceResult]`

______________________________________________________________________

### `enforce(data, target, prediction=None, policy=None, **attributes)`

El punto de entrada principal para auditar conjuntos de datos y modelos.

| Parámetro      | Tipo         | Descripción                                                                               |
| -------------- | ------------ | ----------------------------------------------------------------------------------------- |
| `data`         | `DataFrame`  | DataFrame de Pandas conteniendo características, objetivos, y opcionalmente predicciones. |
| `target`       | `str`        | Nombre de la columna con etiquetas de verdad fundamental.                                 |
| `prediction`   | `str\|array` | (Opcional) Nombre de columna o array de predicciones del modelo.                          |
| `policy`       | `str`        | Ruta al archivo de política OSCAL/YAML.                                                   |
| `**attributes` | `str`        | Mapeos para variables protegidas (ej., `gender="attr9"`, `age="age_col"`).                |

**Retorna:** `List[ComplianceResult]`

Note

Si se omite `prediction`, las métricas de equidad recurren automáticamente a usar `target` para auditar el sesgo de datos.

______________________________________________________________________

### `wrap(model, policy)` (Experimental)

VISTA PREVIA

Esta función es experimental y su API podría cambiar.

Audita transparentemente tu modelo durante flujos de trabajo estándar de Scikit-Learn.

| Parámetro | Tipo     | Descripción                                                    |
| --------- | -------- | -------------------------------------------------------------- |
| `model`   | `object` | Cualquier clasificador o regresor compatible con Scikit-learn. |
| `policy`  | `str`    | Ruta a la política para evaluación.                            |

**Retorna:** `GovernanceWrapper` (Preserva la API original como `.fit()` y `.predict()`).

______________________________________________________________________

### `monitor(name)`

Un gestor de contexto para rastrear métricas de entrenamiento, salud del hardware e impacto ambiental.

```
with vl.monitor(name="CreditModel-v1"):
    model.fit(X, y)
```

**Telemetría Recolectada:**

- **⏱ Duración**: Tiempo de ejecución del bloque.
- **🌱 Emisiones**: Huella de carbono (requiere `codecarbon`).
- **🛡 Estabilidad**: Huella digital del modelo y verificación de integridad.

______________________________________________________________________

## 🛠 Funciones de Utilidad

### `list_scenarios()`

Retorna un diccionario de escenarios disponibles y sus descripciones.

### `load_sample(scenario)`

Carga el conjunto de datos UCI correspondiente para un escenario como un DataFrame de Pandas.
