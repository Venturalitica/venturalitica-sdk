# De Cero a Pro: El Viaje de 5 Minutos 🚀

**Objetivo**: Transformarte de "Desarrollador Python" a "Ingeniero de Gobernanza IA" en 3 pasos.

---

## La Filosofía: Cumplimiento como Código

Estás acostumbrado a `pytest` para verificar si tu función suma 2+2 correctamente.
Pero, ¿cómo pruebas si tu modelo de IA respeta los **Derechos Humanos**?

Venturalítica trata la "Gobernanza" como una dependencia. En lugar de consejos legales vagos, defines **Políticas (OSCAL)** estrictas. Tu pipeline CI/CD las aplica igual que reglas de linter.

### El Plan de Estudios

| Nivel | Rol | Objetivo |
| :--- | :--- | :--- |
| **[Empieza Aquí](#paso-1-instalacion)** | **Desarrollador** | Ejecuta tu primera auditoría en < 60s. |
| **[Nivel 1](level1_policy.md)** | **Ingeniero** | **Implementar Controles** para Riesgos. |
| **[Nivel 2](level2_integrator.md)** | **Integrador** | **Viz & MLOps**: "Cumplimiento como Metadata". |
| **[Nivel 3](level3_auditor.md)** | **Auditor** | Prueba: "Confía en la Caja de Cristal". |
| **[Nivel 4](level4_annex_iv.md)** | **Arquitecto** | Docs GenAI: "Anexo IV". |

---

## Paso 1: Instalación
Recomendamos **uv** para velocidad extrema, o `pip` estándar.

```bash
uv pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
# O
pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
```

## Paso 2: Obtén el Código 📦

Para seguir la **Academia**, clona el repositorio de ejemplos. Este será tu directorio de trabajo para todos los niveles.

```bash
git clone https://github.com/venturalitica/venturalitica-sdk-samples.git
cd venturalitica-sdk-samples/scenarios/loan-credit-scoring
```

## Paso 3: Ejecutando Tu Primera Auditoría ⚡

Ejecuta esta única línea de código. Descarga un dataset, carga una política y audita un modelo de riesgo crediticio.

```python
import venturalitica as vl

# Ejecutar el escenario 'loan' (préstamos)
vl.quickstart('loan')
```

**Salida:**

```text
  CONTROL                DESCRIPTION                            RESULT
  ──────────────────────────────────────────────────────────────────────
  credit-data-bias       Disparate impact ratio > 0.8           ✅ PASS
  credit-age-disparate   Age disparity ratio > 0.5              ❌ FAIL
  ──────────────────────────────────────────────────────────────────────
  Audit Summary: ❌ VIOLATION | 1/2 controls passed
```

### 💡 Mensaje para Llevar a Casa
> **"El Cumplimiento transforma Principios vagos en restricciones de Ingeniería verificables."**
>
> *   **La Política**: `ratio > 0.5` (La Ley).
> *   **La Realidad**: `0.361` (Tu Código).
> *   **El Veredicto**: `❌ FAIL` (La Brecha de Cumplimiento).

No necesitaste un abogado. Solo necesitaste una falla de test visible.

## Paso 4: Elige Tu Camino

Ahora que has visto la falla, aprende cómo arreglarla y verificarla.

<div class="grid cards" markdown>

-   :material-shield-check: **[Nivel 1: El Ingeniero](level1_policy.md)**
    ---
    Aprende a implementar **Controles** que mitigan Riesgos identificados. **Detecta y Bloquea** modelos no conformes.

-   :material-chart-bar: **[Nivel 2: El Integrador](level2_integrator.md)**
    ---
    Registra resultados en herramientas MLOps y verifica resultados visualmente en el **Dashboard**.

-   :material-fingerprint: **[Nivel 3: El Auditor](level3_auditor.md)**
    ---
    Aprende a realizar una auditoría de "Caja de Cristal" en el modelo de préstamos y genera pruebas criptográficas.

-   :material-hospital-box: **[Nivel 4: El Arquitecto](level4_annex_iv.md)**
    ---
    El Nivel Jefe. Entrena un modelo financiero de alto riesgo y genera la masiva Documentación Técnica requerida por la EU AI Act.

</div>

---

## 📚 Referencias Externas

- **EU AI Act**: [Texto Legal Completo (EUR-Lex)](https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=CELEX:52021PC0206) (Español)
- **ISO 42001**: [Sistema de Gestión de IA (AIMS)](https://www.iso.org/standard/81230.html)
- **NIST AI RMF**: [Marco de Gestión de Riesgos 1.0](https://www.nist.gov/itl/ai-risk-management-framework)
