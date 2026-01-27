# Tutorial: Escribiendo Tu Primera Política (OSCAL)

Venturalítica utiliza **OSCAL (Open Security Controls Assessment Language)** para definir reglas de gobernanza. Este enfoque de "Política-como-Código" te permite controlar las versiones de tus requisitos de cumplimiento junto con tu software.

## 1. La Estructura de una Política

Un archivo de política (`.yaml`) le dice al SDK **qué** medir (métricas) y **por qué** (descripciones de control).

```yaml
assessment-plan:
  uuid: policy-v1
  metadata:
    title: "Ley de IA de la UE - Auditoría de Alto Riesgo"
  reviewed-controls:
    control-selections:
      - include-controls:
        # BLOQUE DE CONTROL 1
        - control-id: gender-fairness
          description: "Artículo 10: Gobernanza de Datos. Examen de posibles sesgos."
          props:
            - name: metric_key
              value: demographic_parity_diff
            - name: threshold
              value: "0.10"
            - name: operator
              value: "<"
```

## 2. Definiendo Controles

Cada `control-id` representa una verificación específica.

### A. Verificación de Sesgo (Equidad)
Asegura que tu modelo trate a los grupos por igual.

```yaml
- control-id: check-gender-bias
  props:
    - name: metric_key
      value: demographic_parity_diff
    - name: threshold
      value: "0.10"  # Fallar si la diferencia > 10%
    - name: operator
      value: "<"
```

### B. Calidad de Datos
Verifica el desequilibrio de clases o valores faltantes.

```yaml
- control-id: check-imbalance
  props:
    - name: metric_key
      value: min_class_ratio
    - name: threshold
      value: "0.20"  # Fallar si la clase minoritaria < 20%
    - name: operator
      value: ">"
```

## 3. Métricas Soportadas

Todas las métricas de `venturalitica.metrics` son soportadas. Claves comunes:

| Clave | Descripción |
| :--- | :--- |
| `demographic_parity_diff` | Diferencia en tasas de aceptación (Equidad). |
| `disparate_impact_ratio` | Proporción de tasas de aceptación (Equidad). |
| `accuracy_score` | Precisión general del modelo (Rendimiento). |
| `f1_score` | Media armónica de precisión/recuerdo (Rendimiento). |
| `missing_values_ratio` | Porcentaje de celdas vacías (Calidad). |

## 4. Cómo Ejecutarlo

Una vez que tengas tu `policy.yaml`, aplícalo a tu dataframe:

```python
import venturalitica as vl
import pandas as pd

df = pd.read_csv("data/loan_applications.csv")

vl.enforce(
    data=df,
    target="approved",       # La columna a predecir
    gender="applicant_sex",  # El atributo protegido
    policy="policy.yaml"     # Tu archivo OSCAL
)
```

El SDK evaluará cada control en el YAML contra tus datos. Si algún control falla (y `blocking: true`), genera una excepción `AuditFailure`, deteniendo la canalización.
