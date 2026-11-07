# Evaluación de Impacto en Protección de Datos (DPIA)

> **Plantilla — debe ser revisada y firmada por el DPO de la empresa antes
> de poner el sistema en producción.** Este documento cumple los requisitos
> mínimos del RGPD art. 35.7. Sustituye los placeholders `[…]`.

---

## Nota previa: alcance de esta DPIA

El tratamiento de datos personales en la versión actual de portIO es
**limitado**. La plataforma ha eliminado las órdenes de trabajo, las firmas
electrónicas de operarios, el registro de incidencias y el audit log de
acciones. Lo que queda son:

1. Datos de usuario (email, nombre, rol) necesarios para autenticarse y
   operar la plataforma.
2. Datos de buques (MMSI, IMO, nombre, posición AIS) — estos son datos de
   **entidades marítimas**, no de personas físicas, y en su mayoría son
   datos públicos difundidos por el propio buque mediante AIS.
3. Datos de escalas, atraques y alertas operacionales — referenciados por
   MMSI/nombre de buque, sin datos personales directos.
4. Acceso mediante API-key para la Autoridad Portuaria — la clave se asigna
   a una organización, no a una persona física.
5. Texto libre de las conversaciones del usuario con el asistente de IA
   (`portIO-ai`) — categoría nueva desde que ese módulo se incorporó a la
   plataforma, no contemplada en versiones anteriores de esta DPIA. El
   usuario puede, en teoría, escribir cualquier cosa en el chat; el sistema
   no lo filtra ni lo modera antes de persistirlo.

Dado el **volumen moderado de datos personales tratados** (identidad de los
usuarios administradores, más el texto libre que ellos mismos introduzcan
en el asistente de IA) y la **ausencia de categorías especiales** (RGPD
art. 9), la necesidad de una DPIA plena conforme al art. 35 es discutible
pero menos clara que antes de incorporar el asistente de IA — el punto 5
introduce un vector de datos personales de contenido no acotado que merece
revisión explícita del DPO. Se mantiene este documento como registro de la
evaluación y para su revisión.

---

## 1. Identificación

- **Responsable del tratamiento:** [Razón social, NIF, dirección].
- **DPO:** [Nombre, correo de contacto, teléfono].
- **Sistema:** *portIO* — Plataforma de operativa portuaria marítima.
- **Versión analizada:** [tag git / commit hash al firmar].
- **Fecha de la evaluación:** [yyyy-mm-dd].
- **Próxima revisión:** anual o tras cualquier cambio sustancial del tratamiento.

---

## 2. Descripción sistemática del tratamiento

### 2.1 Finalidades

1. Gestionar el acceso de usuarios (administradores de empresa portuaria)
   a la plataforma de operativa.
2. Facilitar el seguimiento de buques en tiempo real y el historial de
   posiciones AIS para la gestión de escalas y atraques.
3. Proporcionar datos de historial de posiciones de buques a la Autoridad
   Portuaria a través de la API pública (acceso con API-key por organización).

### 2.2 Categorías de datos tratados

| Categoría | Datos concretos | Origen | ¿Datos de personas físicas? |
|---|---|---|---|
| Identidad de usuario | Nombre, correo corporativo, ID UUID | Alta del usuario por admin | Sí |
| Credenciales | Contraseña BCrypt | Alta del usuario | Sí (hash, no texto claro) |
| Datos de buque | MMSI, IMO, nombre del buque, tipo, tonelaje | AIS / fuentes marítimas públicas | No — son datos del buque como entidad |
| Posición AIS | Latitud, longitud, velocidad, rumbo, estado de navegación | Proveedor AIS | No — datos del buque; radiodifundidos públicamente |
| Escala / atraque | Nombre buque, MMSI, muelle asignado, tiempos ETA/ETD | Operadores de la empresa | No — datos operacionales del buque |
| Conversaciones con el asistente de IA | Texto de las preguntas y respuestas (`ai.conversation`/`ai.message`) | Interacción del usuario con `portIO-ai` | Sí — puede contener texto libre escrito por el usuario |
| Alertas operacionales | Tipo de alerta, muelle, MMSI | Generado por la plataforma | No |

**No se tratan categorías especiales** (RGPD art. 9): salud, biometría,
ideología, etc.

**Los datos de posición AIS son datos públicos**: los buques los emiten
obligatoriamente por radiotelemetría (Convenio SOLAS) y son accesibles a
cualquier receptor AIS. Su tratamiento por portIO no introduce ningún riesgo
adicional de privacidad para personas físicas.

### 2.3 Base legal (RGPD art. 6)

- **6.1.b** — ejecución del contrato de servicio con la empresa portuaria
  (gestión de accesos y operativa).
- **6.1.f** — interés legítimo del responsable en la correcta gestión
  portuaria y el cumplimiento de obligaciones marítimas, ponderado con los
  derechos de los usuarios (escaso impacto: solo administradores de empresa,
  no trabajadores de base).

### 2.4 Categorías de afectados

- Administradores y operadores de empresa portuaria con cuenta en la plataforma.
- (Indirectamente y de forma muy limitada) Personal de la Autoridad Portuaria
  con acceso a la API pública si la API-key está vinculada a una persona física.

