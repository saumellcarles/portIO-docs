# Arquitectura — portIO Platform

## 1. Propósito

portIO es una plataforma de **operativa portuaria marítima** con tres áreas
funcionales:

1. **Módulo marítimo** — seguimiento AIS en tiempo real, ficha de buque,
   historial de posiciones segmentado por estado de navegación.
2. **Operaciones portuarias** — consulta de escalas (port calls), atraques
   (berths) y operaciones de atraque sincronizadas desde ICE/PCS, cálculo de
   ETA sobre AIS y alertas de congestión y operaciones.
3. **API pública portuaria** — acceso con API-key al historial de posiciones
   de buques para la Autoridad Portuaria.

Funcionalidades transversales: gestión de empresa, IAM (usuarios/roles),
identidad OAuth2/OIDC, gateway.

4. **Asistente IA (RAG)** — chatbot conversacional (`portIO-ai`) que responde
   preguntas sobre escalas, atraques, alertas y buques vía *tool-calling*
   sobre los servicios de dominio, y sobre el uso de la aplicación vía
   búsqueda semántica (pgvector) en la documentación funcional. Ver
   sección 11.

> **Nota sobre el módulo de operaciones portuarias**: es de **solo
> consulta**. La plataforma no es un sistema de gestión de escalas o
> atraques — no expone creación, edición, asignación de muelle ni borrado
> de una escala, ni manual ni por API. Los datos de escala/atraque (buque,
> ETA, muelle, estado) llegan de los sistemas ICE/PCS del puerto y de AIS; el
> único estado que esta plataforma deriva por sí misma es la transición
> automática `SCHEDULED → ARRIVING` (`VesselArrivalDetector`, por proximidad
> AIS) y el recálculo de ETA. Esta decisión de producto es deliberada: el
> valor de portIO está en la capa de visibilidad, previsión y asistente de
> IA sobre esos datos, no en duplicar la gestión operativa que ya hace el
> ICE/PCS del puerto.

> **Nota sobre el módulo de emisiones MRV**: existió en una fase anterior de
> la plataforma (cálculo Tier 3 EMEP/EEA) pero **se eliminó por completo**
> del backend (`portIO-backend`, migración `V5__drop_emissions.sql`: tabla
> `vessel_emissions` y columnas de motor/MRV en `vessel`, borradas). No
> forma parte del producto actual — cualquier referencia a emisiones en
> código, documentación o en el sitio de marketing (`portIO-web`) que no
> haya sido limpiada es un resto a corregir, no una funcionalidad viva.

---

## 2. Topología de alto nivel

```
                        ┌───────────────┐      ┌─────────────────┐
                        │   Browser     │      │  Browser         │
                        │  app (Next.js)│      │  marketing       │
                        │ portIO-frontend      │  (portIO-web)    │
                        └───┬───────┬───┘      │  sin backend     │
                            │       │          └─────────────────┘
          Auth Code + PKCE  │       │  Authorization: Bearer <JWT>
         (directo al auth)  │       │  (vía gateway)
                            ▼       ▼
                  ┌─────────────┐   ┌────────────────────────┐
                  │ Auth Server │   │  API Gateway            │
                  │ Spring Auth │   │ Spring Cloud Gateway    │
                  │   :9000     │   │  :8080 (único público)  │
                  │             │   │  - JWT verify           │
                  │  /oauth2/*  │   │  - CORS, rate limit     │
                  │  /connect/* │   │  - routing + WS proxy   │
                  └──────┬──────┘   └───┬─────────────┬──────┘
                         │ JWKS         │ /api/**      │ /api/v1/ai/**
                         │◄─────────────┤ /ws          │ (match antes
                         │              ▼              │  que /api/**)
                         │      ┌──────────────┐        ▼
                         │      │   Backend    │   ┌──────────────┐
                         │      │ Spring Boot  │   │  portIO-ai   │
                         │      │    :8081     │   │ FastAPI      │
                         │      │ dominio+WS   │   │    :8083     │
                         │      └──────┬───────┘   └──────┬───────┘
                         │             │ lectura app.*     │
                         └─────┬───────┴───────────────────┘
                               ▼
                       ┌──────────────┐
                       │  PostgreSQL  │
                       │ + PostGIS +  │
                       │   pgvector   │
                       │    :5432     │
                       └──────────────┘
```

---

