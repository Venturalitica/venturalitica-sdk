# De Cero a Pro: El Viaje de 5 Minutos 🚀

**Objetivo**: Transformarte de "Desarrollador Python" a "Ingeniero de Gobernanza IA" en 3 pasos.

______________________________________________________________________

## La Filosofía: Cumplimiento como Código

Estás acostumbrado a `pytest` para verificar si tu función suma 2+2 correctamente. Pero, ¿cómo pruebas si tu modelo de IA respeta los **Derechos Humanos**?

Venturalítica trata la "Gobernanza" como una dependencia. En lugar de consejos legales vagos, defines **Políticas (OSCAL)** estrictas. Tu pipeline CI/CD las aplica igual que reglas de linter.

### El Plan de Estudios

| Nivel                                                                                                  | Rol               | Objetivo                                       | Proyecto                         |
| ------------------------------------------------------------------------------------------------------ | ----------------- | ---------------------------------------------- | -------------------------------- |
| **[Empieza Aquí](#paso-1-instalacion)**                                                                | **Desarrollador** | Ejecuta tu primera auditoría en < 60s.         | `loan-credit-scoring`            |
| **[Nivel 1](https://venturalitica.github.io/venturalitica-sdk/es/academy/level1_policy/index.md)**     | **Ingeniero**     | **Implementar Controles** para Riesgos.        | Política Personalizada           |
| **[Nivel 2](https://venturalitica.github.io/venturalitica-sdk/es/academy/level2_integrator/index.md)** | **Integrador**    | **Viz & MLOps**: "Cumplimiento como Metadata". | MLOps / Dashboard                |
| **[Nivel 3](https://venturalitica.github.io/venturalitica-sdk/es/academy/level3_auditor/index.md)**    | **Auditor**       | Prueba: "Confía en la Caja de Cristal".        | `loan-credit-scoring` (Avanzado) |
| **[Nivel 4](https://venturalitica.github.io/venturalitica-sdk/es/academy/level4_annex_iv/index.md)**   | **Arquitecto**    | Docs GenAI: "Anexo IV".                        | `loan-credit-scoring` (Anexo IV) |

______________________________________________________________________

## Paso 1: Instalación

Recomendamos **uv** para velocidad extrema, o `pip` estándar.

```
uv pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
# O
pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
```

## Paso 2: Obtén el Código 📦

Para seguir la **Academia**, clona el repositorio de ejemplos. Este será tu directorio de trabajo para todos los niveles.

```
git clone https://github.com/venturalitica/venturalitica-sdk-samples.git
cd venturalitica-sdk-samples/scenarios/loan-credit-scoring
```

## Paso 3: Ejecutando Tu Primera Auditoría ⚡

Ejecuta esta única línea de código. Descarga un dataset, carga una política y audita un modelo de riesgo crediticio.

```
import venturalitica as vl

# Ejecutar el escenario 'loan' (préstamos)
vl.quickstart('loan')
```

**Salida:**

```
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
> - **La Política**: `ratio > 0.5` (La Ley).
> - **La Realidad**: `0.361` (Tu Código).
> - **El Veredicto**: `❌ FAIL` (La Brecha de Cumplimiento).

No necesitaste un abogado. Solo necesitaste una falla de test visible.

## Paso 4: Elige Tu Camino

Ahora que has visto la falla, aprende cómo arreglarla y verificarla.

- ## **[Nivel 1: El Ingeniero](https://venturalitica.github.io/venturalitica-sdk/es/academy/level1_policy/index.md)**
  Aprende a implementar **Controles** que mitigan Riesgos identificados. **Detecta y Bloquea** modelos no conformes.
- ## **[Nivel 2: El Integrador](https://venturalitica.github.io/venturalitica-sdk/es/academy/level2_integrator/index.md)**
  Registra resultados en herramientas MLOps y verifica resultados visualmente en el **Dashboard**.
- ## **[Nivel 3: El Auditor](https://venturalitica.github.io/venturalitica-sdk/es/academy/level3_auditor/index.md)**
  Aprende a realizar una auditoría de "Caja de Cristal" en el modelo de préstamos y genera pruebas criptográficas.
- ## **[Nivel 4: El Arquitecto](https://venturalitica.github.io/venturalitica-sdk/es/academy/level4_annex_iv/index.md)**
  El Nivel Jefe. Entrena un modelo financiero de alto riesgo y genera la masiva Documentación Técnica requerida por la EU AI Act.

______________________________________________________________________

## 📚 Referencias Externas

- **EU AI Act**: [Texto Legal Completo (EUR-Lex)](https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=CELEX:52021PC0206) (Español)
- **ISO 42001**: [Sistema de Gestión de IA (AIMS)](https://www.iso.org/standard/81230.html)
- **NIST AI RMF**: [Marco de Gestión de Riesgos 1.0](https://www.nist.gov/itl/ai-risk-management-framework)
