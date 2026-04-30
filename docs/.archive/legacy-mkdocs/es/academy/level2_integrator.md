# Nivel 2: El Integrador (GovOps y Visibilidad)

**Objetivo**: Transformar artefactos de MLOps en Evidencia Regulatoria con una capa de **GovOps**.

**Prerrequisito**: [Nivel 1 (El Ingeniero)](level1_policy.md)

**Contexto**: Continuando con "El Proyecto" (Loan Credit Scoring).

---

## 1. El Cuello de Botella: "En mi máquina funciona"

En el Nivel 1, arreglaste el sesgo localmente. Pero tu manager lo niega porque no puede ver la prueba.
Los emails con capturas de pantalla **no son cumplimiento**.

## 2. La Solución: La Capa GovOps

En **GovOps** (Assurance sobre MLOps), no tratamos el cumplimiento como un paso manual separado. En su lugar, usamos tu infraestructura existente de MLOps (MLflow, WandB) como un **Buffer de Evidencia** que cosecha automáticamente la prueba de seguridad durante el proceso de entrenamiento.

### A. La Integración (Assurance Implícita)

En un Pipeline profesional, la assurance es una capa que envuelve tu entrenamiento. Cada vez que entrenas un modelo, verificas su cumplimiento.

Tu tracker de experimentos ahora rastrea dos tipos de rendimiento: **Precisión** (Operacional) y **Cumplimiento** (Regulatorio).

> Código Completo: Puedes encontrar el script completo, listo para ejecutar, de este nivel aquí: [03_mlops_integration.py](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/03_mlops_integration.py)

=== "MLflow"

    ```python
    import mlflow
    import venturalitica as vl
    from venturalitica.quickstart import load_sample
    from dataclasses import asdict
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("loan-credit-scoring")

    # 0. Preparación de Datos
    df = load_sample("loan")
    X = df.select_dtypes(include=['number']).drop(columns=['class'])
    y = df['class']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 1. Iniciar la Sesión GovOps (Captura implícita de 'Audit Trace')
    with mlflow.start_run(), vl.monitor("train_v1"):
        # 2. Auditoría Pre-entrenamiento de Datos (Artículo 10)
        vl.enforce(
            data=df,
            target="class",
            gender="Attribute9",
            policy="data_policy.oscal.yaml"
        )

        # 3. Entrenar tu modelo
        model = LogisticRegression()
        model.fit(X_train, y_train)
        
        # 4. Auditoría Post-entrenamiento del Modelo (Artículo 15: Supervisión Humana)
        # Descargar model_policy.oscal.yaml: https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/model_policy.oscal.yaml
        results = vl.enforce(
            data=X_test.assign(prediction=model.predict(X_test)),
            target="prediction",               # Comprobando Comportamiento del Modelo
            gender="gender",
            policy="model_policy.oscal.yaml"   # Nueva política para Assurance del Modelo
        )
        
        # 5. Registrar todo en el Buffer de Evidencia
        passed = all(r.passed for r in results)
        mlflow.log_metric("val_accuracy", 0.92)
        mlflow.log_metric("compliance_score", 1.0 if passed else 0.0)
        mlflow.log_dict([asdict(r) for r in results], "compliance_results.json")
        
        if not passed:
            # CRÍTICO: Bloquear el pipeline si el modelo no es ético
            raise ValueError("Model failed ISO 42001 compliance check. See audit trace.")
    ```

    > **Nota**: `vl.monitor()` ahora captura **Evidencia Multimodal**: métricas de hardware/carbono Y la traza lógica de ejecución (historia del código AST).