## 3. Flujo de autenticación (SPA directa, Auth Code + PKCE)

`portIO-frontend` se comunica **directamente** con el servidor de
autorización para autenticarse. No hay BFF ni almacenamiento de tokens en
servidor Next.js. La SPA almacena los tokens y los envía como `Bearer` en
cada llamada a la API. El gateway es un proxy inverso de validación JWT
pura para `/api/**`; el auth server es el único otro servicio expuesto
directamente al navegador.

```
Browser (Next.js SPA)              Auth Server (:9000)       Gateway (:8080)      Backend (:8081)
         │                                  │                      │                     │
         │ 1. Usuario sin token             │                      │                     │
         │    genera code_verifier +        │                      │                     │
         │    code_challenge (S256)         │                      │                     │
         │                                  │                      │                     │
         │ 2. window.location =             │                      │                     │
         │    /oauth2/authorize?...         │                      │                     │
         │─────────────────────────────────►│                      │                     │
         │                                  │                      │                     │
         │         3. Usuario se autentica (formulario en auth server)                   │
         │◄─────────────────────────────────│                      │                     │
         │                                  │                      │                     │
         │ 4. 302 redirect a /auth/callback │                      │                     │
         │◄─────────────────────────────────│                      │                     │
         │                                  │                      │                     │
         │ 5. POST /oauth2/token            │                      │                     │
         │    grant_type=authorization_code │                      │                     │
         │─────────────────────────────────►│                      │                     │
         │                                  │                      │                     │
         │ 6. 200 { access_token, id_token, refresh_token }        │                     │
         │◄─────────────────────────────────│                      │                     │
         │                                  │                      │                     │
         │ 7. GET /api/vessels              │                      │                     │
         │    Authorization: Bearer <token> │                      │                     │
         │─────────────────────────────────────────────────────────►│                     │
         │                                  │  8. JWKS lookup      │                     │
         │                                  │◄─────────────────────│                     │
         │                                  │ signing keys         │                     │
         │                                  │─────────────────────►│                     │
         │                                  │                      │ 9. Verify RS256     │
         │                                  │                      │    exp/iss/aud      │
         │                                  │                      │                     │
         │                                  │                      │ 10. Forward Bearer  │
         │                                  │                      │────────────────────►│
         │                                  │                      │    11. Verify JWT   │
         │                                  │                      │        de nuevo,    │
         │                                  │                      │        independiente│
         │                                  │                      │        (mismo JWKS).│
         │                                  │                      │        Extrae       │
         │                                  │                      │        company_id,  │
         │                                  │                      │        roles, sub.  │
         │                                  │                      │      12. 200 {...}  │
         │◄─────────────────────────────────────────────────────────◄────────────────────│
```

### Registro OAuth2 del cliente (en el auth server)

Datos reales del único cliente sembrado por `AuthorizationServerConfig`
(`CommandLineRunner`, idempotente en cada arranque):

```
client_id:              prl-webapp
client_authentication:  NONE        ← cliente público, PKCE obligatorio
grant_types:            authorization_code, refresh_token
redirect_uri:           ${AUTH_CLIENT_PRL_WEBAPP_ORIGIN}/auth/callback
post_logout_redirect_uri: ${AUTH_CLIENT_PRL_WEBAPP_ORIGIN}/
scopes:                 openid, profile, workorder.read, workorder.write,
                         incident.read, incident.write, admin
                         (los scopes workorder.*/incident.* son un resto
                         del modelo de dominio anterior - el código actual
                         no los comprueba en ningún endpoint)
require_proof_key:      true        ← PKCE requerido
access_token_ttl:       365 días    ← deliberado, ver nota de riesgo abajo
refresh_token_ttl:      365 días
reuse_refresh_tokens:   false       ← rotación
```

> **TTL de 365 días — deviación deliberada y documentada en el propio
> código** (`AuthorizationServerConfig.TokenSettings`), muy por encima de
> la práctica recomendada (minutos-horas). Un token filtrado es válido
> durante un año; revocarlo antes de su expiración requiere rotar la clave
> de firma o revocar el cliente — no hay revocación individual de tokens
> ya emitidos sin esos dos mecanismos.

### Almacenamiento de tokens en el navegador

- `access_token` + `refresh_token` + `idToken` → store Zustand con
  middleware `persist`, respaldado en **`sessionStorage`** (no
  `localStorage`: la sesión no sobrevive indefinidamente entre
  pestañas/ventanas y queda menos expuesta a XSS persistente).
