# Nivel 1: El Ingeniero (Política y Configuración) 🟢

**Objetivo**: Aprender a implementar **Controles** que mitiguen **Riesgos**.

**Prerrequisito**: [De Cero a Pro (Inicio)](index.md)

---

## 1. El Escenario: Del Riesgo al Control

En un Sistema de Gestión formal (**ISO 42001**), la gobernanza sigue un flujo "top-down":

1.  **Evaluación de Riesgo**: El Oficial de Cumplimiento (CO) identifica un riesgo de negocio (ej. *"Nuestra IA de préstamos podría discriminar a los ancianos, causando daño legal y reputacional"*).
2.  **Definición del Control**: Para mitigar este riesgo, el CO establece un **Control** (ej. *"El Ratio de Disparidad por Edad debe ser siempre > 0.5"*).
3.  **Implementación Técnica**: Ese es tu trabajo. Tomas el requisito del CO y lo conviertes en la "Ley Técnica" (**Artículo 10: Gobernanza de Datos**).

En el inicio rápido [De Cero a Pro](index.md), `vl.quickstart('loan')` FALLÓ:

```text
credit-age-disparate   Age disparity          0.361      > 0.5      ❌ FAIL
```

### ¿Qué pasó?
El **Control** detectó exitosamente una **Brecha de Cumplimiento**. La "Realidad" de los datos (`0.361`) violó el requisito establecido para mitigar el riesgo de "Sesgo de Edad".

> **Regla #1: El Handshake de Responsabilidad**.
> El Oficial de Cumplimiento identifica **Riesgos** y establece **Controles**. 
> El Ingeniero implementa y **Verifica** esos controles usando Evidencia.

Si bajas el umbral a 0.3 solo para que el test "pase", no estás arreglando el código—estás **evadiendo un control de seguridad** y exponiendo a la empresa al riesgo original.

## 2. Anatomía de un Control (OSCAL)

Tu trabajo es traducir el requisito del CO a Código.
Crea un archivo llamado `data_governance.yaml`. Mantén el umbral en **0.5 (El Estándar Organizacional)**.

```yaml
assessment-plan:
  metadata:
    title: "Artículo 10: Estándar de Gobernanza de Datos"
  control-implementations:
    - description: "Monitoreo de Equidad"
      implemented-requirements:
        # 🟢 Control 1: Chequeo de Sesgo
        - control-id: age-check
          description: "La Disparidad por Edad debe ser estándar (> 0.5)"
          props:
            - name: metric_key
              value: disparate_impact        # La métrica de Python
            - name: "input:dimension"
              value: age                    # El concepto abstracto
            - name: operator
              value: gt                     # Mayor que (Greater Than)
            - name: threshold
              value: "0.5"                  # 🔒 NO CAMBIES ESTO
```

## 3. Ejecuta Tu Política

Ahora, ejecutemos la auditoría de nuevo con *tu* configuración. Observa cómo mapeamos el concepto abstracto `age` a tu columna específica.

```python
import venturalitica as vl
from ucimlrepo import fetch_ucirepo

# 1. Obtener Datos (CSV Sucio)
dataset = fetch_ucirepo(id=144)
df = dataset.data.features
df['class'] = dataset.data.targets

# 2. Ejecutar Auditoría (El Mapeo)
results = vl.enforce(
    data=df,
    target="class",
    age="Attribute13",    # 🗝️ MAPEO: 'age' es en realidad 'Attribute13'
    policy="data_governance.yaml"
)

# 3. Verificar Resultados
if all(r.passed for r in results):
    print("✅ Auditoría Aprobada!")
else:
    print("❌ BLOQUEADO: Violación de Cumplimiento detectada.")
    print("👉 Acción: Enviar trace.json al SaaS para revisión del Oficial.")
```

### 🤝 El "Handshake" (La Traducción)

Fíjate en lo que acaba de pasar.

-   **Legal**: "Sé justo (> 0.5)." (Definido en tu YAML)
-   **Dev**: "Esta columna `Attribute13` es `age`." (Definido en tu Python)

Este mapeo es el **Handshake**. Tú construyes el puente entre Datos sucios y Leyes rígidas. Así es como implementas **ISO 42001** sin perder la cabeza en hojas de cálculo.

## 4. Verificación Visual

Cuando ejecutes esto, **FALLARÁ** en tu terminal. Y eso es **BUENO**.
Pero el cumplimiento no son solo logs de terminal.

Para ver el reporte profesional y la visualización de esta falla, ejecuta el dashboard local:

```bash
uv run venturalitica ui
```

Navega a la pestaña de **Política**. Verás la prueba visual de tu riesgo identificado:

![Policy Failure](../assets/academy/policy_status_fail.png)

Has prevenido exitosamente que una IA no conforme llegue a producción midiendo el riesgo contra un estándar verificable.

## 5. Mensajes para Llevar a Casa 🏠

1.  **Política como Código**: La gobernanza es solo un archivo `.yaml`. Define el **Control**.
2.  **El Handshake**: Tú defines el *Mapeo* (`age`=`Attribute13`). El Oficial define el *Requisito* (`> 0.5`).
3.  **El Tratamiento empieza con la Detección**: La falla local es la señal necesaria para iniciar un plan de tratamiento de riesgos formal ISO 42001.

---

**Siguiente Paso**: La build falló localmente. ¿Cómo se lo decimos al Oficial de Cumplimiento?
👉 **[Ir al Nivel 2: El Integrador (MLOps)](level2_integrator.md)**
