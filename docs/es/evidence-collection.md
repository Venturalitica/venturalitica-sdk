# Colección de Evidencia: La Grabadora de Caja Negra

Mientras que las **Políticas** (el Ejecutor) evitan que los modelos malos lleguen a producción, la **Colección de Evidencia** (la Grabadora) asegura que puedas probar exactamente qué sucedió durante el entrenamiento. Esta es tu grabadora de vuelo de "Caja Negra" para la IA.

En Venturalítica, la colección de evidencia es distinta de la aplicación de políticas. Puedes registrar evidencia sin bloquear un despliegue, o aplicar estrictamente sin guardar trazas. Sin embargo, para el pleno cumplimiento de la Ley de IA de la UE (Artículo 12: Mantenimiento de Registros), necesitas ambos.

## Dos Formas de Registrar

### 1. El Envoltorio Automático (`vl.wrap`)

La forma más fácil de recolectar evidencia es envolver tu estimador. Esto se conecta automáticamente a `.fit()` y `.predict()` para capturar entradas, salidas y metadatos.

```python
import venturalitica as vl
from sklearn.ensemble import RandomForestClassifier

# 1. Envolver el modelo
model = vl.wrap(RandomForestClassifier(), policy="my_policy.yaml")

# 2. Entrenar como de costumbre (La evidencia se auto-recolecta)
model.fit(X_train, y_train, audit_data=train_df, gender="sex")
```

**¿Qué se registra?**
*   **Marca de tiempo**: Horas precisas de inicio/fin.
*   **Configuración del Modelo**: Hiperparámetros (`n_estimators`, `max_depth`, etc.).
*   **Forma de Datos**: Número de filas/columnas utilizadas.
*   **Contexto del Código**: El nombre del archivo y el análisis AST del script que llamó a `fit`.

### 2. El Recolector de Trazas (`vl.tracecollector`)

Para bucles de entrenamiento personalizados (ej., PyTorch, TensorFlow) o canalizaciones complejas donde `fit()` no es suficiente, usa el gestor de contexto.

```python
import venturalitica as vl

# Iniciar la sesión de grabación
with vl.tracecollector("custom_training_run"):
    # Tu lógica personalizada aquí
    model = train_custom_model(data)
    evaluate_model(model)
    
# La evidencia se guarda en .venturalitica/trace_custom_training_run.json
```

## ¿A dónde va la evidencia?

Toda la evidencia se asegura localmente en el directorio `.venturalitica/`:

*   **`results.json`**: El resultado de tus auditorías de política (Pasa/Falla).
*   **`trace_{name}.json`**: Los metadatos de ejecución (marcas de tiempo, análisis de código).
*   **`bom.json`**: El inventario de la cadena de suministro de software (dependencias).

## Impacto en el Cumplimiento

Para el **Artículo 12 (Ley de IA de la UE)**, esta evidencia es obligatoria. El Panel de Venturalítica lee estos archivos para probar:

1.  **Trazabilidad**: "Sabemos exactamente qué código y datos produjeron el Modelo v1.0."
2.  **Integridad**: "La evidencia no ha sido manipulada" (vía anclaje SHA-256).

!!! tip "Ver Tus Trazas"
    Después de ejecutar tu script de entrenamiento, lanza el panel (`venturalitica ui`) para visualizar estas trazas en la sección **Artículo 12**.
