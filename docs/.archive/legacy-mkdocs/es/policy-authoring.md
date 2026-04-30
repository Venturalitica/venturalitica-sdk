# Guia de Redaccion de Politicas

Esta guia explica como escribir archivos de politica OSCAL para Venturalitica. Las politicas definen los controles de equidad, rendimiento, privacidad y calidad de datos que tu sistema de IA debe superar.

---

## El formato canonico: `assessment-plan`

Venturalitica utiliza el formato **OSCAL `assessment-plan`** como formato canonico de politicas. Aunque el cargador del SDK soporta multiples tipos de documentos OSCAL (`catalog`, `system-security-plan`, `component-definition`, `profile`), las nuevas politicas deben escribirse en formato `assessment-plan`.

!!! info "Por que assessment-plan?"
    El formato `assessment-plan` se corresponde directamente con el modelo de aplicacion del SDK: se definen controles con metricas, umbrales y operadores, y luego se evaluan contra los datos. El Dashboard Policy Editor tambien genera exclusivamente el formato `assessment-plan`.

---

## Politica minima

La politica valida mas simple tiene un unico control:

```yaml
assessment-plan:
  metadata:
    title: "My First Policy"
  control-implementations:
    - description: "Fairness Controls"
      implemented-requirements:
        - control-id: bias-check
          description: "Disparate impact must satisfy the Four-Fifths Rule"
          props:
            - name: metric_key
              value: disparate_impact
            - name: threshold
              value: "0.8"
            - name: operator
              value: ">"
            - name: "input:dimension"
              value: gender
```

Para aplicarla:

```python
import venturalitica as vl

results = vl.enforce(
    data=df,
    target="class",
    gender="Attribute9",
    policy="my_policy.oscal.yaml"
)
```

---

## Anatomia de un control

Cada control (un `implemented-requirement`) tiene las siguientes propiedades:

| Propiedad | Obligatoria | Descripcion |
| :--- | :--- | :--- |
| `control-id` | Si | Identificador unico del control |
| `description` | No | Descripcion legible por humanos |
| `props` | Si | Lista de propiedades clave-valor (ver mas abajo) |

### Referencia de Props

| Nombre del Prop | Obligatorio | Descripcion | Ejemplo |
| :--- | :--- | :--- | :--- |
| `metric_key` | Si | Clave de registro de la metrica a calcular | `disparate_impact` |
| `threshold` | Si | Valor numerico del umbral (como cadena de texto) | `"0.8"` |
| `operator` | Si | Operador de comparacion | `">"`, `"<"`, `">="`, `"<="`, `"=="`, `"gt"`, `"lt"` |
| `input:dimension` | Depende | Atributo protegido para metricas de equidad | `gender`, `age` |
| `input:target` | No | Sobreescribir la columna objetivo para este control | `class` |
| `input:prediction` | No | Sobreescribir la columna de prediccion | `y_pred` |

!!! tip
    El prefijo `input:*` mapea valores a los argumentos con nombre de la funcion de metrica. `input:dimension` se convierte en `dimension="gender"` cuando se invoca la metrica.

---

## El patron de dos politicas

El cumplimiento profesional separa las auditorias de datos y de modelo en dos politicas:

### Politica de datos (Articulo 10)

Verifica los datos de entrenamiento **antes** del entrenamiento del modelo:

```yaml
assessment-plan:
  metadata:
    title: "Article 10: Data Assurance"
  control-implementations:
    - description: "Data Quality & Fairness"
      implemented-requirements:
        - control-id: data-imbalance
          description: "Minority class must be > 20%"
          props:
            - name: metric_key
              value: class_imbalance
            - name: threshold
              value: "0.2"
            - name: operator
              value: ">"

        - control-id: data-gender-bias
          description: "Gender disparate impact > 0.8 (Four-Fifths Rule)"
          props:
            - name: metric_key
              value: disparate_impact
            - name: "input:dimension"
              value: gender
            - name: threshold
              value: "0.8"
            - name: operator
              value: ">"

        - control-id: data-age-bias
          description: "Age disparity > 0.5"
          props:
            - name: metric_key
              value: disparate_impact
            - name: "input:dimension"
              value: age
            - name: threshold
              value: "0.5"
            - name: operator
              value: ">"
```

### Politica de modelo (Articulo 15)

Verifica las predicciones del modelo **despues** del entrenamiento:

```yaml
assessment-plan:
  metadata:
    title: "Article 15: Model Assurance"
  control-implementations:
    - description: "Model Performance & Fairness"
      implemented-requirements:
        - control-id: model-accuracy
          description: "Model accuracy >= 80%"
          props:
            - name: metric_key
              value: accuracy_score
            - name: threshold
              value: "0.80"
            - name: operator
              value: ">="

        - control-id: model-fairness
          description: "Demographic parity difference < 0.10"
          props:
            - name: metric_key
              value: demographic_parity_diff
            - name: "input:dimension"
              value: gender
            - name: threshold
              value: "0.10"
            - name: operator
              value: "<"
```

