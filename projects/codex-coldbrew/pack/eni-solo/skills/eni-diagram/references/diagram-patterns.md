# 图表模式库

生成图表源码时优先套用这些紧凑模式，而不是现场发明复杂语法。

## Mermaid 流程图

```mermaid
flowchart TD
  start([Begin]) --> check[Validate token]
  check --> ok{Token valid?}
  ok -- yes --> grant[Issue session]
  ok -- no --> deny[Return 401]
  grant --> end([End])
  deny --> end
```

## Mermaid 泳道式流程图

```mermaid
flowchart LR
  subgraph dev[Developer]
    d1[Push commit]
  end
  subgraph ci[CI Platform]
    c1[Run checks]
    c2[Build image]
  end
  subgraph ops[Operations]
    o1[Approve release]
  end
  d1 --> c1
  c1 -- passed --> c2
  c2 -- failed --> d1
  c2 --> o1
```

## Mermaid 架构图

```mermaid
flowchart LR
  client[Client] --> gw[Gateway]
  gw --> svc[Order Service]
  svc --> cache[(Redis)]
  svc --> db[(Postgres)]
  svc -. emit .-> broker[[Kafka]]
  broker --> consumer[Notification Worker]
```

## Mermaid 时序图

```mermaid
sequenceDiagram
  actor U as User
  participant W as Web
  participant S as Service
  database D as DB
  U->>W: Submit login form
  W->>S: POST /session
  S->>D: Lookup credential hash
  D-->>S: Record found
  S-->>W: 200 with cookie
  W-->>U: Redirect to dashboard
```

## Mermaid ER 图

```mermaid
erDiagram
  AUTHOR ||--o{ BOOK : writes
  BOOK ||--|{ COPY : has
  MEMBER ||--o{ LOAN : makes
  COPY ||--o{ LOAN : lent_as
  AUTHOR {
    string id PK
    string name
  }
  BOOK {
    string isbn PK
    string author_id FK
    date published_at
  }
```

## Mermaid 状态图

```mermaid
stateDiagram-v2
  [*] --> New
  New --> Assigned: assign
  Assigned --> InProgress: start
  InProgress --> InReview: submit
  InReview --> Done: approve
  InReview --> InProgress: request changes
  Done --> [*]
```

## Mermaid 类图

```mermaid
classDiagram
  class Account {
    +string id
    +string email
    +enableMfa()
  }
  class Payment {
    +string id
    +decimal amount
    +capture()
  }
  Account "1" --> "0..*" Payment : owns
```

## Mermaid 甘特图

```mermaid
gantt
  title Release Timeline
  dateFormat  YYYY-MM-DD
  section Planning
  Requirements       :a1, 2026-02-01, 6d
  Architecture       :after a1, 5d
  section Delivery
  Backend            :2026-02-12, 12d
  Frontend           :2026-02-12, 10d
  QA                 :2026-02-24, 6d
```

## Mermaid 思维导图

```mermaid
mindmap
  root((Research Plan))
    Questions
      Problem statement
      Scope
    Sources
      Academic papers
      Industry reports
    Outputs
      Draft
      Review
```

## Mermaid 用户旅程

```mermaid
journey
  title Onboarding Journey
  section Signup
    Visit landing page: 4: User
    Create account: 5: User
  section First use
    Import data: 3: User
    Invite teammate: 4: User
```

## Graphviz 依赖图

```dot
digraph G {
  rankdir=LR;
  node [shape=box, style=rounded];
  web -> gateway;
  gateway -> orders;
  gateway -> billing;
  orders -> cache;
  billing -> db;
  worker -> queue;
  worker -> db;
}
```

## Graphviz 分簇架构

```dot
digraph G {
  rankdir=LR;
  compound=true;
  node [shape=box, style=rounded];

  subgraph cluster_edge {
    label="Edge";
    cdn;
    waf;
  }

  subgraph cluster_app {
    label="Application";
    api;
    worker;
    queue [shape=cylinder];
    db [shape=cylinder];
  }

  cdn -> api;
  waf -> api;
  api -> db;
  api -> queue;
  queue -> worker;
  worker -> db;
}
```

## PlantUML 时序图

```plantuml
@startuml
actor User
participant Web
participant API
database DB
User -> Web: Submit order
Web -> API: POST /orders
API -> DB: Insert row
DB --> API: OK
API --> Web: 201 Created
Web --> User: Order confirmation
@enduml
```

## PlantUML 组件架构

```plantuml
@startuml
actor User
rectangle "Frontend" {
  [Web App]
}
rectangle "Backend" {
  [API Service]
  queue "Queue"
  [Worker]
  database "Database"
}
User --> [Web App]
[Web App] --> [API Service]
[API Service] --> Database
[API Service] --> Queue
Queue --> [Worker]
[Worker] --> Database
@enduml
```

## SVG 兜底

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360" role="img">
  <title>Simple process diagram</title>
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
      <path d="M0,0 L0,6 L9,3 z" />
    </marker>
  </defs>
  <rect x="40" y="120" width="160" height="70" rx="10" fill="white" stroke="black" />
  <text x="120" y="160" text-anchor="middle">Start</text>
  <line x1="200" y1="155" x2="320" y2="155" stroke="black" marker-end="url(#arrow)" />
  <rect x="320" y="120" width="180" height="70" rx="10" fill="white" stroke="black" />
  <text x="410" y="160" text-anchor="middle">Process</text>
</svg>
```
