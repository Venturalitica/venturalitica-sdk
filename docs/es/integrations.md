# Integraciones MLOps (La Guía de Operaciones)

Esta guía se centra en la **Persona MLOps**: quien automatiza el pipeline.
Venturalítica se integra estrictamente con tus herramientas existentes para asegurar que la **Evidencia (Artículo 12)** se recopile automáticamente durante tus ejecuciones de CI/CD.

---

## El Concepto

No queremos reemplazar tu pila de MLOps. Queremos **certificarla**.

| Herramienta | Integración | Beneficio |
|:--|:--|:--|
| **MLflow / WandB** | `vl.wrap()` | Vincula automáticamente la Política `model_policy.yaml` a los artefactos de la ejecución. |
| **Panel de Estado** | `venturalitica ui` | Proporciona verificaciones de salud tipo "Semáforo" para tu pipeline de cumplimiento. |

---

## 1. Versionado Regulatorio

Cada vez que entrenas un modelo usando `vl.wrap()` o `vl.monitor()`, Venturalítica automáticamente toma una instantánea de tu política de gobernanza (`model_policy.yaml`) y la sube a tu servidor de seguimiento activo.

*   **¿Por qué?** Asegura que tu rastro de auditoría sea estrictamente reproducible. Puedes probar exactamente *qué* reglas estaban activas durante el entrenamiento (ej. "Política v1.2 vs v1.3").
*   **¿Dónde?** Busca `policy_snapshot` en tus artefactos de MLflow o archivos de WandB.

---

## 2. Guía de Configuración

### Weights & Biases (Nube)
Venturalítica detecta automáticamente ejecuciones de `wandb`.

1.  **Configurar**: Establece `WANDB_API_KEY` en tu `.env`.
2.  **Ejecutar**: Solo usa `vl.wrap(model)` dentro de tu script.
3.  **Verificar**: Abre `venturalitica ui` -> **Integraciones**.

### MLflow (Local/Remoto)
Compatible tanto con `mlruns` locales como con Servidores de Seguimiento remotos.

1.  **Configurar**: Establece `MLFLOW_TRACKING_URI` (opcional, predeterminado a `./mlruns`).
2.  **Ejecutar**: Asegúrate de que `mlflow.start_run()` esté activo cuando llames a `fit()`.
3.  **Verificar**: La UI generará enlaces profundos a tu Experimento y ID de Ejecución específicos.

---

## 3. Ejemplo (Escenario de Préstamo)

Aquí se muestra cómo automatizar la **Auditoría del Artículo 15** dentro de un pipeline estándar.

```python
import venturalitica as vl
import mlflow
from sklearn.ensemble import RandomForestClassifier

# 1. Definir Política (El Estándar)
policy = "model_policy.yaml"

# 2. Iniciar Ejecución MLOps
with mlflow.start_run():
    
    # 3. Envoltura Transparente (La Capa de Gobernanza)
    # Esto captura automáticamente la instantánea 'model_policy.yaml'
    model = vl.wrap(RandomForestClassifier(), policy=policy)
    
    # 4. Entrenar (Evidencia y Artefactos auto-subidos)
    model.fit(
        X_train, y_train,
        audit_data=train_df,
        gender="Attribute9",  # Mapeo estricto para auditoría
        age="Attribute13"
    ) 
```