### Aplicar ambas politicas

```python
# Pre-entrenamiento: auditar los datos
vl.enforce(data=train_df, target="class", gender="Attribute9",
           policy="data_policy.oscal.yaml")

# Post-entrenamiento: auditar el modelo
vl.enforce(data=test_df, target="class", prediction="y_pred",
           gender="Attribute9", policy="model_policy.oscal.yaml")
```

O en una sola llamada:

```python
vl.enforce(
    data=df,
    target="class",
    gender="Attribute9",
    policy=["data_policy.oscal.yaml", "model_policy.oscal.yaml"]
)
```

---

## Metricas disponibles

Cualquier metrica registrada en `METRIC_REGISTRY` puede usarse como `metric_key`. Consulta la [Referencia de Metricas](metrics.md) para la lista completa. Las mas comunes:

| Categoria | Clave de metrica | Operador tipico | Umbral tipico |
| :--- | :--- | :--- | :--- |
| **Calidad de datos** | `disparate_impact` | `>` | `0.8` |
| **Calidad de datos** | `class_imbalance` | `>` | `0.2` |
| **Rendimiento** | `accuracy_score` | `>=` | `0.80` |
| **Rendimiento** | `f1_score` | `>=` | `0.75` |
| **Equidad** | `demographic_parity_diff` | `<` | `0.10` |
| **Equidad** | `equalized_odds_ratio` | `<` | `0.20` |
| **Privacidad** | `k_anonymity` | `>=` | `5` |

---

## Mapeo de dimensiones

El prop `input:dimension` indica al SDK que atributo protegido analizar. El valor es un nombre abstracto que se resuelve mediante [Column Binding](column-binding.md):

```yaml
# En tu politica:
- name: "input:dimension"
  value: gender          # Nombre abstracto

# En tu codigo Python:
vl.enforce(data=df, gender="Attribute9")  # Mapea 'gender' -> 'Attribute9'
```

---

## Multiples implementaciones de controles

Puedes agrupar controles de forma logica:

```yaml
assessment-plan:
  metadata:
    title: "Comprehensive AI Assurance Policy"
  control-implementations:
    - description: "Data Quality Controls (Article 10)"
      implemented-requirements:
        - control-id: dq-001
          # ...
        - control-id: dq-002
          # ...

    - description: "Fairness Controls (Article 9)"
      implemented-requirements:
        - control-id: fair-001
          # ...

    - description: "Privacy Controls (GDPR)"
      implemented-requirements:
        - control-id: priv-001
          # ...
```

---

## Edicion visual

El Dashboard Policy Editor ofrece una interfaz visual para crear politicas:

1. Ejecuta `venturalitica ui`
2. Navega a **Phase 2: Risk Policy**
3. Usa el formulario para agregar controles, seleccionar metricas y establecer umbrales
4. El editor genera OSCAL YAML en formato `assessment-plan` y lo guarda en tu proyecto

Consulta la [Guia del Dashboard](dashboard.md) para mas detalles.

---

## Convencion de nombres de archivo

| Archivo | Proposito |
| :--- | :--- |
| `data_policy.oscal.yaml` | Controles de auditoria de datos previos al entrenamiento |
| `model_policy.oscal.yaml` | Controles de auditoria del modelo posteriores al entrenamiento |
| `risks.oscal.yaml` | Politica combinada de inicio rapido (usada por `vl.quickstart()`) |

La extension `.oscal.yaml` es una convencion, no un requisito. El SDK carga cualquier archivo `.yaml`.

---

## Formatos OSCAL soportados

Aunque `assessment-plan` es el formato canonico, el cargador tambien acepta:

| Formato | Nivel de soporte | Notas |
| :--- | :--- | :--- |
| `assessment-plan` | Primario | Formato canonico, generado por el Dashboard |
| `catalog` | Soportado | Utilizado en algunas muestras avanzadas |
| `system-security-plan` | Soportado | Utilizado por el comando `pull` del SaaS |
| `component-definition` | Soportado | Formato estandar de componentes OSCAL |
| `profile` | Soportado | Formato de perfil OSCAL |
| Lista YAML plana | Alternativa | Formato de emergencia para listas simples |

!!! warning "Inconsistencia en el formato SSP"
    El comando `pull` del CLI actualmente descarga politicas en formato `system-security-plan`. Estas se cargan correctamente, pero difieren del formato `assessment-plan` generado por el Dashboard. Una version futura unificara ambos formatos.