### 2.5 Plazos de conservación

| Dato | Plazo | Base |
|---|---|---|
| Datos de usuario activo | Mientras dure la relación contractual con la empresa | Contrato |
| Datos de usuario tras baja | 4 años | Prescripción acciones contractuales |
| Historial AIS (`vessel_history`) | Configurable; por defecto 90 días | Minimización |
| Datos de escala / atraque | Mientras la escala esté activa + 2 años | Obligación operativa portuaria |

---

## 3. Necesidad y proporcionalidad

| Principio (art. 5) | Cumplimiento |
|---|---|
| Licitud, lealtad, transparencia | Información al usuario en el proceso de alta. |
| Limitación de finalidad | Datos solo para las finalidades del §2.1. Sin uso comercial ni perfilado. |
| Minimización | Solo se almacenan los datos de usuario estrictamente necesarios para la autenticación y la operativa. Los datos AIS son datos de buques, no de personas. |
| Exactitud | El usuario admin puede corregir su perfil. |
| Limitación de plazo | Ver §2.5. |
| Integridad y confidencialidad | TLS extremo a extremo, JWT firmado RS256, BCrypt en credenciales, aislamiento por empresa filtrado explícitamente en cada consulta de repositorio (`company_id` del claim JWT, ver ARCHITECTURE.md §6). |
| Responsabilidad proactiva | Esta evaluación + designación de DPO + procedimientos documentados. |

---

## 4. Riesgos para los derechos del interesado

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Acceso indebido a cuenta de usuario por credenciales comprometidas | Baja | **Medio-Alto** | BCrypt + rotación de refresh_token. **Riesgo no mitigado hoy**: el `access_token` tiene una validez de 365 días (deviación deliberada documentada en `portIO-auth`, no 15 minutos) — un token filtrado sigue siendo válido durante un año salvo rotación de la clave de firma o revocación del cliente completo; no hay revocación individual de un token concreto. Pendiente de revisión por el responsable del tratamiento antes de producción con datos reales. |
| Acceso indebido por interno con SUPERUSER Postgres | Baja | Medio | Lista cerrada de admins de BD + 2FA recomendado + logs de acceso al sistema. |
| Filtración por brecha de seguridad | Baja | Medio | Aislamiento Docker, TLS, sin PII innecesaria, datos AIS son públicos. |
| Decisión automatizada con efecto jurídico | Nulo | — | No hay perfilado ni decisión automatizada. |

Riesgo residual valorado **bajo**. La plataforma no trata datos de trabajadores,
no captura geolocalización de personas, no genera registros de comportamiento
individual y no produce firmas electrónicas. El tratamiento se limita a
credenciales de administradores y datos operacionales de buques (no personales).

---

## 5. Derechos del interesado

Procedimiento documentado para ejercer derechos (RGPD art. 15-22) por correo
a `[dpo@empresa.com]`. Plazo de respuesta: 1 mes (prorrogable a 2 en
supuestos del art. 12.3).

| Derecho | Cómo se atiende |
|---|---|
| Acceso | Endpoint `GET /api/users/me` devuelve los datos del usuario autenticado. Export adicional bajo petición al DPO. |
| Rectificación | Edición del perfil por el propio usuario o por un admin. |
| Supresión | Eliminación lógica (`deleted_at`) del registro de usuario. Revisar si existen obligaciones de conservación contractuales. |
| Oposición | Limitada por base 6.1.b/f. Documentado caso por caso. |
| Portabilidad | Export JSON de los datos del usuario bajo petición. |

---

## 6. Consulta previa a la AEPD

**No procede.** El riesgo residual es bajo y el tratamiento de datos
personales es mínimo (solo identidad de administradores de empresa).
No se cumplen los supuestos del art. 35.3 RGPD que obligarían a consulta
previa (evaluación sistemática de personas, datos a gran escala de categorías
especiales, vigilancia sistemática de zona de acceso público).

---

## 7. Firmas

- **DPO:** ______________________ Fecha: __________
- **Responsable del tratamiento:** ______________________ Fecha: __________

---

## Anexo A — Inventario técnico de tratamientos de datos personales

| Componente | Datos personales | Volumen estimado | Cifrado |
|---|---|---|---|
| Postgres `app.app_user` | Nombre, email, rol | ~10–50 filas/empresa | TLS en tránsito + at-rest recomendado |
| `auth.auth_user` | Email, contraseña BCrypt | Igual que app_user | TLS en tránsito + at-rest recomendado |
| `ai.conversation` / `ai.message` | Texto libre de las preguntas del usuario al asistente de IA, propiedad de `(company_id, user_id)` | Variable, sin límite de retención implementado | TLS en tránsito + at-rest recomendado |
| JWT access_token | Sub (user_id), email, company_id, authorities | sessionStorage del navegador (365 días de validez — ver §4) | RS256 firmado |

Los demás componentes (`vessel`, `vessel_live`, `vessel_history`,
`port_call`, `berth_operation`, `operations_alert`) no contienen datos de
personas físicas identificadas o identificables. El módulo de emisiones
MRV (`vessel_emissions`) que mencionaban versiones anteriores de este
documento **se eliminó por completo de la plataforma** y no existe en el
esquema actual.
