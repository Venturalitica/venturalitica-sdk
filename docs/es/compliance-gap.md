# La Brecha de Cumplimiento (Hoja de Ruta)

Venturalítica v0.3 proporciona la base para una **IA de Caja de Cristal**, pero los sistemas de alto riesgo (Ley de IA de la UE) requieren una mejora continua. Este documento identifica las brechas técnicas actuales y las características requeridas para convertir la "Evidencia Técnica" en "Certeza Legal".

---

## 🛠 Características Faltantes y Brechas Abiertas

### 1. Endurecimiento de Evidencia (Artículo 12)
*   **Estado Actual**: Hashing SHA-256 de archivos de evidencia.
*   **La Brecha**: Sin **Firma Digital** nativa.
*   **Requisito**: Implementación de firma GPG/X.509 para archivos `trace.json` para asegurar el no repudio en auditorías legales.

### 2. Gobernanza de Datos Profunda (Artículo 10)
*   **Estado Actual**: Equilibrio de clases básico y verificaciones de valores faltantes.
*   **La Brecha**: Falta de **Linaje de Datos** y **Procedencia de Anotaciones**.
*   **Requisito**: Herramientas para registrar la fuente de las etiquetas, métricas de acuerdo entre anotadores y detección de "envenenamiento" para conjuntos de entrenamiento.

### 3. Verificaciones Interactivas de Supervisión Humana (Artículo 14)
*   **Estado Actual**: Verificación estática de elementos interactivos (análisis AST).
*   **La Brecha**: Sin verificación en tiempo de ejecución de acciones "Humano-en-el-bucle" (HITL).
*   **Requisito**: Un envoltorio `vl.oversight()` para registrar cuando un humano realmente aprueba/rechaza una predicción de alto riesgo.

### 4. Robustez Adversarial (Artículo 15)
*   **Estado Actual**: Métricas de rendimiento (Precisión/F1).
*   **La Brecha**: Sin **Escáneres de Ataques** nativos.
*   **Requisito**: Integración con bibliotecas de robustez (ej., ART, CleverHans) para automatizar pruebas adversariales como parte de la canalización `enforce()`.

### 5. Mitigación Automatizada de Sesgos
*   **Estado Actual**: Solo detección.
*   **La Brecha**: Fricción en la corrección del sesgo detectado.
*   **Requisito**: Integración con Fairlearn/AIF360 para "mitigaciones sugeridas" directamente en el Panel.

---

## 🚀 Proponer una Característica

Estamos construyendo el futuro de la IA Responsable. Si tienes un requisito específico para cumplir un mandato de cumplimiento, queremos escucharte.

1.  **Abre un [Issue en GitHub](https://github.com/venturalitica/venturalitica-sdk/issues/new)**.
2.  Etiquétalo como `feature-request` + `compliance-gap`.
3.  Describe el **Artículo Legal** (ej., Art 13) o **Dolor Técnico** que estás abordando.

[Ver Discusiones de la Hoja de Ruta](https://github.com/venturalitica/venturalitica-sdk/discussions)
