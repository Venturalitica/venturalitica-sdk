# 🛠️ Escribiendo Política Primero en Código (El Ingeniero)

Esta guía se centra en la **Persona del Ingeniero**: quien traduce los requisitos legales en reglas técnicas (OSCAL).
En el **Nivel 1**, aprendiste a "Bloquear" despliegues incorrectos. Ahora escribiremos el archivo de política real que gobierna el proyecto.

---

## Parte 1: La Política de Datos (`data_policy.yaml`)

Para la **Fase 1 (Auditoría de Datos)**, solo nos importa el **Artículo 10 (Gobernanza de Datos)**.
Tu Científico de Datos (El Constructor) no puede comenzar el entrenamiento hasta que este archivo esté listo.

### 1. La Estructura

Crea un archivo llamado `data_policy.yaml` en la raíz de tu proyecto.

```yaml
assessment-plan:
  uuid: credit-scoring-v1
  metadata:
    title: "Artículo 10: Directiva de Crédito al Consumo (CCD)"
    description: "Criterios de aceptación para la calidad y sesgo de los datos de entrenamiento."
  reviewed-controls:
    control-selections:
      - include-controls:
        # LAS REGLAS VAN AQUÍ
```

---

## 2. Definiendo las Reglas (Controles)

Un "Control" es una unidad de lógica. En la Ley de IA de la UE, debes probar que verificaste riesgos específicos.

### Regla A: Representación (Soporte Estadístico)
*   **Requisito Legal**: "Los conjuntos de datos de entrenamiento, validación y prueba deberán ser pertinentes, representativos, libres de errores y completos." (Art 10.3)
*   **Traducción**: Asegurar que ningún grupo demográfico sea borrado (Mínimo 20% de representación).

```yaml
        - control-id: check-imbalance
          description: "Asegurar que los grupos minoritarios sean estadísticamente significativos."
          props:
            - name: metric_key
              value: min_class_ratio
            - name: threshold
              value: "0.20"  # Fallar si la clase minoritaria < 20%
            - name: operator
              value: ">"
```

### Regla B: Sesgo (Impacto Dispar)
*   **Requisito Legal**: "Examen de posibles sesgos." (Art 10.2.f)
*   **Traducción**: Las tasas de aceptación no deben desviarse más del 20% entre grupos (Regla de los Cuatro Quintos).

```yaml
        - control-id: check-gender-bias
          description: "El Ratio de Impacto Dispar debe estar entre 0.8 - 1.25"
          props:
            - name: metric_key
              value: disparate_impact_ratio
            - name: threshold
              value: "0.80"
            - name: operator
              value: ">"
```

---

## 3. Verificar la Política

Antes de entregarla al Científico de Datos, verifica que funcione.

```python
import venturalitica as vl
from venturalitica.quickstart import load_sample

# 1. Cargar el Conjunto de Datos 'Aprobado' (Simulado)
data = load_sample('loan')

# 2. Prueba Seca de la Política
try:
    vl.enforce(
        data=data,
        target="class",
        gender="Attribute9",  # "Estado personal y sexo" en Datos de Crédito Alemán
        policy="data_policy.yaml"
    )
    print("✅ La política tiene sintaxis válida y pasa los datos base.")
except Exception as e:
    print(f"❌ Error de Política: {e}")
```

---

## Parte 2: La Política del Modelo (`model_policy.yaml`)

Una vez aprobados los datos, necesitas definir las reglas para el **producto final** (el modelo entrenado).
Esto corresponde al **Artículo 15 (Precisión, Robustez y Ciberseguridad)**.

Crea un segundo archivo: `model_policy.yaml`.

### Regla C: Rendimiento (Precisión)
*   **Requisito Legal**: "Los sistemas de IA de alto riesgo se diseñarán... para lograr un nivel adecuado de precisión." (Art 15.1)
*   **Traducción**: El modelo debe ser mejor que adivinar al azar (ej. > 70% de precisión).

```yaml
        - control-id: accuracy-check
          description: "El modelo debe lograr al menos 70% de precisión."
          props:
            - name: metric_key
              value: accuracy_score
            - name: threshold
              value: "0.70"
            - name: operator
              value: ">"
```

### Regla D: Equidad Post-Entrenamiento (Resultado)
*   **Requisito Legal**: "Los resultados no deberán estar sesgados..."
*   **Traducción**: Incluso si los datos estaban equilibrados, el modelo podría aprender a discriminar. Verifica las predicciones nuevamente.

```yaml
        - control-id: gender-fairness-model
          description: "Asegurar que las predicciones del modelo no impacten disparmente a las mujeres."
          props:
            - name: metric_key
              value: disparate_impact_ratio
            - name: "input:dimension"
              value: "gender"         # Enlazar explícitamente a la columna de género
            - name: threshold
              value: "0.80"
            - name: operator
              value: ">"
```

---

## ¿Qué Sigue?

Ahora has creado la **especificación**.
👉 Entrega estos archivos (`data_policy.yaml` y `model_policy.yaml`) a tu Científico de Datos. Ellos los usarán en el **Nivel 2** para auditar su flujo de entrenamiento.
