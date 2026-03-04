# Nivel 4: El Arquitecto (Generacion Anexo IV)

**Objetivo**: Automatizar la creacion de documentos regulatorios de 50+ paginas.

**Prerrequisito**: [Nivel 3 (El Auditor)](level3_auditor.md)

---

## 1. El Cuello de Botella: "Documentacion Tecnica"

De acuerdo con el **Articulo 11** y **Anexo IV** de la EU AI Act, los sistemas de Alto Riesgo (como **Scoring de Credito**) requieren Documentacion Tecnica exhaustiva.
Escribir esto manualmente toma **semanas**.

## 2. La Solucion: Cumplimiento Generativo

Usamos tus **Politicas (Nivel 1 & 2)** y **Evidencia (Nivel 2/3)** para invocar a un LLM que redacte el documento por ti.

Venturalitica soporta:

- **Nube**: Mistral (via API).
- **Local**: Ollama (Proposito general).
- **Soberana (NUEVO)**: **ALIA** (Nativo Espanol GGUF via Llama.cpp) - *Experimental*.

### El Upgrade

Continuamos trabajando en el proyecto de "Scoring de Credito".

> Codigo Completo: Puedes encontrar el script de automatizacion para la generacion del Anexo IV aqui: [generate_annex_iv.py](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/generate_annex_iv.py)

### Ejecutar la Auditoria de Alto Riesgo

Asegurate de haber corrido los pasos de recoleccion:

```python
import venturalitica as vl
from venturalitica.quickstart import load_sample

# 1. Cargar Datos
df = load_sample("loan")
train_df = df.sample(frac=0.8, random_state=42)
val_df = df.drop(train_df.index)

# 2. Ejecutar la Auditoria de Assurance de Articulo 10 (Datos) y Articulo 15 (Modelo)
with vl.monitor("loan_annex_audit"):
    # 2.1 Verificar Datos de Entrenamiento (Art 10)
    # Descarga data_policy.oscal.yaml desde:
    # https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/data_policy.oscal.yaml
    vl.enforce(
        data=train_df,
        target="class",
        gender="Attribute9",
        age="Attribute13",
        policy="data_policy.oscal.yaml"
    )
    
    # 2.2 Verificar Rendimiento del Modelo (Art 15)
    # Descarga model_policy.oscal.yaml desde:
    # https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/scenarios/loan-credit-scoring/policies/loan/model_policy.oscal.yaml
    vl.enforce(
        data=val_df.assign(prediction=val_df["class"]),  # Modelo simulado
        target="class",
        prediction="prediction",
        gender="Attribute9",
        policy="model_policy.oscal.yaml"
    )
```

## 3. Generar el Documento

1.  Instala las dependencias del dashboard: `pip install venturalitica[dashboard]`
2.  Abre el Dashboard: `venturalitica ui`.
3.  Ve a la pestana **"Generador Anexo IV"**.
4.  Selecciona Proveedor: **Nube (Mistral)**, **Local (Ollama)**, o **Soberana (ALIA - Experimental)**.
5.  Haz click en **"Generar Anexo IV"**.

    ![Generador Anexo IV](../assets/academy/annex_iv_generator.png)

### El Proceso de Generacion
Observa los logs. El Sistema actua como un **Equipo de Agentes**:

1.  **Scanner**: Lee tu `trace.json` (La Evidencia).
2.  **Planner**: Decide que secciones del Anexo IV aplican a tu tipo de modelo especifico.
3.  **Writer**: Redacta "Seccion 2.c: Arquitectura" usando el `summary()` de tu codigo Python real.
4.  **Critic**: Revisa el borrador contra el estandar ISO 42001.

**Resultado**: Un archivo markdown (`Annex_IV.md`) que cita tus puntajes de precision especificos (ej. `Demographic Parity: 0.92`) como prueba de seguridad.

## 4. Seleccionando tu LLM

| Caracteristica | Nube (Mistral API) | Local (Ollama) | Soberana (ALIA - Experimental) |
| :--- | :--- | :--- | :--- |
| **Privacidad** | Transporte Encriptado | 100% Offline | Bloqueado por Hardware |
| **Soberania** | Alojado en UE | Generico | **Nativo Espanol** |
| **Velocidad** | Rapido (Modelo Grande) | Mas lento | **Lento (Experimental)** |
| **Caso de Uso** | Pulido Final de Alta Calidad | Testing Iterativo | **Solo Investigacion** |

Actualmente ofrecemos **ALIA** como una feature experimental para organizaciones pilotando IA soberana nativa en espanol.

!!! warning "Feature Experimental y Requisitos de Hardware"
    ALIA es un modelo de 40B parametros. Esta marcado como **EXPERIMENTAL** y requiere recursos de hardware significativos:
    
    *   **RAM/VRAM**: ~41GB requeridos (cuantizacion Q8).
    *   **GPU**: Se recomienda una GPU de gama alta (ej. RTX 3090/4090 con 24GB+) para velocidades usables.
    *   **Rendimiento**: En hardware de consumo o GPUs mas pequenas (como RTX 2000), la inferencia correra efectivamente en CPU y sera muy lenta.

## 5. Exportar a PDF

Por defecto, generamos `Annex_IV.md` (Markdown) para control de versiones. Para convertir esto a un PDF de grado regulatorio:

=== "Python (mdpdf)"
    ```bash
    uv pip install mdpdf
    uv run mdpdf Annex_IV.md
    ```

=== "Pandoc (Avanzado)"
    ```bash
    pandoc Annex_IV.md -o Annex_IV.pdf --toc --pdf-engine=xelatex
    ```

## 6. Mensajes para Llevar a Casa

1.  **La Documentacion es una Funcion**: `f(Evidencia) -> Documento`. Nunca escribas lo que puedes generar.
2.  **LiveTrace**: Si tu precision cae manana, regenera el documento. Reflejara el estado *actual*, previniendo la "Deriva de Documentacion".
3.  **El Bucle Completo**: Has ido de Codigo -> Politica (N1) -> Ops (N2) -> Evidencia (N3) -> Documento Legal (N4).

---

### Felicidades!
Has completado la **Academia Venturalitica**.
Ahora estas listo para integrar esto en tu propio Pipeline CI/CD.

### Referencias

- **[Ciclo de Vida Completo](../full-lifecycle.md)** -- El flujo completo en una sola pagina para copiar y pegar
- **[Guia del Dashboard](../dashboard.md)** -- Tutorial detallado del Dashboard y la Fase 4
- **[Referencia de Metricas](../metrics.md)** -- Todas las 35+ metricas disponibles para politicas
- **[Creacion de Politicas](../policy-authoring.md)** -- Escribe politicas OSCAL personalizadas
