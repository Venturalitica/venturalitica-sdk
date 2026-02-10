# Cumplimiento en Modo Estricto

## 🛡️ Previniendo Fallas Silenciosas (Artículo 14)

La Ley de IA de la UE (Artículo 14) exige supervisión humana efectiva y medidas técnicas para prevenir riesgos. En un flujo de trabajo de cumplimiento programático, el mayor riesgo es una "falla silenciosa", donde una verificación de cumplimiento se omite debido a una mala configuración (por ejemplo, una columna faltante o una métrica no definida) pero la tubería continúa desplegando el modelo.

Venturalítica impone el **Modo Estricto** para prevenir esto.

## Cómo Funciona

Cuando el Modo Estricto está habilitado:
1.  **Métricas Faltantes**: Si un control hace referencia a una clave de métrica que no está registrada, la validación genera un `ValueError` en lugar de omitirlse.
2.  **Variables No Vinculadas**: Si una política requiere una variable (por ejemplo, `codigo_postal`) que no se puede encontrar en tu DataFrame o mapeo de contexto, la validación genera un `ValueError`.
3.  **Errores de Cálculo**: Cualquier error en tiempo de ejecución durante el cálculo de la métrica (por ejemplo, división por cero) se convierte en una falla dura.

### Detección Automática (CI/CD)

El SDK detecta automáticamente si se está ejecutando en un entorno de Integración Continua.

*   **Si `CI=true`**: El Modo Estricto está **HABILITADO** por defecto.
*   **Si `VENTURALITICA_STRICT=true`**: El Modo Estricto está **HABILITADO**.

Esto significa que puedes desarrollar localmente con verificaciones "laxs" (recibiendo advertencias por configuración faltante), pero tu pipeline de CI (GitHub Actions, GitLab CI, Jenkins) **romperá la compilación** si el cumplimiento no es totalmente riguroso.

## Configuración Manual

Puedes forzar el modo estricto en tu código:

```python
import venturalitica as vl

# Forzar verificación estricta incluso localmente
vl.enforce(
    data=df,
    target="y",
    policy="my_policy.yaml",
    strict=True  # <--- Genera errores en cualquier configuración faltante
)
```

## Mejores Prácticas

1.  **Usa siempre `CI=true` en pipelines de producción.**
2.  **Monitorea tus logs.** En modo laxo (local), busca advertencias `[Skip]`.
3.  **Define todas las métricas.** Asegúrate de que cada clave de métrica en tu política OSCAL tenga una función correspondiente en el `METRIC_REGISTRY`.
