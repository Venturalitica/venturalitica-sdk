# Vinculacion de Columnas (Column Binding)

Venturalitica utiliza un sistema de **vinculacion de columnas basado en sinonimos** para mapear conceptos abstractos (como "gender" o "age") a nombres reales de columnas en un DataFrame (como "Attribute9" o "Attribute13"). Esto desacopla las politicas OSCAL de los esquemas especificos de cada conjunto de datos.

---

## Como Funciona

Cuando se invoca `vl.enforce()`, el SDK resuelve los nombres de columna en tres pasos:

1. **Parametros explicitos**: Verifica si los valores de `target` o `prediction` existen como nombres de columna
2. **Descubrimiento por sinonimos**: Busca el nombre de la columna en `COLUMN_SYNONYMS`
3. **Fallback en minusculas**: Intenta una coincidencia sin distinguir mayusculas de minusculas

### Ejemplo

```python
vl.enforce(
    data=df,
    target="class",          # Explicito: busca la columna 'class'
    gender="Attribute9",     # Mapeo de atributo: 'gender' -> 'Attribute9'
    age="Attribute13",       # Mapeo de atributo: 'age' -> 'Attribute13'
    policy="data_policy.oscal.yaml"
)
```

En la politica OSCAL, los controles referencian nombres abstractos como `gender` y `age` mediante `input:dimension`. El SDK los resuelve a las columnas reales en tiempo de ejecucion.

---

## Diccionario de Sinonimos

El diccionario integrado `COLUMN_SYNONYMS` mapea roles semanticos a variantes conocidas de nombres de columna:

| Rol | Sinonimos Conocidos |
| :--- | :--- |
| `gender` | `sex`, `gender`, `sexo`, `Attribute9` |
| `age` | `age`, `age_group`, `edad`, `Attribute13` |
| `race` | `race`, `ethnicity`, `raza` |
| `target` | `target`, `class`, `label`, `y`, `true_label`, `ground_truth`, `approved`, `default`, `outcome` |
| `prediction` | `prediction`, `pred`, `y_pred`, `predictions`, `score`, `proba`, `output` |
| `dimension` | `sex`, `gender`, `age`, `race`, `Attribute9`, `Attribute13` |

### Descubrimiento Automatico

Si no se proporciona un mapeo de columnas de forma explicita, el SDK descubre automaticamente las columnas escaneando el DataFrame en busca de sinonimos conocidos:

```python
# Estas dos llamadas son equivalentes para el dataset UCI German Credit:
vl.enforce(data=df, target="class", gender="Attribute9")
vl.enforce(data=df)  # Descubre automaticamente 'class' como target y 'Attribute9' como gender
```

---

## Funciones de Resolucion

### `discover_column(requested, context_mapping, data, synonyms)`

Descubre una columna individual usando el siguiente orden de prioridad:

1. Verificar `context_mapping` (mapeo proporcionado explicitamente por el usuario)
2. Verificar si `requested` es un nombre de columna directo
3. Buscar en `COLUMN_SYNONYMS` un grupo coincidente
4. Fallback en minusculas
5. Devolver `"MISSING"` si no se encuentra

### `resolve_col_names(val, data, synonyms)`

Resuelve uno o mas nombres de columna a partir de una cadena o lista:

- Soporta cadenas separadas por comas: `"target, gender"`
- Soporta listas: `["target", "gender"]`
- Devuelve una lista de nombres de columna resueltos

---

## El Handshake entre Politica y Codigo

La vinculacion de columnas conecta los **requisitos legales** (politicas OSCAL) con la **realidad tecnica** (DataFrames desordenados):

```
Politica OSCAL                  Codigo Python                DataFrame
+--------------+    enforce()   +-----------+    binding     +------------+
| dimension:   | ------------> | gender=   | ------------> | Attribute9 |
|   gender     |               | "Attr..."  |               | (columna   |
| threshold:   |               |            |               |  real)     |
|   > 0.8      |               |            |               |            |
+--------------+               +-----------+               +------------+
```

Este diseno implica que:

- **Los Oficiales de Cumplimiento** redactan politicas usando nombres abstractos (`gender`, `age`)
- **Los Ingenieros** proporcionan el mapeo a los nombres tecnicos de columna una sola vez
- **La misma politica** funciona en distintos conjuntos de datos con esquemas diferentes

---

## Soporte Multilingue

El diccionario de sinonimos incluye traducciones al espanol:

- `gender` = `sexo`
- `age` = `edad`
- `race` = `raza`

Esto permite utilizar conjuntos de datos con encabezados de columna en espanol sin necesidad de un mapeo explicito.

---

## Sinonimos Personalizados

Es posible extender el diccionario de sinonimos de forma programatica:

```python
from venturalitica.binding import COLUMN_SYNONYMS

# Agregar un sinonimo personalizado para su conjunto de datos
COLUMN_SYNONYMS["income"] = ["income", "salary", "wage", "earnings", "ingreso"]
```

O pasar un diccionario de sinonimos personalizado a las funciones de resolucion:

```python
from venturalitica.binding import resolve_col_names

custom_synonyms = {
    "risk_score": ["risk", "risk_score", "risk_level", "riesgo"],
}
resolved = resolve_col_names("risk_score", df, synonyms=custom_synonyms)
```
