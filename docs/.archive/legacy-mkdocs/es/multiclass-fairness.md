# Metricas de Equidad Multiclase

Venturalitica incluye 7 metricas de equidad multiclase para evaluar sistemas de IA con mas de 2 clases de salida (por ejemplo, grados de riesgo crediticio A/B/C/D, clasificacion multi-etiqueta, categorias de sentimiento). Estas extienden los conceptos tradicionales de equidad binaria a escenarios multiclase.

## Cuando Usar Metricas Multiclase

Utilice estas metricas cuando su modelo produce **3+ clases**. Las metricas binarias como `disparate_impact` o `demographic_parity_diff` solo funcionan con salidas de 2 clases. Las metricas multiclase agregan la equidad a traves de todas las etiquetas de clase.

Escenarios comunes:

- Calificacion de riesgo crediticio (A, B, C, D, E)
- Categorias de recomendacion de empleo
- Clasificacion de diagnostico medico
- Etiquetas de moderacion de contenido

---

## Referencia de Metricas

### 1. `multiclass_demographic_parity`

**Que mide**: Disparidad maxima en las tasas de prediccion entre grupos protegidos, agregada sobre todas las clases usando descomposicion one-vs-rest.

**Formula**: Para cada clase `c`, se calcula `P(Y_hat=c | A=a)` para cada grupo `a`. La disparidad para la clase `c` es `max(rates) - min(rates)`. Se devuelve la disparidad maxima entre todas las clases.

**Valor ideal**: 0.0 (todos los grupos reciben cada clase en tasas iguales).

**Registry key**: `multiclass_demographic_parity`

**Entradas requeridas**: `target`, `prediction`, `dimension`

```yaml
- control-id: mc-demographic-parity
  description: "Multi-class demographic parity < 0.15"
  props:
    - name: metric_key
      value: multiclass_demographic_parity
    - name: threshold
      value: "0.15"
    - name: operator
      value: lt
    - name: "input:target"
      value: target
    - name: "input:prediction"
      value: prediction
    - name: "input:dimension"
      value: gender
```

---

### 2. `multiclass_equal_opportunity`

**Que mide**: Disparidad maxima en las tasas de verdaderos positivos (TPR) entre grupos protegidos, usando descomposicion one-vs-rest. Garantiza que cada grupo tenga la misma probabilidad de ser clasificado correctamente para cada clase.

**Formula**: Para cada clase `c`, se calcula el TPR por grupo: `P(Y_hat=c | Y=c, A=a)`. Disparidad = `max(TPRs) - min(TPRs)`. Se devuelve la disparidad maxima entre clases.

**Valor ideal**: 0.0 (recall igual para todos los grupos en cada clase).

**Registry key**: `multiclass_equal_opportunity`

**Entradas requeridas**: `target`, `prediction`, `dimension`

---

### 3. `multiclass_confusion_metrics`

**Que mide**: Precision/recall por clase y exactitud por grupo. Devuelve un diccionario (no un escalar), util para diagnosticos detallados en lugar de umbrales de politica.

**Tipo de retorno**: `Dict` con las claves `per_class_metrics` (precision/recall por clase) y `per_group_performance` (exactitud por grupo).

**Registry key**: `multiclass_confusion_metrics`

**Entradas requeridas**: `target`, `prediction`, `dimension`

**Nota**: Esta metrica devuelve un diccionario, no un float. Esta disenada principalmente para reportes de diagnostico y puede no funcionar directamente con controles OSCAL basados en umbrales. Use `calc_multiclass_fairness_report()` en Python para un analisis combinado.

---

### 4. `weighted_demographic_parity_multiclass`

**Que mide**: Paridad demografica con estrategia de agregacion configurable entre clases.

**Estrategias** (configuradas via el parametro `strategy`):

| Estrategia | Descripcion |
| :--- | :--- |
| `macro` (por defecto) | Disparidad maxima entre todas las clases |
| `micro` | Disparidad maxima usando distribuciones de prediccion normalizadas |
| `one-vs-rest` | Igual que macro pero con descomposicion one-vs-rest explicita |
| `weighted` | Disparidades ponderadas por prevalencia de clase |

**Formula (macro)**: Igual que `multiclass_demographic_parity`, pero con control de estrategia.

**Valor ideal**: 0.0

**Registry key**: `weighted_demographic_parity_multiclass`

**Entradas requeridas**: `target` (no utilizado pero validado), `prediction`, `dimension`

**Muestras minimas**: 30

---

### 5. `macro_equal_opportunity_multiclass`

**Que mide**: Igualdad de oportunidad promediada por macro. Calcula la disparidad de TPR para cada clase (one-vs-rest) y luego devuelve el maximo.