- El refresco es **reactivo**, no por temporizador: un interceptor de
  respuesta de axios detecta un `401`, llama a `/oauth2/token` con
  `grant_type=refresh_token` una sola vez (promesa compartida para no
  disparar refrescos en paralelo) y reintenta la petición original.
- **Logout**: `GET /connect/logout` (OIDC **RP-Initiated Logout** de
  Spring Authorization Server, activado vía `.oidc(Customizer.withDefaults())`
  en el `@Order(1)` chain), con `id_token_hint` + `post_logout_redirect_uri`
  — **no** `/oauth2/revoke`. Mata la cookie de sesión SSO del auth server;
  sin eso, cualquier visita posterior a `/` reautenticaría en silencio al
  usuario mientras la sesión SSO siga viva.

---

## 4. Contextos acotados (Bounded Contexts)

Backend: **monolito modular** (una sola aplicación Spring Boot, una BD),
con DDD bounded contexts como paquetes Java bajo `com.portio.backend`.

| Contexto     | Responsabilidad                                                        |
|--------------|------------------------------------------------------------------------|
| `shared`     | Primitivas compartidas: `CompanyContext`, seguridad, manejo de errores |
| `company`    | Agregado Company, alta de empresa                                      |
| `iam`        | Agregado User, alta de usuarios (espeja identidades del auth server)   |
| `maritime`   | Tracking AIS, ficha de buque, historial de posiciones                  |
| `operations` | Escalas (port calls), atraques (berths), operaciones, alertas          |
| `apikey`     | Claves de integración por empresa (`pk_live_...`), validadas por el *gateway* |

`company` e `iam` siguen hexagonal estricto (`domain`/`port`/`infrastructure`)
porque son los contextos más estables. `maritime` y `operations` usan
`application`/`infrastructure` sin interfaz de puerto explícita entre
ambos — la complejidad real está en la orquestación temporal
(*schedulers*, WebSocket, cálculo), no en intercambiar implementaciones de
persistencia.

No existen módulos `workorder`, `template`, `incident`, `pdf`, `geo`,
`audit`, `outbox`, `notification` ni `emisiones`/`emissions` — han sido
eliminados de la plataforma en fases anteriores.

---

## 5. Capas hexagonales (por contexto)

```
portIO-backend/src/main/java/com/portio/backend/
└── <contexto>/
    ├── domain/              ← Java puro, sin framework (solo company/iam)
    │   ├── model/           ← agregados, entidades, value objects
    │   └── port/
    │       └── out/         ← interfaces de repositorio/adaptador (driven)
    ├── application/         ← casos de uso, @Service
    └── infrastructure/
        ├── persistence/     ← entidades JPA, repos Spring Data, adaptadores
        ├── rest/            ← @RestController, DTOs
        └── (config/, vesselapi/, etc. según contexto)
```

### Reglas de dependencia

- `domain` (donde existe, `company`/`iam`) **nunca** importa Spring, Jakarta
  ni JPA.
- Los DTOs REST viven en `infrastructure.rest`, nunca se filtran al dominio.
- Las entidades JPA (`@Entity`) viven en `infrastructure.persistence`, no
  son modelos de dominio.
- `ChatController`/`UserController`/etc. dependen solo de su servicio de
  aplicación, nunca saltan directamente a un repositorio.

---

## 6. Aislamiento de empresa (multi-empresa, BD única)

**Problema**: una BD Postgres, múltiples empresas, aislamiento de datos
estricto.

**Solución real implementada** (no Hibernate `@Filter` — se consideró en
una fase de diseño anterior pero **no se implementó**; el aislamiento es
explícito en código, no declarativo):

1. **Claim JWT `company_id`**: cada access token lleva el `company_id` del
   usuario, emitido por el auth server al autenticarse.
2. **`CompanyContext`**: bean *request-scoped*, poblado por
   `CompanyContextFilter` a partir del JWT en `portIO-backend`; `portIO-ai`
   (Python) aplica el mismo patrón con un contexto por petición que rellena su
   middleware de seguridad a partir del mismo JWT. El *gateway*
   nunca inyecta cabeceras de identidad; cada servicio deriva la suya del
   mismo JWT de forma independiente.
