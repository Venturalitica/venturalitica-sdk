# Venturalitica

**La Caja de Cristal para IA de Alto Riesgo.**

Venturalitica transforma tu código Python en **Evidencia Legal**. Mapea automáticamente tus métricas técnicas, auditorías de datos y logs de ejecución a la **Ley de IA de la UE (Artículos 9-15)** sin salir de tu entorno local.

---

## Inicio Rápido en 60 Segundos

```bash
pip install venturalitica
```

Detecta sesgos en tus conjuntos de datos o modelos con una sola línea de código:

```python
import venturalitica as vl

# Run a full audit on the built-in loan scenario
results = vl.quickstart('loan')
```

Luego lanza el **Dashboard Caja de Cristal** para explorar los resultados:

```bash
venturalitica ui
```

---

## Características Clave

| Característica | Descripción |
| :--- | :--- |
| **`enforce()`** | Audita conjuntos de datos y modelos contra políticas OSCAL con más de 35 métricas integradas. |
| **`monitor()`** | Envuelve ejecuciones de entrenamiento con recolección automática de evidencia (BOM, hardware, carbono). |
| **Dashboard Caja de Cristal** | Flujo de trabajo regulatorio en 4 fases: Identidad, Política, Verificación, Reporte. |
| **Política como Código** | Define reglas de Assurance en formato OSCAL `assessment-plan`. |
| **Column Binding** | Desacopla políticas de esquemas mediante resolución de columnas basada en sinónimos. |
| **Soberanía Local** | Sin dependencia de la nube. Toda la verificación se ejecuta localmente. |
| **Anexo IV** | Auto-redacción de documentación técnica a partir de trazas locales. |

---

## Documentación

| Guía | Descripción |
| :--- | :--- |
| **[Inicio Rápido](quickstart.md)** | Ejecuta un escaneo de cumplimiento completo en 2 minutos. |
| **[Referencia de API](api.md)** | `enforce()`, `monitor()`, `wrap()`, `quickstart()`, `PolicyManager`. |
| **[Referencia de Métricas](metrics.md)** | Más de 35 métricas en 7 categorías. |
| **[Autoría de Políticas](policy-authoring.md)** | Escribe políticas OSCAL desde cero. |
| **[Guía del Dashboard](dashboard.md)** | El flujo de trabajo en 4 fases de la Caja de Cristal. |
| **[Column Binding](column-binding.md)** | Mapea nombres abstractos a columnas de DataFrame. |
| **[Referencia de Probes](probes.md)** | 7 probes de evidencia para cumplimiento con la Ley de IA de la UE. |
| **[Funcionalidades Experimentales](experimental.md)** | CLI `login`/`pull`/`push` (vista previa SaaS). |

### Academy (Aprendizaje Paso a Paso)

| Nivel | Rol | Enfoque |
| :--- | :--- | :--- |
| **[Nivel 1](academy/level1_policy.md)** | Autor de Políticas | Escribe tu primera política OSCAL para el escenario de préstamos. |
| **[Nivel 2](academy/level2_integrator.md)** | Integrador | Añade `enforce()` a tu Pipeline de ML. |
| **[Nivel 3](academy/level3_auditor.md)** | Auditor | Revisa evidencia e interpreta resultados. |
| **[Nivel 4](academy/level4_annex_iv.md)** | Responsable de Cumplimiento | Genera documentación técnica del Anexo IV. |

### Tutoriales

- **[Escribir Políticas Code-First](tutorials/01_writing_policy.md)** -- Traduce requisitos legales a controles OSCAL.

---

## Instalación

```bash
pip install venturalitica
```

Requiere Python 3.9+. Para el Dashboard, el extra opcional `dashboard` se incluye por defecto.

---

## Enlaces

[Guía de Inicio Rápido](quickstart.md) | [Referencia de API](api.md) | [GitHub](https://github.com/venturalitica/venturalitica-sdk)

*   **¿Encontraste un error o quieres proponer una funcionalidad?** Abre un **[GitHub Issue](https://github.com/venturalitica/venturalitica-sdk/issues/new)**.

(c) 2026 Venturalitica | Construido para una IA Responsable
