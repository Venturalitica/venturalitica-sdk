# Referencia de Metricas

Venturalitica incluye mas de 35 metricas organizadas en 7 categorias. Cada metrica esta registrada en `METRIC_REGISTRY` y puede ser referenciada por su clave en archivos de politica OSCAL.

---

## Categorias de Metricas de un Vistazo

| Categoria | Metricas | Descripcion |
| :--- | :--- | :--- |
| **Rendimiento** | 4 | Accuracy, precision, recall y F1 estandar de ML |
| **Equidad (Tradicional)** | 2 | Paridad demografica, igualdad de oportunidad |
| **Equidad (Alternativa)** | 2 | Probabilidades igualadas, paridad predictiva |
| **Equidad Multiclase** | 7 | Metricas de equidad para clasificacion multiclase |
| **Calidad de Datos** | 4 | Impacto dispar, desequilibrio de clases, completitud |
| **Privacidad** | 4 | k-anonymity, l-diversity, t-closeness, minimizacion de datos |
| **Equidad Causal** | 4 | Contrafactual, descomposicion de caminos, awareness |

---

## Metricas de Rendimiento

| Clave de Registro | Funcion | Descripcion |
| :--- | :--- | :--- |
| `accuracy_score` | `calc_accuracy` | Precision general de clasificacion |
| `precision_score` | `calc_precision` | Valor predictivo positivo |
| `recall_score` | `calc_recall` | Sensibilidad / tasa de verdaderos positivos |
| `f1_score` | `calc_f1` | Media armonica de precision y recall |

**Uso en politica:**

```yaml
- control-id: model-accuracy
  props:
    - name: metric_key
      value: accuracy_score
    - name: threshold
      value: "0.80"
    - name: operator
      value: ">="
```

---

## Metricas de Equidad (Tradicional)

Estas son las medidas de equidad mas utilizadas para clasificacion binaria.

### `demographic_parity_diff`

Mide la diferencia en tasas de prediccion positiva entre grupos protegidos.

- **Formula:** |P(Y=1|A=a) - P(Y=1|A=b)|
- **Valor ideal:** 0.0
- **Umbral tipico:** < 0.10
- **Requiere:** `dimension` (columna del atributo protegido)

### `equal_opportunity_diff`

Mide la diferencia en tasas de verdaderos positivos (TPR) entre grupos.

- **Formula:** |TPR_a - TPR_b|
- **Valor ideal:** 0.0
- **Umbral tipico:** < 0.10
- **Requiere:** `dimension`, `target`, `prediction`

---

## Metricas de Equidad (Alternativa)

### `equalized_odds_ratio`

Asegura que tanto TPR como FPR sean iguales entre grupos. Mas estricta que la igualdad de oportunidad.

