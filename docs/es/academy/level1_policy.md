# Nivel 1: El Ingeniero (Politica y Configuracion)

**Objetivo**: Aprender a implementar **Controles** que mitiguen **Riesgos**.

**Prerrequisito**: [De Cero a Pro (Indice)](index.md)

---

## 1. El Escenario: Del Riesgo al Control

En un Sistema de Gestion formal (**ISO 42001**), la Assurance sigue un flujo top-down:

1.  **Evaluacion de Riesgo**: El Oficial de Cumplimiento (CO) identifica un riesgo de negocio (ej. *"Nuestra IA de prestamos podria discriminar a solicitantes de edad avanzada, causando dano legal y reputacional"*).
2.  **Definicion del Control**: Para mitigar este riesgo, el CO establece un **Control** (ej. *"El Ratio de Disparidad por Edad debe ser siempre > 0.5"*).
3.  **Implementacion Tecnica**: Ese es tu trabajo. Tomas el requisito del CO y lo conviertes en la "Ley" tecnica (**Articulo 10: Assurance de Datos**).

En el inicio rapido [De Cero a Pro](index.md), `vl.quickstart('loan')` FALLO:

```text
credit-age-disparate   Age disparity          0.361      > 0.5      FAIL
```

### Que paso?

El **Control** detecto exitosamente una **Brecha de Cumplimiento**. La "Realidad" de los datos (`0.361`) violo el requisito establecido para mitigar el riesgo de "Sesgo de Edad".

> **Regla #1: El Handshake de Responsabilidad**.
> El Oficial de Cumplimiento identifica **Riesgos** y establece **Controles**.
> El Ingeniero implementa y **Verifica** esos controles usando Evidencia.

Si bajas el umbral a 0.3 solo para que el test "pase", no estas arreglando el codigo -- estas **evadiendo un control de seguridad** y exponiendo a la empresa al riesgo original.

## 2. Anatomia de un Control (OSCAL)

Tu trabajo es traducir el requisito del CO a Codigo.
Crea un archivo llamado `data_policy.oscal.yaml` (o [descargalo desde GitHub](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/data_policy.oscal.yaml)).

El formato canonico es `assessment-plan`. Aqui tienes la politica completa con **3 controles** -- copia y pega esto en tu proyecto:

```yaml
assessment-plan:
  metadata:
    title: Credit Risk Assessment Policy (German Credit)
    version: "1.1"
  control-implementations:
    - description: Credit Scoring Fairness Controls
      implemented-requirements:

        # Control 1: Class Imbalance
        # "Rejected loans must be >= 20% of the dataset"
        - control-id: credit-data-imbalance
          description: >
            Data Quality: Minority class (rejected loans) should represent
            at least 20% of the dataset to avoid biased training.
          props:
            - name: metric_key
              value: class_imbalance
            - name: threshold
              value: "0.2"
            - name: operator
              value: gt
            - name: "input:target"
              value: target

        # Control 2: Gender Fairness (Four-Fifths Rule)
        # "Loan approvals must not favor one gender > 80%"
        - control-id: credit-data-bias
          description: >
            Pre-training Fairness: Disparate impact ratio should follow
            the standard '80% Rule' (Four-Fifths Rule).
          props:
            - name: metric_key
              value: disparate_impact
            - name: threshold
              value: "0.8"
            - name: operator
              value: gt
            - name: "input:target"
              value: target
            - name: "input:dimension"
              value: gender

        # Control 3: Age Fairness
        # "Loan approvals must not discriminate by age > 50%"
        - control-id: credit-age-disparate
          description: "Disparate impact ratio for raw age"
          props:
            - name: metric_key
              value: disparate_impact
            - name: threshold
              value: "0.50"
            - name: operator
              value: gt
            - name: "input:target"
              value: target
            - name: "input:dimension"
              value: age
```

### Que hace cada propiedad

