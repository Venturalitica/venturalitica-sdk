# La Brecha de Cumplimiento (Hoja de Ruta)

Venturalítica **v0.4** proporciona la base para la **IA de Caja de Cristal**, pero los sistemas de alto riesgo (Ley de IA de la UE) requieren una mejora continua. Este documento identifica las brechas técnicas actuales y las características requeridas para convertir la "Evidencia Técnica" en "Certeza Legal".

---

## ✅ Brechas Recientemente Cerradas (v0.4)

La "Auditoría Estratégica Profunda" y el lanzamiento de la **Academy** han cerrado las siguientes brechas críticas:

### 1. Documentación Técnica (Artículo 11)
*   **Brecha Anterior**: Redacción manual de archivos técnicos.
*   **Solución**: El **Generador del Anexo IV** (Mistral & **ALIA** IA Soberana) ahora automatiza la redacción de documentos regulatorios.

### 2. Transparencia y Confianza (Artículo 13)
*   **Brecha Anterior**: Sin prueba de cumplimiento de cara al público.
*   **Solución**: **El Sello Digital**. En lugar de una insignia SVG estática, Venturalítica ahora aplica un hash a la Evidencia de Traza (SHA-256) para crear una firma criptográfica a prueba de manipulaciones.

### 3. Eficiencia de Recursos (Artículo 15)
*   **Brecha Anterior**: Sin seguimiento del uso de energía o hardware.
*   **Solución**: `vl.monitor()` ahora registra automáticamente las emisiones de CO2 y el consumo de GPU/RAM.

---

## 🛠 Características Faltantes y Brechas Abiertas

### 1. Endurecimiento de Evidencia (Artículo 12)
*   **Estado Actual**: Hashing SHA-256 de archivos de evidencia (El "Sello Digital").
*   **La Brecha**: Sin **Firma Digital** nativa (No repudio).
*   **Requisito**: Implementación de firma GPG/X.509 para archivos `trace.json` para asegurar que no puedan ser falsificados ni siquiera por el propietario del sistema.

### 2. Gobernanza de Datos Profunda (Artículo 10)
*   **Estado Actual**: Balance de clases básico y verificaciones de valores faltantes.
*   **La Brecha**: Falta de **Linaje de Datos** y **Procedencia de Anotaciones**.
*   **Requisito**: Herramientas para registrar la fuente de las etiquetas, métricas de acuerdo entre anotadores y detección de "envenenamiento" para conjuntos de entrenamiento.

### 3. Verificaciones Interactivas de Supervisión Humana (Artículo 14)
*   **Estado Actual**: Verificación estática para elementos interactivos (análisis AST).
*   **La Brecha**: Sin verificación en tiempo de ejecución de acciones "Humano-en-la-bucle" (HITL).
*   **Requisito**: Un envoltorio `vl.oversight()` para registrar *cuándo* un humano realmente aprueba/rechaza una predicción de alto riesgo en producción.

### 4. Robustez Adversarial (Artículo 15)
*   **Estado Actual**: Seguimiento de Eficiencia y Precisión (`vl.monitor`).
*   **La Brecha**: Sin **Escáneres de Ataques** nativos para seguridad.
*   **Requisito**: Integración con bibliotecas de robustez (ej. ART, CleverHans) para automatizar pruebas adversariales como parte del pipeline `enforce()`.

### 5. Mitigación de Sesgo Automatizada
*   **Estado Actual**: Solo detección.
*   **La Brecha**: Fricción al corregir el sesgo detectado.
*   **Requisito**: Integración con Fairlearn/AIF360 para "mitigaciones sugeridas" directamente en el Panel de Control.

---

## 🚀 Propón una Característica

Estamos construyendo el futuro de la IA Responsable. Si tienes un requisito específico para cumplir un mandato de cumplimiento, queremos escucharte.

1.  **Abre un [GitHub Issue](https://github.com/venturalitica/venturalitica-sdk/issues/new)**.
2.  Etiquétalo como `feature-request` + `compliance-gap`.
3.  Describe el **Artículo Legal** (ej. Art 13) o **Dolor Técnico** que estás abordando.

[Ver Discusiones de Hoja de Ruta](https://github.com/venturalitica/venturalitica-sdk/discussions)
