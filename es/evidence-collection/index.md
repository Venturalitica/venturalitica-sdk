# Recopilación de Evidencia: La Caja Negra

Mientras que las **Políticas** (el Ejecutor) detienen modelos defectuosos antes de llegar a producción, la **Recopilación de Evidencia** (el Registrador) asegura que puedas probar exactamente qué sucedió durante el entrenamiento. Esta es tu "Caja Negra" de vuelo para la IA.

En Venturalítica, la recopilación de evidencia es distinta de la aplicación de políticas. Puedes registrar evidencia sin bloquear un despliegue, o aplicar estrictamente sin guardar trazas. Sin embargo, para el cumplimiento total de la Ley de IA de la UE (Artículo 12: Mantenimiento de Registros), necesitas ambos.

## Dos Formas de Registrar

### 1. El Envoltorio Automático (`vl.wrap`)

La forma más fácil de recopilar evidencia es envolver tu estimador. Esto se conecta automáticamente a `.fit()` y `.predict()` para capturar entradas, salidas y metadatos.

```
import venturalitica as vl
from sklearn.ensemble import RandomForestClassifier

# 1. Envolver el modelo
model = vl.wrap(RandomForestClassifier(), policy="model_policy.yaml")

# 2. Entrenar como siempre (La evidencia se recolecta automáticamente)
model.fit(X_train, y_train, audit_data=train_df, gender="Attribute9")
```

**¿Qué se registra?** * **Marca de tiempo**: Tiempos precisos de inicio/fin. * **Configuración del Modelo**: Hiperparámetros (`n_estimators`, `max_depth`, etc.). * **Forma de Datos**: Número de filas/columnas usadas. * **Contexto de Código**: El nombre del archivo y análisis AST del script que llamó a `fit`.

### 2. El Monitor Multimodal (`vl.monitor`)

Para bucles de entrenamiento personalizados (ej. PyTorch, TensorFlow) o pipelines complejos donde `fit()` no es suficiente, usa el gestor de contexto.

```
import venturalitica as vl

# Iniciar la sesión de grabación
with vl.monitor("training_run_v1"):
    # Tu lógica personalizada aquí
    model = train_custom_model(data)
    evaluate_model(model)

# La evidencia se guarda en .venturalitica/trace_training_run_v1.json
```

## ¿A dónde va la evidencia?

Toda la evidencia se asegura localmente en el directorio `.venturalitica/`:

- **`results.json`**: El resultado de tus auditorías de política (Pasa/Falla).
- **`trace_{name}.json`**: Los metadatos de ejecución (marcas de tiempo, análisis de código).
- **`bom.json`**: El inventario de la cadena de suministro de software (dependencias).

## Impacto en el Cumplimiento

Para el **Artículo 12 (Ley de IA de la UE)**, esta evidencia es obligatoria. El Panel de Venturalítica lee estos archivos para probar:

1. **Trazabilidad**: "Sabemos exactamente qué código y datos produjeron el Modelo v1.0."
1. **Integridad**: "La evidencia no ha sido manipulada" (mediante anclaje SHA-256).

Ver tus Trazas

Después de ejecutar tu script de entrenamiento, lanza el panel (`venturalitica ui`) para visualizar estas trazas en la sección del **Artículo 12**.