3. **Filtrado explícito por repositorio**: cada consulta sensible exige
   `company_id` como parte de la firma del método de repositorio
   (`findByIdAndCompanyId(...)`, nunca `findById(...)` a secas) — para que
   sea estructuralmente imposible olvidarlo en un nuevo endpoint.
4. **Verificación en servicio**: `ConversationService` (portIO-ai) y los
   servicios de `operations` repiten la comprobación de propiedad antes de
   leer/escribir, no confían solo en la query.
5. **En `portIO-ai`**, una capa adicional: las *tools* (las herramientas que
   el modelo puede invocar) reciben el `companyId` por la configuración de
   ejecución del agente (`RunnableConfig` de LangGraph), rellenada por el
   servidor — nunca por un argumento que el
   modelo o el usuario puedan influir. Si una herramienta se invoca sin ese
   contexto, falla explícitamente en vez de devolver datos sin filtrar.

No existe un test de integración `CompanyIsolationIT` dedicado en el
repositorio actual; la única cobertura automatizada de aislamiento son los
tests específicos de cada servicio (p. ej. en `portIO-ai`, los tests de
integración de conversaciones y de *tools* contra un Postgres real).

---

## 7. Modelo de seguridad

### Roles

El único valor real de `Role` en el backend (`iam.domain.model.Role`) es
`ADMIN`. Varios endpoints (`@PreAuthorize`) aceptan también
`hasAnyRole('ADMIN', 'COMPANY_ADMIN')` como preparación para un segundo rol
operativo que **hoy no se emite** — `portIO-auth` solo emite
`ROLE_ADMIN` en el claim `authorities`. No hay un `ROLE_PLATFORM_ADMIN`
real en el sistema actual.

Los roles llegan al JWT como `authorities` (array de strings), generados
en `portIO-auth` desde la columna `auth.auth_user.authorities` (CSV). Cada
servicio los mapea con su propio `JwtAuthConverter`
(`ROLE_`-prefixed `SimpleGrantedAuthority`).

---

## 8. Stack tecnológico

| Capa       | Tecnología                                                                |
|------------|-----------------------------------------------------------------------------|
| Backend    | Java 21, Spring Boot 3.3.5, Spring Security, JPA/Hibernate, Flyway, Lombok, MapStruct (en classpath, mappers escritos a mano) |
| Auth       | Spring Authorization Server (gestionado por Boot 3.3.5)                    |
| Gateway    | Spring Cloud Gateway 2023.0.3, reactivo (WebFlux)                           |
| IA         | Python 3.12, FastAPI + Pydantic v2, LangChain + LangGraph (agente con *tool-calling*), SQLAlchemy 2 async + Alembic, pgvector. Solo Ollama está cableado hoy (`ChatOllama`/`OllamaEmbeddings`; cambiar de proveedor es cambiar esas dos clases, no hay selección por variable de entorno). Hasta noviembre de 2026 era Spring Boot + Spring AI, con el mismo contrato HTTP |
| BD         | PostgreSQL + PostGIS + pgvector, una sola instancia, esquemas `app`/`auth`/`ai` |
| App        | Next.js 14 (App Router), TypeScript, Tailwind, Radix UI, Framer Motion, MapLibre GL, Zustand, Axios, React Hook Form + Zod. **Sin React Query** (retirado deliberadamente, ver `portIO-frontend`) |
| Web        | Next.js 14 (App Router), TypeScript, Tailwind, Framer Motion, Radix UI — sitio de marketing estático, sin backend propio |
| Tests      | JUnit 5, Testcontainers (Postgres real, no mocks), AssertJ, MockMvc         |
| Build      | Maven (backend / auth / gateway / ai), pnpm (frontend), npm (web)          |

---

## 9. Límites de módulos y comunicación

- **BD única**. Todos los servicios backend comparten la misma instancia
  Postgres, separados por esquema: `app` (backend), `auth` (auth server),
  `ai` (portIO-ai).
- No hay llamadas HTTP entre servicios backend en *runtime* — cada uno
  valida el JWT de forma independiente contra el mismo JWKS del auth
  server (offline, cacheado). `portIO-ai` sí lee (solo lectura, nunca
  escritura) tablas de `app.*` con consultas SQLAlchemy en transacciones
  `READ ONLY`.
