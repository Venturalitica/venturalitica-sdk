# Inicio Rápido en 60 Segundos

**Objetivo**: Tu primera auditoría de sesgo en menos de 60 segundos.

---
## Los fundamentos: Del Riesgo al Código

Construir una IA de Alto Riesgo requiere un cambio fundamental en cómo abordamos las pruebas. Ya no es suficiente verificar la precisión técnica (por ejemplo, F1 Score); ahora debemos probar matemáticamente que el sistema respeta los derechos fundamentales, como la no discriminación o la calidad de los datos, tal como lo exige la **Ley de IA de la UE**.

Venturalítica automatiza esto tratando la "Gobernanza" como una dependencia. En lugar de vagos requisitos legales, defines políticas estrictas (OSCAL) que tu modelo debe aprobar antes de ser desplegado. Esto convierte el cumplimiento en un problema de ingeniería determinista.

!!! question "¿Es mi Sistema de Alto Riesgo?"
    Según el [**Artículo 6**](https://artificialintelligenceact.eu/es/article/6/) de la Ley de IA de la UE, un sistema es de Alto Riesgo si está cubierto por el [**Anexo I**](https://artificialintelligenceact.eu/es/annex/1/) (Componentes de Seguridad como maquinaria/dispositivos médicos) o listado en el [**Anexo III**](https://artificialintelligenceact.eu/es/annex/3/) (Biometría, Infraestructura Crítica, Educación, Empleo, Servicios Esenciales, Cumplimiento de la Ley, Migración, Justicia/Democracia).

**La Capa de Traducción:**

1.  **Riesgo Fundamental**: "El modelo no debe discriminar a grupos protegidos" (Art 9).

2.  **Control de Política**: "La Tasa de Impacto Dispar debe ser > 0.8".

3.  **Aserción de Código**: `assert calculated_metric > 0.8`.

Cuando ejecutas `quickstart()`, técnicamente estás ejecutando una **Prueba Unitaria de Ética**.

---
## Paso 1: Instalación

```bash
pip install git+https://github.com/Venturalitica/venturalitica-sdk.git
```

---

## Paso 2: Ejecuta Tu Primera Auditoría

```python
import venturalitica as vl

vl.quickstart('loan')
```

**Salida:**

```text
[Venturalítica {{ version }}] 🎓 Escenario: Equidad en Calificación Crediticia
[Venturalítica {{ version }}] 📊 Cargado: UCI Dataset #144 (1000 muestras)

  CONTROL                DESCRIPCION                            ACTUAL     LIMITE     RESULTADO
  ────────────────────────────────────────────────────────────────────────────────────────────────
  credit-data-imbalance  Calidad de Datos                       0.431      > 0.2      ✅ PASS
  credit-data-bias       Impacto Dispar                         0.836      > 0.8      ✅ PASS
  credit-age-disparate   Disparidad por Edad                    0.361      > 0.5      ❌ FAIL
  ────────────────────────────────────────────────────────────────────────────────────────────────
  Resumen de Auditoría: ❌ VIOLACIÓN | 2/3 controles pasados
```

!!! info
    La auditoría detectó un sesgo basado en la edad en el conjunto de datos de Crédito Alemán UCI.

## Paso 3: Qué Sucede Bajo el Capó

La función `quickstart()` es un envoltorio que realiza el ciclo de vida completo de cumplimiento de una sola vez:

1.  **Descarga Datos**: Obtiene el conjunto de datos de Crédito Alemán UCI.
2.  **Carga Política**: Lee `risks.oscal.yaml` que define las reglas de equidad.
3.  **Ejecuta**: Corre la auditoría (`vl.enforce`).
4.  **Registra**: Captura la evidencia (`trace.json`) para el panel de control.

Aquí está el código "manual" equivalente:

```python
from ucimlrepo import fetch_ucirepo
import venturalitica as vl

# 1. Cargar Datos (La "Fuente de Riesgo")
dataset = fetch_ucirepo(id=144)
df = dataset.data.features
df['class'] = dataset.data.targets

# 2. Definir la Política (La "Ley")
# Cargamos una pre-definida policies/risks.oscal.yaml

# 3. Ejecutar la Auditoría (La "Prueba")
# Esto genera automáticamente la Lista de Materiales de Evidencia (BOM)
with vl.tracecollector("manual_audit"):
    vl.enforce(
        data=df,
        target="class",          # El resultado (True/False)
        gender="Attribute9",     # Grupo Protegido A
        age="Attribute13",       # Grupo Protegido B
        policy="risks.oscal.yaml"
    )
```

### La Lógica de la Política

La política (`risks.oscal.yaml`) es el puente. Le dice al SDK *qué* verificar para que no tengas que codificarlo.

```yaml
# ... dentro del YAML OSCAL ...
- control-id: credit-data-bias
  description: "La tasa de impacto dispar debe ser > 0.8 (regla del 80%)"
  props:
    - name: metric_key
      value: disparate_impact   # <--- La Función Python a llamar
    - name: threshold
      value: "0.8"              # <--- El Límite a aplicar
    - name: operator
      value: ">"                # <--- La Lógica (> 0.8)
    - name: "input:dimension"
      value: gender             # <--- Mapea a "Attribute9"
```

Este diseño desacopla la **Gobernanza** (el archivo de política) de la **Ingeniería** (el código python).

---

## Por Qué Importa Esto

Sin este mecanismo, tu modelo de IA es una "Caja Negra" legal:

*   **Responsabilidad Civil**: No puedes probar que verificaste el sesgo *antes* del despliegue (Art 9).
*   **Fragilidad**: El cumplimiento es una lista de verificación manual, fácil de olvidar u omitir.
*   **Opacidad**: Los auditores no pueden ver el vínculo entre tu código y la ley.

Al ejecutar `quickstart()`, acabas de generar un **Artefacto de Cumplimiento** inmutable. Incluso si las leyes cambian, tu evidencia permanece.

## Paso 4: El Panel de Control "Caja de Cristal" 📊

Ahora que tenemos la evidencia (la grabación de la "Caja Negra"), inspeccionémosla en el **Mapa Regulatorio**.

```bash
venturalitica ui
```

Navega a través de las pestañas del **Mapa de Cumplimiento**:

*   **Artículo 9 (Riesgo)**: Ve el control fallido `credit-age-disparate`. Esta es tu evidencia técnica de "Monitoreo de Riesgos".
*   **Artículo 10 (Datos)**: Ve la distribución de datos y verificaciones de calidad.
*   **Artículo 13 (Transparencia)**: Revisa el "Feed de Transparencia" para ver tus dependencias de Python (BOM).

---

## Paso 5: Generar Documentación (Anexo IV) 📝

El paso final es convertir esta evidencia en un documento legal.

1.  En el Panel, ve a la pestaña **"Generación"**.
2.  Selecciona **"Español"**.
3.  Haz clic en **"Generar Anexo IV"**.

Venturalítica redactará un documento técnico que hace referencia a tu ejecución específica:

> *"Como se evidencia en `trace_quickstart_loan.json`, el sistema fue auditado contra **[Política OSCAL: Equidad en Calificación Crediticia]**. Se detectó una desviación en la Disparidad de Edad (0.36), identificando un riesgo potencial de sesgo..."*

### Referencias
*   **Política Usada**: [`loan/risks.oscal.yaml`](https://github.com/venturalitica/venturalitica-sdk-samples/blob/main/policies/loan/risks.oscal.yaml)
*   **Base Legal**:
    *   [Ley de IA de la UE Artículo 9 (Gestión de Riesgos)](https://artificialintelligenceact.eu/es/article/9/)
    *   [Ley de IA de la UE Artículo 11 (Documentación Técnica)](https://artificialintelligenceact.eu/es/article/11/)

## ¿Qué sigue?

- **[Referencia de API](api.md)** - Documentación completa
- **Crea tu propia política** - Copia el YAML anterior y modifica los umbrales
