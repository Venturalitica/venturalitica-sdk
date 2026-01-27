# Nivel 2: El Integrador (GovOps y Visibilidad) 🟡

**Objetivo**: Transformar artefactos de MLOps en Evidencia Regulatoria con una capa de **GovOps**.

**Prerrequisito**: [Nivel 1 (El Ingeniero)](level1_policy.md)

**Contexto**: Continuando con "El Proyecto".

---

## 1. El Cuello de Botella: "En mi máquina funciona"

En el Nivel 1, arreglaste el sesgo localmente. Pero tu manager lo niega porque no puede ver la prueba.
Los emails con capturas de pantalla **no son cumplimiento**.

## 2. La Solución: La Capa GovOps

En **GovOps** (Gobernanza sobre MLOps), no tratamos el cumplimiento como un paso manual separado. En su lugar, usamos tu infraestructura existente de MLOps (MLflow, WandB) como un **Buffer de Evidencia** que cosecha automáticamente la prueba de seguridad durante el proceso de entrenamiento.

### A. La Integración (Gobernanza Implícita)

En un pipeline profesional, la gobernanza es una capa que envuelve tu entrenamiento. Cada vez que entrenas un modelo, verificas su cumplimiento.

Tu tracker de experimentos ahora rastrea dos tipos de rendimiento: **Precisión** (Operacional) y **Cumplimiento** (Regulatorio).

=== "MLflow"

    ```python
    import mlflow
    import venturalitica as vl
    from dataclasses import asdict

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("loan-credit-scoring")

    # 1. Iniciar Sesión GovOps (Captura implícita de 'Audit Trace')
    with mlflow.start_run(), vl.monitor("train_v1"):
        # 2. Entrenar tu modelo
        # model.fit(X_train, y_train)
        
        # 3. Aplicar Cumplimiento (Artículo 15: Supervisión Humana)
        results = vl.enforce(
            data=X_test.assign(prediction=model.predict(X_test)),
            target="prediction",               # 🧠 Comprobando Comportamiento del Modelo
            gender="gender",
            policy="model_policy.yaml"         # 🗝️ Nueva política para Gobernanza del Modelo
        )
        
        # 4. Registrar todo en el Buffer de Evidencia
        passed = all(r.passed for r in results)
        mlflow.log_metric("val_accuracy", 0.92)
        mlflow.log_metric("compliance_score", 1.0 if passed else 0.0)
        mlflow.log_dict([asdict(r) for r in results], "compliance_results.json")
        
        if not passed:
            # 🛑 CRÍTICO: Bloquear el pipeline si el modelo no es ético
            raise ValueError("El modelo falló el cumplimiento ISO 42001. Ver traza de auditoría.")
    ```

    > **Nota**: `vl.monitor()` ahora captura **Evidencia Multimodal**: métricas de hardware/carbono Y la traza lógica de ejecución (historia del código AST).

=== "Weights & Biases"

    ```python
    import wandb
    import venturalitica as vl

    wandb.init(project="loan-credit-scoring")

    # 1. Abrir Contexto de Monitor
    with vl.monitor("wandb_sync"):
        # model.fit(X_train, y_train)
        
        # 2. Ejecutar Enforce (Artículo 15)
        audit = vl.enforce(
            data=pd.read_csv("val_data.csv"),
            policy="model_policy.yaml",
            target="prediction"
        )

    # 3. Registrar Artefactos de Cumplimiento
    artifact = wandb.Artifact('compliance-bundle', type='evidence')
    artifact.add_file(".venturalitica/results.json")
    artifact.add_file(".venturalitica/trace_wandb_sync.json")
    wandb.log_artifact(artifact)
    
    passed = all(r.passed for r in audit)
    wandb.log({"accuracy": 0.89, "compliance": 1.0 if passed else 0.0})
    
    if not passed:
        raise ValueError("Modelo rechazado por política de GovOps.")
    ```

### B. La Verificación (Dashboard)

Ahora que el código ha corrido, verifiquemos lo que enviamos.

1.  **Ejecuta la UI**:
    ```bash
    uv run venturalitica ui
    ```
2.  **Chequeo de Logs**: Verifica que `.venturalitica/results.json` existe.
3.  **Navega a "Estado de Política"**: Confirma que tu "Tratamiento de Riesgo" (el umbral ajustado) está registrado.

**Insight Clave**: "El reporte se ve profesional, y no escribí una sola palabra de él."

![Evidence Graph](../assets/academy/dashboard_overview.png)

---

## 3. Profundización: El Handshake de Dos Políticas (Art 10 vs 15)

El GovOps profesional requiere separación de preocupaciones. Ahora gestionas dos capas de gobernanza distintas:

1.  **Nivel 1 (Artículo 10)**: Verificó los **Datos Crudos** contra `data_policy.yaml`. El objetivo era probar que el dataset era justo antes de desperdiciar energía en entrenamiento.
2.  **Nivel 2 (Artículo 15)**: Verifica el **Comportamiento del Modelo** contra `model_policy.yaml`. El objetivo es probar que la IA toma decisiones justas en una ejecución de "Caja de Cristal".

| Etapa | Mapeo de Variables | Archivo de Política | Requisito Mandatorio |
| :--- | :--- | :--- | :--- |
| **Auditoría de Datos** | `target="class"` | `data_policy.yaml` | **Artículo 10** (Gobernanza de Datos) |
| **Auditoría de Modelo** | `target="prediction"` | `model_policy.yaml` | **Artículo 15** (Supervisión Humana) |

Este desacople es el núcleo del **Handshake**. Incluso si la Ley (`> 0.5`) permanece igual, el *sujeto* de la ley cambia de **Datos** a **Matemáticas**.

## 4. La Puerta (CI/CD)

Si `compliance_score == 0`, la build falla.
GitLab CI / GitHub Actions ahora pueden bloquear un despliegue basado en ética, igual que bloquean por errores de sintaxis.

---

## 5. Mensajes para Llevar a Casa 🏠

1.  **GovOps es Nativo**: La gobernanza no es un paso extra; es un context manager (`vl.monitor`) alrededor de tu entrenamiento.
2.  **Telemetría es Evidencia**: RAM, CO2 y Traza no son solo métricas—cumplen con la supervisión del **Artículo 15**.
3.  **Traza Unificada**: `vl.monitor()` captura todo, desde uso de hardware hasta análisis de código AST, en un solo archivo `.json`.
4.  **Fricción Cero**: El Data Scientist sigue usando MLflow/WandB, mientras el SDK cosecha la evidencia.

👉 **[Siguiente: Nivel 3 (El Auditor)](level3_auditor.md)**