=== "Weights & Biases"

    ```python
    import wandb
    import venturalitica as vl
    from venturalitica.quickstart import load_sample
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split

    wandb.init(project="loan-credit-scoring")

    # 0. Preparación de datos
    df = load_sample("loan")
    X = df.select_dtypes(include=['number']).drop(columns=['class'])
    y = df['class']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 1. Abrir un Contexto de Monitor
    with vl.monitor("wandb_sync"):
        # Auditoría Pre-entrenamiento (Artículo 10)
        vl.enforce(data=df, policy="data_policy.oscal.yaml", target="class")

        # 2. Entrenar y Auditar
        model = LogisticRegression(max_iter=1000)
        model.fit(X_train, y_train)

        # Auditoría Post-entrenamiento (Artículo 15)
        test_df = X_test.copy()
        test_df["class"] = y_test
        test_df["prediction"] = model.predict(X_test)
        # Descargar model_policy.oscal.yaml: https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/model_policy.oscal.yaml
        audit = vl.enforce(
            data=test_df,
            target="class",
            prediction="prediction",
            gender="Attribute9",
            policy="model_policy.oscal.yaml"
        )

    # 3. Registrar Artefactos de Cumplimiento
    artifact = wandb.Artifact('compliance-bundle', type='evidence')
    artifact.add_file(".venturalitica/results.json")
    wandb.log_artifact(artifact)

    passed = all(r.passed for r in audit)
    wandb.log({"accuracy": model.score(X_test, y_test), "compliance": 1.0 if passed else 0.0})

    if not passed:
        raise ValueError("Modelo rechazado por la política GovOps.")
    ```

### B. La Verificación (Dashboard)

Ahora que el código ha corrido, verifiquemos lo que enviamos.

1.  **Ejecuta la UI**:
    ```bash
    pip install venturalitica[dashboard]   # Requerido para la interfaz
    venturalitica ui
    ```
2.  **Chequeo de Logs**: Verifica que `.venturalitica/results.json` existe (esta es la salida por defecto de `enforce`).
3.  **Navega a "Estado de Política"**: Confirma que tu "Tratamiento de Riesgo" (el umbral ajustado) está registrado.

**Insight Clave**: "El reporte se ve profesional, y no escribí una sola palabra de él."

![Evidence Graph](../assets/academy/dashboard_overview.png)

---

## 3. Profundización: El Handshake de Dos Políticas (Art 10 vs 15)

El GovOps profesional requiere separación de preocupaciones. Ahora gestionas dos capas de assurance distintas:

1.  **Nivel 1 (Artículo 10)**: Verificó los **Datos Crudos** contra `data_policy.yaml`. El objetivo era probar que el dataset era justo antes de desperdiciar energía en entrenamiento.
2.  **Nivel 2 (Artículo 15)**: Verifica el **Comportamiento del Modelo** contra `model_policy.yaml`. El objetivo es probar que la IA toma decisiones justas en una ejecución de "Caja de Cristal".

| Etapa | Mapeo de Variables | Archivo de Política | Requisito Mandatorio |
| :--- | :--- | :--- | :--- |
| **Auditoría de Datos** | `target="class"` | [data_policy.oscal.yaml](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/data_policy.oscal.yaml) | **Artículo 10** (Assurance de Datos) |
| **Auditoría de Modelo** | `target="prediction"` | [model_policy.oscal.yaml](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/model_policy.oscal.yaml) | **Artículo 15** (Supervisión Humana) |

Este desacople es el núcleo del **Handshake**. Incluso si la Ley (`> 0.5`) permanece igual, el *sujeto* de la ley cambia de **Datos** a **Matemáticas**.

## 4. La Puerta (CI/CD)

Si `compliance_score == 0`, la build falla.
GitLab CI / GitHub Actions ahora pueden bloquear un despliegue basado en ética, igual que bloquean por errores de sintaxis.

---

## 5. Mensajes para Llevar a Casa

1.  **GovOps es Nativo**: La assurance no es un paso extra; es un context manager (`vl.monitor`) alrededor de tu entrenamiento.
2.  **Telemetría es Evidencia**: RAM, CO2 y resultados de Traza no son solo métricas--cumplen con la supervisión del **Artículo 15**.
3.  **Traza Unificada**: `vl.monitor()` captura todo, desde uso de hardware hasta análisis de código AST, en un solo archivo `.json`.
4.  **Fricción Cero**: El Data Scientist sigue usando MLflow/WandB, mientras el SDK cosecha la evidencia.

---

### Referencias

- **[Referencia de API](../api.md)** -- Firmas de `enforce()` y `monitor()`
- **[Autoría de Políticas](../policy-authoring.md)** -- Cómo escribir políticas OSCAL
- **[Referencia de Probes](../probes.md)** -- Qué captura `monitor()` automáticamente
- **[Column Binding](../column-binding.md)** -- Cómo funciona `gender="Attribute9"`

**[Siguiente: Nivel 3 (El Auditor)](level3_auditor.md)**