**Formula**: Para cada clase `c`, se binariza como `y_true_c = (y == c)`. Se calcula el TPR por grupo. Disparidad = `max(TPRs) - min(TPRs)`. Se devuelve `max(disparities)`.

**Valor ideal**: 0.0

**Registry key**: `macro_equal_opportunity_multiclass`

**Entradas requeridas**: `target`, `prediction`, `dimension`

**Muestras minimas**: 30

---

### 6. `micro_equalized_odds_multiclass`

**Que mide**: Disparidad combinada de TPR + FPR entre grupos. Mide si la exactitud general y la tasa de error del modelo son equitativas entre grupos protegidos.

**Formula**: Para cada grupo, se calcula la exactitud general y la tasa de error. Se devuelve `(max_accuracy - min_accuracy) + (max_error_rate - min_error_rate)`.

**Valor ideal**: 0.0 (sin disparidad de exactitud/error entre grupos).

**Registry key**: `micro_equalized_odds_multiclass`

**Entradas requeridas**: `target`, `prediction`, `dimension`

**Muestras minimas**: 30

---

### 7. `predictive_parity_multiclass`

**Que mide**: Disparidad de precision entre grupos protegidos para cada clase. Garantiza que cuando el modelo predice una clase, sea igualmente preciso para todos los grupos.

**Estrategias**: `macro` (por defecto), `weighted`

**Formula (macro)**: Para cada clase `c`, se calcula la precision por grupo: `P(Y=c | Y_hat=c, A=a)`. Disparidad = `max(precisions) - min(precisions)`. Se devuelve el maximo entre clases.

**Valor ideal**: 0.0

**Registry key**: `predictive_parity_multiclass`

**Entradas requeridas**: `target`, `prediction`, `dimension`

**Nota**: Esta metrica devuelve una tupla `(value, metadata)` donde metadata contiene `total_samples`, `min_class_support` y `min_prediction_support`.

---

## Tabla Resumen

| Registry Key | Que Verifica | Ideal | Estrategias |
| :--- | :--- | :--- | :--- |
| `multiclass_demographic_parity` | Paridad en tasa de prediccion (OVR) | 0.0 | Agregacion `max`, `macro` |
| `multiclass_equal_opportunity` | Paridad de TPR (OVR) | 0.0 | -- |
| `multiclass_confusion_metrics` | Diagnosticos por clase/grupo | Dict | -- |
| `weighted_demographic_parity_multiclass` | Paridad en tasa de prediccion | 0.0 | `macro`, `micro`, `one-vs-rest`, `weighted` |
| `macro_equal_opportunity_multiclass` | Paridad de TPR (macro) | 0.0 | -- |
| `micro_equalized_odds_multiclass` | Paridad de exactitud + error | 0.0 | -- |
| `predictive_parity_multiclass` | Paridad de precision | 0.0 | `macro`, `weighted` |

---

## Reporte Integral

Para una vista combinada, utilice la funcion `calc_multiclass_fairness_report()` en Python:

```python
from venturalitica.metrics import calc_multiclass_fairness_report

report = calc_multiclass_fairness_report(
    y_true=df["target"],
    y_pred=df["prediction"],
    protected_attr=df["gender"]
)

# Returns dict with:
# - weighted_demographic_parity_macro
# - macro_equal_opportunity
# - micro_equalized_odds
# - predictive_parity_macro
```

### Analisis Interseccional

Para equidad interseccional (por ejemplo, genero x edad), pase multiples atributos:

```python
from venturalitica.assurance.fairness.multiclass_reporting import calc_intersectional_metrics

results = calc_intersectional_metrics(
    y_true=df["target"],
    y_pred=df["prediction"],
    protected_attrs={
        "gender": df["gender"],
        "age_group": df["age_group"]
    }
)

# Returns:
# - intersectional_disparity: max - min accuracy across slices
# - worst_slice: e.g., "female x elderly"
# - best_slice: e.g., "male x young"
# - slice_details: accuracy per intersection
```

---

## Restricciones

- **Muestras minimas**: La mayoria de las metricas multiclase requieren >= 30 muestras y lanzan un `ValueError` en caso contrario.
- **Grupos minimos**: Se requieren al menos 2 grupos protegidos.
- **Clases minimas**: Se requieren al menos 2 clases (aunque para problemas de 2 clases, se prefieren las metricas binarias mas simples).
- **Dependencia opcional**: Algunas metricas usan Fairlearn internamente. Instale con `pip install fairlearn` si es necesario.

---

## Relacionado

- **[Referencia de Metricas](metrics.md)** -- Las 35+ metricas incluyendo equidad binaria, privacidad y rendimiento
- **[Redaccion de Politicas](policy-authoring.md)** -- Como usar registry keys en controles OSCAL
- **[Vinculacion de Columnas](column-binding.md)** -- Como `dimension`, `target`, `prediction` se mapean a columnas
