# 🛠️ Entrenamiento del Modelo (El Constructor)

Esta guía se centra en la **Persona del Constructor**: el Científico de Datos que entrena el modelo.
En el flujo de trabajo de **Venturalítica**, tu trabajo es "fabricar" el sistema de IA de acuerdo con las especificaciones definidas por el **Ingeniero** (Nivel 1).

---

## El Apretón de Manos de Dos Políticas

El cumplimiento no es un solo paso. Es un apretón de manos entre **Datos** (Artículo 10) y **Modelo** (Artículo 15).

| Fase | Política | Artículo (Ley de IA de la UE) | Función |
|:--|:--|:--|:--|
| **1. Auditoría de Datos** | `data_policy.yaml` | **Art. 10**: Assurance de Datos | `vl.enforce(data=train_df)` |
| **2. Auditoría del Modelo** | `model_policy.yaml` | **Art. 15**: Precisión y Robustez | `vl.enforce(data=test_df, prediction=pred)` |

---

## Paso 1: Cargar y Dividir Datos

Usamos el conjunto de datos estándar de **Evaluación de Crédito** (Loan Credit Scoring).

```python
from ucimlrepo import fetch_ucirepo
from sklearn.model_selection import train_test_split
import pandas as pd

# 1. Obtener Datos
dataset = fetch_ucirepo(id=144)
df = dataset.data.features.copy()
df['class'] = dataset.data.targets

# 2. Dividir (Entrenamiento/Prueba)
train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)

# 3. Codificar para Entrenamiento (One-Hot)
df_encoded = pd.get_dummies(df.drop(columns=['class']))
X_train, X_test, y_train, y_test = train_test_split(
    df_encoded, 
    df['class'].values.ravel(), 
    test_size=0.2, 
    random_state=42
)
```

---

## Paso 2: Auditoría Pre-Entrenamiento (Artículo 10)

Antes de invertir tiempo de cómputo, verifica la materia prima.

```python
import venturalitica as vl

# Iniciar el 'registrador de evidencia' para la Fase de Entrenamiento
with vl.monitor("training_run_v1"):
    
    # 🔍 AUDITORÍA 1: GOBERNANZA DE DATOS (Los Ingredientes)
    print("🛡️ Auditando Datos (Artículo 10)...")
    vl.enforce(
        data=train_df,
        target="class",
        gender="Attribute9",  # Mapeo estrictamente definido por la política
        age="Attribute13",
        policy="data_policy.yaml"
    )
```

**Salida Real:**
```text
[Venturalítica {{ version }}] 🛡  Aplicando política: data_policy.yaml

  CONTROL                DESCRIPCION                            ACTUAL     LIMITE     RESULTADO
  ────────────────────────────────────────────────────────────────────────────────────────────────
  imbalance              Proporción minoritaria                 0.431      > 0.2      ✅ PASS
  gender-bias            Impacto dispar                         0.836      > 0.8      ✅ PASS
  ────────────────────────────────────────────────────────────────────────────────────────────────
```

---

## Paso 3: Entrenar el Modelo

Si los datos pasan, procede a fabricar el modelo.

```python
    # 🏭 FABRICAR: Entrenar el Modelo
    from sklearn.ensemble import RandomForestClassifier
    
    print("🤖 Entrenando Modelo...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Generar predicciones para la siguiente auditoría
    predictions = model.predict(X_test)
```

---

## Paso 4: Auditoría Post-Entrenamiento (Artículo 15)

Ahora verifica el producto terminado contra los requisitos de rendimiento.

```python
    # 🔍 AUDITORÍA 2: PRECISIÓN Y EQUIDAD DEL MODELO (El Producto)
    print("🛡️ Auditando Modelo (Artículo 15)...")
    
    # Preparar dataframe de auditoría
    audit_df = df.iloc[test_df.index].copy()
    audit_df['prediction'] = predictions
    
    vl.enforce(
        data=audit_df,
        target="class",
        prediction="prediction", # Ahora evaluamos la SALIDA usando los mismos atributos sensibles
        gender="Attribute9",
        age="Attribute13",
        policy="model_policy.yaml"
    )
```

**Salida Real:**
```text
[Venturalítica {{ version }}] 🛡  Aplicando política: model_policy.yaml

  CONTROL                DESCRIPCION                            ACTUAL     LIMITE     RESULTADO
  ────────────────────────────────────────────────────────────────────────────────────────────────
  accuracy-check         Precisión Mínima                       0.760      > 0.7      ✅ PASS
  recall-check           Recall (Aversión al Riesgo)            0.720      > 0.6      ✅ PASS
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Resumen de Auditoría: ✅ POLÍTICA CUMPLIDA | 2/2 controles pasados
  
  ✅ TraceCollector [training_run_v1] evidencia guardada en .venturalitica/trace_training_run_v1.json
```

---

## Paso 5: Ver Evidencia

Ahora has completado el **Trabajo del Constructor**.
Ejecuta el panel de control para ver tu "Caja de Cristal".

```bash
venturalitica ui
```