- **Formula:** |TPR_a - TPR_b| + |FPR_a - FPR_b|
- **Valor ideal:** 0.0
- **Umbral tipico:** < 0.20
- **Requiere:** `dimension`, `target`, `prediction`
- **Referencia:** [Hardt et al. 2016](https://arxiv.org/abs/1610.02413)

### `predictive_parity`

Mide la igualdad de precision entre grupos. Cuando se emite una prediccion positiva, debe ser igualmente fiable independientemente de la pertenencia al grupo.

- **Formula:** |Precision_a - Precision_b|
- **Valor ideal:** 0.0
- **Umbral tipico:** < 0.10
- **Requiere:** `dimension`, `target`, `prediction`
- **Referencia:** [Corbett-Davies et al. 2017](https://arxiv.org/abs/1708.09055)

---

## Metricas de Equidad Multiclase

Para tareas de clasificacion multiclase. Consulta [Equidad Multiclase](multiclass-fairness.md) para uso detallado.

| Clave de Registro | Descripcion |
| :--- | :--- |
| `multiclass_demographic_parity` | Paridad demografica extendida a multiclase |
| `multiclass_equal_opportunity` | Igualdad de oportunidad por clase |
| `multiclass_confusion_metrics` | Analisis de matriz de confusion por grupo |
| `weighted_demographic_parity_multiclass` | Paridad demografica ponderada por clase |
| `macro_equal_opportunity_multiclass` | Igualdad de oportunidad promediada macro |
| `micro_equalized_odds_multiclass` | Probabilidades igualadas promediadas micro |
| `predictive_parity_multiclass` | Paridad predictiva por clase |

---

## Metricas de Calidad de Datos

| Clave de Registro | Descripcion | Umbral Tipico |
| :--- | :--- | :--- |
| `disparate_impact` | Ratio de la Regla de los Cuatro Quintos entre grupos | > 0.80 |
| `class_imbalance` | Proporcion de la clase minoritaria | > 0.20 |
| `group_min_positive_rate` | Tasa positiva minima entre grupos | > 0.10 |
| `data_completeness` | Proporcion de valores no nulos | > 0.95 |

**Ejemplo de uso (escenario de prestamos):**

```yaml
- control-id: credit-data-bias
  description: "Disparate impact ratio must satisfy the Four-Fifths Rule"
  props:
    - name: metric_key
      value: disparate_impact
    - name: "input:dimension"
      value: gender
    - name: operator
      value: ">"
    - name: threshold
      value: "0.8"
```

---

## Metricas de Privacidad

Medidas de privacidad alineadas con el RGPD desde `venturalitica.assurance.privacy`.

### `k_anonymity`

Tamano minimo de grupo cuando se conocen los cuasi-identificadores. Previene la re-identificacion.

- **Formula:** min(|group|) donde los grupos se definen por cuasi-identificadores
- **Valor ideal:** >= 5 (recomendacion RGPD)
- **Requiere:** columnas de cuasi-identificadores

```python
from venturalitica.metrics.privacy import calc_k_anonymity

k = calc_k_anonymity(df, quasi_identifiers=["age", "gender", "zipcode"])
assert k >= 5, "GDPR recommends k >= 5"
```

### `l_diversity`

Minimo de valores distintos de un atributo sensible por grupo de cuasi-identificadores.

- **Formula:** min(valores distintos en sensitive_attribute por grupo QI)
- **Valor ideal:** >= 2

### `t_closeness`

Diferencia maxima de distribucion entre grupos usando la Distancia del Transporte de Tierra (Earth Mover Distance).

- **Formula:** max(EMD entre distribuciones de grupo)
- **Valor ideal:** < 0.15
- **Referencia:** [Li et al. 2007](https://en.wikipedia.org/wiki/T-closeness)

### `data_minimization`

Cumplimiento del Articulo 5 del RGPD -- proporcion de columnas no sensibles.

- **Formula:** (total_columns - sensitive_columns) / total_columns
- **Valor ideal:** >= 0.70

```python
from venturalitica.metrics.privacy import calc_data_minimization_score

score = calc_data_minimization_score(
    df,
    sensitive_columns=["age", "income", "health_status"]
)
```

---

## Metricas de Equidad Causal

Metricas avanzadas desde `venturalitica.assurance.causal`.

| Clave de Registro | Descripcion |
| :--- | :--- |
| `path_decomposition` | Descompone caminos causales para identificar discriminacion directa vs indirecta |
| `counterfactual_fairness` | Prueba si cambiar un atributo protegido cambiaria el resultado |
| `fairness_through_awareness` | Asegura que individuos similares reciban predicciones similares |
| `causal_fairness_diagnostic` | Diagnostico integral combinando multiples pruebas causales |

---

## Alias para LLM y Benchmarks

Estos son alias de conveniencia que usan `calc_mean` internamente:

| Clave de Registro | Caso de Uso |
| :--- | :--- |
| `bias_score` | Puntuacion general de sesgo para salidas de LLM |
| `stereotype_preference_rate` | Deteccion de estereotipos en texto generado |
| `category_bias_score` | Sesgo por categoria en evaluaciones de benchmarks |

---

## Metricas ESG / QA Financiero

Metricas especializadas para analisis de reportes ESG:

| Clave de Registro | Descripcion |
| :--- | :--- |
| `classification_distribution` | Distribucion de clasificaciones ESG |
| `report_coverage` | Cobertura de requisitos de reporte |
| `provenance_completeness` | Completitud de la cadena de procedencia de datos |
| `chunk_diversity` | Diversidad de fragmentos de texto en Pipeline RAG |
| `subtitle_diversity` | Diversidad de encabezados de seccion en reportes |

---

## Jerarquia de Metricas de Equidad

Diferentes metricas capturan distintos conceptos de equidad, ordenados por nivel de exigencia:

```
Demographic Parity (menos estricta)
    |  Mismas tasas de aprobacion entre grupos
    v
Equal Opportunity (media)
    |  Mismo TPR entre grupos
    v
Equalized Odds (mas estricta)
    |  Mismo TPR Y FPR entre grupos
    v
Predictive Parity (ortogonal)
       Misma precision entre grupos
```

En la practica, un sistema puede aprobar la paridad demografica y al mismo tiempo fallar en probabilidades igualadas. Elige las metricas alineadas con tu contexto de riesgo:

- **Credito / Contratacion:** Equalized odds + predictive parity
- **Salud:** Equalized odds + metricas de privacidad (k-anonymity >= 5)
- **Auditoria integral:** Todas las metricas en conjunto

---

## Uso de Metricas en Politicas OSCAL

Cada metrica puede ser referenciada en una politica OSCAL a traves de la propiedad `metric_key`:

```yaml
assessment-plan:
  metadata:
    title: "Custom Fairness Policy"
  control-implementations:
    - description: "Fairness Controls"
      implemented-requirements:
        - control-id: my-check
          props:
            - name: metric_key
              value: equalized_odds_ratio    # <-- Registry key
            - name: threshold
              value: "0.20"
            - name: operator
              value: "<"
            - name: "input:dimension"
              value: gender                  # <-- Protected attribute
```

Consulta la [Guia de Autoria de Politicas](policy-authoring.md) para la referencia completa del formato OSCAL.

---

## Agregar Metricas Personalizadas

Para registrar una nueva metrica:

1. Crea la funcion en el modulo correspondiente bajo `venturalitica/assurance/`:

    ```python
    def calc_my_metric(df, **kwargs) -> float:
        # Validate inputs
        if "dimension" not in kwargs:
            raise ValueError("Missing 'dimension' parameter")
        # Calculate and return
        return value
    ```

2. Registrala en `venturalitica/metrics/__init__.py`:

    ```python
    METRIC_REGISTRY["my_metric"] = calc_my_metric
    ```

3. Usala en tu politica OSCAL a traves de `metric_key: my_metric`.

---

## Referencias

- [Fairlearn](https://fairlearn.org/) -- Biblioteca de equidad de Microsoft
- [AI Fairness 360](https://aif360.readthedocs.io/) -- Metricas de equidad de IBM
- [Articulo 5 del RGPD](https://gdpr-info.eu/art-5-gdpr/) -- Principio de minimizacion de datos
- [OSCAL](https://pages.nist.gov/OSCAL/) -- Open Security Controls Assessment Language
