# El Panel de Cumplimiento: Una Caja de Cristal para la IA

El **Panel de Cumplimiento de Venturalítica** es tu centro de control local para la Gobernanza de IA. A diferencia de las herramientas de cumplimiento de "Caja Negra" que operan a puerta cerrada, Venturalítica proporciona una experiencia de **Caja de Cristal**: expone la evidencia técnica exacta que tu sistema está produciendo y la mapea directamente a las obligaciones regulatorias.

El panel hace concreto lo abstracto. Toma los artefactos invisibles de tu canalización de ML—métricas, registros, dependencias—y los convierte en una **Matriz de Trazabilidad Regulatoria**.

## El Mapa Regulatorio Secuencial (Artículos 9-15)

La característica central del panel es el estricto mapeo secuencial de los requisitos de la **Ley de IA de la UE** para Sistemas de IA de Alto Riesgo (Capítulo III, Sección 2). Esta "Caminata de Cumplimiento" te guía a través del ciclo de vida de un sistema conforme.

### El Flujo de Trazabilidad

# Note: adjusted path

#### 1. [Artículo 9: Sistema de Gestión de Riesgos](https://artificialintelligenceact.eu/es/article/9/)

- **La Ley**: Debes identificar y mitigar riesgos para la salud, seguridad y derechos fundamentales.
- **El Código**: Venturalítica mapea tus **Auditorías de Equidad** aquí. Si ejecutas una verificación de sesgo (ej. `gender-bias`), el resultado es la evidencia técnica de que estás monitoreando riesgos de Derechos Fundamentales.
- **Estado**:
  - `Mitigación Verificada`: Tus pruebas de equidad pasaron.
  - `Riesgo Materializado`: Una prueba falló (ej. Impacto Dispar detectado).

#### 2. [Artículo 10: Gobernanza de Datos](https://artificialintelligenceact.eu/es/article/10/)

- **La Ley**: Los datos de entrenamiento, validación y prueba deben ser relevantes, representativos y libres de errores.
- **El Código**: Mapea a tus **Verificaciones de Calidad de Datos** (ej. desequilibrio de clases, valores faltantes) y uso de bibliotecas de datos (`pandas`, `numpy`).
- **Estado**: Marca si la validación de datos fue omitida o falló.

#### 3. [Artículo 11: Documentación Técnica](https://artificialintelligenceact.eu/es/article/11/)

- **La Ley**: Debes mantener documentación técnica actualizada demostrando conformidad.
- **El Código**: Verifica la presencia de tu **Lista de Materiales de Software (SBOM)** (generada por `venturalitica scan`) y el **Borrador de Archivo Técnico** (generado por `venturalitica doc`).
- **Estado**: Verde si existen artefactos; Amarillo/Rojo si falta documentación.

# Note: adjusted path

#### 4. [Artículo 12: Mantenimiento de Registros](https://artificialintelligenceact.eu/es/article/12/)

- **La Ley**: Registro automático de eventos durante la vida del sistema para asegurar trazabilidad.
- **El Código**: Verifica dos componentes críticos:
  - **Anclaje Criptográfico**: Muestra el hash SHA-256 de tu evidencia, probando la integridad de los datos.
  - **Trazas de Ejecución**: Confirma que los metadatos de tiempo de ejecución (`runtime_meta`) fueron capturados durante el entrenamiento/inferencia.

#### 5. [Artículo 13: Transparencia e Información](https://artificialintelligenceact.eu/es/article/13/)

- **La Ley**: El sistema debe ser suficientemente transparente para permitir a los usuarios interpretar los resultados.
- **El Código**: Verifica la **Opacidad del Código**. ¿Es accesible el código fuente para auditoría? ¿Se proporcionan instrucciones?

#### 6. [Artículo 14: Supervisión Humana](https://artificialintelligenceact.eu/es/article/14/)

- **La Ley**: El sistema debe estar diseñado para ser supervisado por personas naturales (humano en el bucle).
- **El Código**: Escanea en busca de lógica de "Botón de Parada" o interfaces interactivas (ej. aplicaciones Streamlit, notebooks Jupyter) que impliquen capacidad de control humano.

#### 7. [Artículo 15: Precisión, Robustez y Ciberseguridad](https://artificialintelligenceact.eu/es/article/15/)

- **La Ley**: El sistema debe ser resistente a errores y ataques.
- **El Código**:
  - **Precisión**: Mapea a tus **Métricas de Rendimiento** (Accuracy, F1, Recall).
  - **Ciberseguridad**: Verifica **Vulnerabilidades de Cadena de Suministro** (CVEs) en tus dependencias a través del escaneo SBOM.

## Por Qué Importa Esto

Este diseño secuencial transforma el cumplimiento de una lista de verificación caótica en un **flujo de trabajo de ingeniería lógico**:

1. **Evaluar Riesgo** (Art 9)
1. **Limpiar Datos** (Art 10)
1. **Documentarlo** (Art 11)
1. **Registrarlo** (Art 12)
1. **Explicarlo** (Art 13)
1. **Controlarlo** (Art 14)
1. **Asegurarlo** (Art 15)

Al seguir este flujo, estás alineando estructuralmente tu sistema de IA con la ley, línea por línea.
