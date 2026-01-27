# 🛠️ Integración de Entrenamiento de Modelos (Venturalítica)

Integra verificaciones de equidad y rendimiento en tu flujo de trabajo de ML con Venturalítica.

---

## Descripción General

!!! info "Versión Interactiva"
    Puedes ejecutar este tutorial en un Jupyter Notebook: [01-training-tutorial.ipynb](https://github.com/venturalitica/venturalitica-sdk/blob/main/notebooks/01-training-tutorial.ipynb)

| Fase | Verificación | Función |
|:--|:--|:--|
| Pre-entrenamiento | Sesgo de datos | `enforce(data=train_df)` |
| Post-entrenamiento | Equidad del modelo + Rendimiento | `enforce(data=test_df, prediction=pred)` |

---

## Paso 1: Cargar y Preparar Datos

Dado que el conjunto de datos de Crédito Alemán contiene cadenas categóricas, debemos codificarlas antes del entrenamiento.

```python
from ucimlrepo import fetch_ucirepo
from sklearn.model_selection import train_test_split
import pandas as pd

# Obtener Crédito Alemán UCI
dataset = fetch_ucirepo(id=144)
df = dataset.data.features.copy()
df['class'] = dataset.data.targets

# Dividir datos sin procesar para la auditoría
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# Codificar datos para entrenamiento con Scikit-Learn
df_encoded = pd.get_dummies(df.drop(columns=['class']))
X_train, X_test, y_train, y_test = train_test_split(
    df_encoded, 
    df['class'].values.ravel(), 
    test_size=0.2, 
    random_state=42
)
```

---

## Paso 2: Auditoría Pre-Entrenamiento (Sesgo de Datos)

Verifica tus datos de entrenamiento en busca de sesgos **antes** de comenzar la fase de entrenamiento intensiva en cómputo.

!!! tip "¿Por qué necesitamos `tracecollector`?"
    El cumplimiento requiere pruebas. Usa `vl.tracecollector` para registrar la "Historia del Código" (BOM, Encabezados) junto con los resultados de la auditoría. Esto es requerido para la generación del Anexo IV.

```python
import venturalitica as vl

# Iniciar el 'registrador de evidencia'
with vl.tracecollector("training_audit"):
    
    # Ejecutar la Auditoría de Datos
    vl.enforce(
        data=train_df,
        target="class",
        gender="Attribute9",  # Columna de Género/Estado
        age="Attribute13",    # Columna de Edad
        policy="loan-policy.yaml"
    )
```

**Salida Real:**
```text
[Venturalítica {{ version }}] 🚀 TraceCollector [training_audit] comenzando...
[Venturalítica {{ version }}] 🛡  Aplicando política: loan-policy.yaml

  CONTROL                DESCRIPCION                            ACTUAL     LIMITE     RESULTADO
  ────────────────────────────────────────────────────────────────────────────────────────────────
  imbalance              Proporción minoritaria                 0.431      > 0.2      ✅ PASS
  gender-bias            Impacto dispar                         0.836      > 0.8      ✅ PASS
  age-bias               Disparidad por edad                    0.361      > 0.5      ❌ FAIL
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Resumen de Auditoría: ❌ VIOLACIÓN | 2/3 controles pasados
  
  ✅ TraceCollector [training_audit] evidencia guardada en .venturalitica/trace_training_audit.json
```

---

## Paso 3: Entrenar y Evaluar

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Obtener predicciones en el conjunto de prueba
predictions = model.predict(X_test)
```

---

## Paso 4: Auditoría Post-Entrenamiento (Equidad + Rendimiento)

Audita el comportamiento del modelo en datos no vistos. Reutilizamos el mismo recolector de trazas (o iniciamos uno nuevo) para capturar esta fase.

```python
# Crear dataframe de auditoría (características sin procesar + predicciones)
test_audit_df = df.iloc[test_df.index].copy()
test_audit_df['prediction'] = predictions

with vl.tracecollector("model_eval"):
    vl.enforce(
        data=test_audit_df,
        target="class",
        prediction="prediction",
        gender="Attribute9",
        age="Attribute13",
        policy="loan-policy.yaml"
    )
```

**Salida Real:**
```text
[Venturalítica {{ version }}] 🛡  Aplicando política: loan-policy.yaml

  CONTROL                DESCRIPCION                            ACTUAL     LIMITE     RESULTADO
  ────────────────────────────────────────────────────────────────────────────────────────────────
  imbalance              Proporción minoritaria                 0.418      > 0.2      ✅ PASS
  gender-bias            Impacto dispar                         0.905      > 0.8      ✅ PASS
  age-bias               Disparidad por edad                    0.600      > 0.5      ✅ PASS
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Resumen de Auditoría: ✅ POLÍTICA CUMPLIDA | 3/3 controles pasados
```

!!! warning
    Aunque los datos de entrenamiento fallaron la verificación de Edad (**0.361**), las predicciones del modelo en el conjunto de prueba (**0.600**) lograron pasar el límite de la política (>0.5). Sin embargo, esta mejora debe ser monitoreada de cerca para asegurar que se generalice más allá de este segmento de prueba específico.

!!! info "**¿Por qué 0.361 vs 1.000?**"
    Si ves un `1.000` perfecto pero esperas sesgo, verifica tu vinculación de columnas. Si falta una columna o no coincide, Venturalítica puede predeterminar a 1.0. Siempre verifica los nombres de tus columnas (como `Attribute9` vs `gender`) en la llamada `enforce()`. {{ version }} también incluye un filtro de soporte mínimo (N>=5) para asegurar significancia estadística, lo que contribuye a la lectura precisa de **0.361**.

---

## Paso 5: Incluyendo Métricas de Rendimiento

Tiene perfecto sentido auditar el rendimiento junto con la equidad. Si "arreglas" el sesgo pero destruyes la utilidad del modelo (por ejemplo, 20% de precisión), el sistema sigue fallando.

Puedes definir umbrales de rendimiento en la misma política:

```yaml
- control-id: accuracy-threshold
  description: "El modelo debe lograr al menos 75% de precisión"
  props:
    - name: metric_key
      value: accuracy
    - name: threshold
      value: "0.75"
    - name: operator
      value: gt
```

Venturalítica soporta: `accuracy`, `precision`, `recall`, y `f1`.

**Ejemplo de Salida con Rendimiento:**
```text
[Venturalítica {{ version }}] 🛡  Aplicando política: tutorial_policy.yaml

  CONTROL                DESCRIPCION                            ACTUAL     LIMITE     RESULTADO
  ────────────────────────────────────────────────────────────────────────────────────────────────
  gender-disparate       Equidad de género (DI > 0.8)           0.905      > 0.8      ✅ PASS
  age-disparate          Equidad de edad (DI > 0.5)             0.600      > 0.5      ✅ PASS
  accuracy-check         Precisión > 70%                        0.795      > 0.7      ✅ PASS
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Resumen de Auditoría: ✅ POLÍTICA CUMPLIDA | 3/3 controles pasados
```

---

## Paso 6: Gobernanza Automática con `vl.wrap` (Experimental)

!!! warning "**Característica Experimental**"
    `vl.wrap` está actualmente en vista previa. Su API y comportamiento pueden cambiar en versiones futuras. Úsalo con precaución.

Si estás usando **Scikit-Learn**, puedes automatizar todo el proceso de auditoría envolviendo tu modelo. Esto asegura que cada llamada `.fit()` y `.predict()` sea auditada contra tu política.

```python
# Envolver tu modelo
base_model = RandomForestClassifier(n_estimators=100, random_state=42)
governed_model = vl.wrap(base_model, policy="loan-policy.yaml") # Gobernanza Venturalítica

# ¡Las auditorías son automatizadas! 
# Solo proporciona los datos sin procesar para el mapeo de atribución (ej. género, edad)
governed_model.fit(
    X_train, y_train, 
    audit_data=train_df, 
    gender="Attribute9", 
    age="Attribute13"
)

# Predecir también activa la auditoría de equidad + rendimiento
predictions = governed_model.predict(
    X_test, 
    audit_data=test_df, 
    gender="Attribute9", 
    age="Attribute13"
)
```

Este patrón reduce el código repetitivo y garantiza que ningún modelo vaya a producción sin un rastro de auditoría verificado.

---

## Paso 7: Ver Evidencia en el Panel de Control
Ahora que has ejecutado el entrenamiento y evaluación con `tracecollector`, has generado los artefactos requeridos para la **Ley de IA de la UE**.

Inspecciónalos en el Panel de Caja de Cristal:

```bash
venturalitica ui
```

Esto lanzará el servidor local donde puedes ver:

*   **Artículo 9**: Tus resultados de Auditoría de Equidad y Rendimiento.
*   **Artículo 13**: La BOM de tu entorno de entrenamiento.
*   **Generación**: El borrador de tu documentación técnica.