| Propiedad | Proposito | Ejemplo |
| :--- | :--- | :--- |
| `metric_key` | Que metrica calcular (ver [Referencia de Metricas](../metrics.md)) | `disparate_impact`, `class_imbalance`, `accuracy_score` |
| `threshold` | El limite numerico | `"0.8"` |
| `operator` | Operador de comparacion: `gt`, `gte`, `lt`, `lte`, `eq` | `gt` = mayor que |
| `input:target` | Columna que contiene las etiquetas de verdad | `target` (resuelto via column binding) |
| `input:dimension` | Atributo protegido por el cual segmentar | `gender`, `age` (resuelto via [Column Binding](../column-binding.md)) |
| `input:prediction` | Columna que contiene las predicciones del modelo (auditorias de modelo) | `prediction` |

## 3. Ejecuta Tu Politica Personalizada

Ahora, ejecutemos la auditoria con *tu* archivo de politica. Copia y pega este bloque de codigo:

```python
import venturalitica as vl
from venturalitica.quickstart import load_sample

# 1. Cargar el Dataset German Credit (ejemplo integrado)
data = load_sample("loan")
print(f"Dataset: {data.shape[0]} rows, {data.shape[1]} columns")

# 2. Ejecutar Auditoria contra tu politica
results = vl.enforce(
    data=data,
    target="class",            # Ground truth column
    gender="Attribute9",       # "Personal status and sex" -> gender
    age="Attribute13",         # "Age in years" -> age
    policy="data_policy.oscal.yaml"
)

# 3. Imprimir resultados
for r in results:
    status = "PASS" if r.passed else "FAIL"
    print(f"  {r.control_id:<25} {r.actual_value:.3f}  {r.operator} {r.threshold}  {status}")
```

### Salida esperada

```text
Dataset: 1000 rows, 21 columns
  credit-data-imbalance     0.300  gt 0.2   PASS
  credit-data-bias          0.895  gt 0.8   PASS
  credit-age-disparate      0.361  gt 0.5   FAIL
```

Dos controles pasan, uno falla. El ratio de disparidad por edad (0.361) esta por debajo del umbral de 0.5.

### El Handshake de "Traduccion"

Observa lo que acaba de pasar:

-   **Legal**: "Se justo (> 0.5)." -- Definido en tu politica YAML por el Oficial de Cumplimiento.
-   **Dev**: "La columna `Attribute13` significa `age`." -- Definido en tu llamada Python por el Ingeniero.

Este mapeo es el **Handshake**. Tu construyes el puente entre DataFrames desordenados y requisitos legales rigidos. Asi es como implementas **ISO 42001** sin perder la cabeza en hojas de calculo.

```text
OSCAL Policy              Python Code                DataFrame
+-----------+       +------------------+       +---------------+
| age       | ----> | age="Attribute13"| ----> | Attribute13   |
| gender    | ----> | gender="Attr..9" | ----> | Attribute9    |
| target    | ----> | target="class"   | ----> | class         |
+-----------+       +------------------+       +---------------+
```

Consulta [Column Binding](../column-binding.md) para ver el algoritmo completo de resolucion.

## 4. Verificacion Visual

La salida del terminal es evidencia, pero el cumplimiento requiere reportes profesionales.
Lanza el Dashboard local para visualizar los resultados:

```bash
pip install venturalitica[dashboard]   # Requerido para la interfaz
venturalitica ui
```

Navega a la pestana de **Fase 3 (Verificar y Evaluar)**. Veras:

- Marcas verdes para los dos controles que pasan
- Una bandera roja para `credit-age-disparate` con el valor medido (0.361) vs. el umbral (0.5)
- El archivo JSON de traza se guarda automaticamente como evidencia local

Has prevenido exitosamente que una IA no conforme llegue a produccion midiendo el riesgo contra un estandar verificable.

## 5. Mensajes para Llevar a Casa

1.  **Politica como Codigo**: La Assurance es un archivo `.yaml`. Define los **Controles** que tu sistema debe pasar.
2.  **El Handshake**: Tu defines el *Mapeo* (`age`=`Attribute13`). El Oficial define el *Requisito* (`> 0.5`). Ninguno puede actuar solo.
3.  **El Tratamiento empieza con la Deteccion**: La falla local es la senal necesaria para iniciar un plan de tratamiento de riesgos formal ISO 42001. No bajes el umbral -- arregla los datos.

---

**Siguiente Paso**: La auditoria fallo localmente. Como la integramos en un Pipeline de ML?

**[Ir al Nivel 2: El Integrador (MLOps)](level2_integrator.md)**