- El *gateway* es el único punto de entrada público para `/api/**` y
  `/ws/**`. El auth server también está expuesto públicamente (el
  navegador debe redirigir a él para `/oauth2/authorize` y `/oauth2/token`,
  además de `/connect/logout`), pero solo sus endpoints OAuth2/OIDC y la
  página de login. `portIO-backend` y `portIO-ai` **nunca** son accesibles
  desde el exterior directamente.
- `/api/public/**` (histórico de buques) es la única superficie que el
  *gateway*/backend sirven sin autenticación JWT — pensada para la
  Autoridad Portuaria u otros consumidores externos de confianza. La
  clave de API de integración (`/api/integrations/api-key`) se emite por
  empresa pero **hoy no hay ningún filtro en el gateway que la valide** —
  gap de seguridad conocido, no una decisión de diseño.

---

## 10. Layout del repositorio (monorepo lógico, repos físicos separados)

```
portIO-platform/
├── portIO-backend/       Maven, servicio de dominio Spring Boot (puerto 8081)
├── portIO-auth/          Maven, Spring Authorization Server (puerto 9000)
├── portIO-gateway/       Maven, Spring Cloud Gateway (puerto 8080, único público)
├── portIO-ai/             Python (uv), asistente IA FastAPI + LangGraph (puerto 8083) - ver sección 11
├── portIO-frontend/      Next.js 14, aplicación real (puerto 3000)
├── portIO-web/           Next.js 14, sitio de marketing (sin backend propio)
├── portIO-infra/
│   └── docker-compose.yml   stack completo para desarrollo local
└── portIO-docs/
    ├── funcional/         PANTALLAS.md - documentación de cada pantalla
    ├── tecnica/           ARCHITECTURE.md (este archivo), CONTRACTS.md, DPIA.md
    ├── presentacion/      presentación comercial (PDF + script de generación)
    └── screenshots/       capturas reales usadas por funcional/PANTALLAS.md
```

Cada servicio tiene su propio repositorio Git independiente (no es un
monorepo con un único historial) y su propio `README.md` con el detalle
funcional y técnico completo de ese servicio — este documento cubre solo
lo que cruza fronteras de servicio.

## 11. Asistente IA (portIO-ai)

Microservicio independiente, mismo patrón de despliegue que `backend`
(nunca expuesto a Internet, solo alcanzable vía *gateway*).

```
portIO-frontend → Gateway (Path=/api/v1/ai/**, declarada antes de /api/**)
                → portIO-ai :8083 → { Postgres (schema ai, pgvector) + app.* read-only
                                     , Ollama (servicio ollama del compose) }
```

- **Identidad**: el mismo patrón que `backend` — valida el JWT de forma
  independiente contra el mismo JWKS del auth server y deja `company_id` y
  `sub` en un contexto por petición (en Python, `security/`). El *gateway* no
  añade *headers* de identidad; nunca lo hizo para `backend` tampoco.
- **Datos estructurados**: el modelo nunca ejecuta SQL. Responde preguntas
  sobre escalas/atraques/alertas/buques vía *tool-calling* (agente
  LangGraph: modelo ↔ 5 *tools* de solo lectura, como máximo 10 llamadas al
  modelo por turno) con consultas SQLAlchemy en transacciones `READ ONLY`
  sobre las tablas de `app` que ya posee `backend`. El `companyId` llega al
  *tool* por la configuración de ejecución del agente (`RunnableConfig`),
  nunca como argumento que el modelo pueda rellenar.
- **Documentación funcional**: indexada con pgvector (esquema propio `ai`,
  tabla `ai.document_chunk`) para RAG sobre "cómo se usa la aplicación" —
  ingesta idempotente (hash de contenido en `ai.ingested_source`), solo
  re-embebe cuando el contenido cambia.
- **Conversaciones**: persistidas en `ai.conversation` / `ai.message`,
  propiedad de `(company_id, user_id)`; un intento de leer la conversación
  de otro usuario u otra empresa es un `404`, nunca un `403`.
- **Resumen ejecutivo diario**: los datos se calculan primero (mismas
  herramientas que el chat) y **después** un único modelo convierte ese
  bloque fijo en narrativa — la cifra nunca puede divergir del texto
  porque ambas vienen de los mismos datos.
- Detalle completo (endpoints, variables de entorno, decisiones de diseño)
  en el propio `portIO-ai/README.md` y en [CONTRACTS.md](CONTRACTS.md)
  sección 7.
