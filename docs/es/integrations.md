# Integraciones Profundas (Caja de Cristal v2.0)

Venturalítica v0.4.0 introduce **Integraciones Profundas**, diseñadas para hacer que la Gobernanza de IA sea una parte perfecta de tu flujo de trabajo MLOps existente. Llamamos a esto "Caja de Cristal 2.0": visibilidad completa tanto en el código como en los artefactos regulatorios que lo gobernaron.

## Características

### 1. Versionado Regulatorio
Cada vez que entrenas un modelo usando `vl.wrap()`, Venturalítica automáticamente toma una instantánea de tu política de gobernanza (`oscal.yaml`) y la sube a tu servidor de seguimiento activo.

-   **¿Por qué?** Asegura que tu rastro de auditoría sea estrictamente reproducible. Puedes probar exactamente *qué* reglas estaban activas durante el entrenamiento.
-   **¿Dónde?** Busca `policy_snapshot` en tus artefactos de MLflow o archivos de WandB.

### 2. Pestaña de Estado de Integraciones
La nueva pestaña **Integraciones** en `venturalitica ui` proporciona una verificación de salud en tiempo real de tu ecosistema de gobernanza.

-   **Sistema de Semáforo**: Ve instantáneamente si tu MLflow local o WandB en la Nube están conectados.
-   **Enlaces Profundos**: Navegación de un clic a la ejecución *exacta* en tu herramienta MLOps que produjo la evidencia.

## Configuración

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

## Ejemplo

```python
import venturalitica as vl
import mlflow

# 1. Definir Política
policy = "risks.oscal.yaml"

# 2. Iniciar Ejecución MLOps
with mlflow.start_run():
    # 3. Envoltura Transparente
    model = vl.wrap(RandomForestClassifier(), policy=policy)
    
    # 4. Entrenar (Artefactos auto-subidos)
    model.fit(X_train, y_train) 
```
