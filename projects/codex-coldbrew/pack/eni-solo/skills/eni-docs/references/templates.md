# 通用文档模板

## 目录

- [项目 README](#项目-readme)
- [API 端点文档](#api-端点文档)
- [文档目录组织](#文档目录组织)

## 项目 README

```markdown
# 项目名称

一句话说明这个项目解决什么问题。

## 环境要求

- Node.js ≥ 20
- 数据库版本
- 其他前置条件

## 快速开始

\`\`\`bash
npm install
npm run dev
\`\`\`

## 使用示例

\`\`\`typescript
import { createClient } from "pkg";
const client = createClient({ region: "us-east" });
const result = await client.query("SELECT 1");
\`\`\`

## 配置项

| 变量 | 必填 | 默认值 | 说明 |
| ---- | ---- | ------ | ---- |
| `API_KEY` | 是 | - | 服务密钥 |
| `LOG_LEVEL` | 否 | info | 日志级别 |

## 文档索引

- [API 参考](./docs/api/README.md)
- [架构总览](./docs/architecture/overview.md)
```

## API 端点文档

```markdown
# 资源名称

简要说明该资源做什么。

## GET /resources

获取资源列表。

**路径参数**

| 名称 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| - | - | - | 无 |

**查询参数**

| 名称 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `limit` | number | 否 | 每页数量（默认 20） |
| `cursor` | string | 否 | 分页游标 |

**响应**

\`\`\`json
{
  "data": [],
  "next_cursor": null
}
\`\`\`

**示例**

\`\`\`typescript
const page = await api.list("/resources", { limit: 10 });
\`\`\`

**错误码**

| 状态码 | 错误码 | 说明 |
| ------ | ------ | ---- |
| 400 | `INVALID_PARAMS` | 参数校验失败 |
| 401 | `UNAUTHORIZED` | 认证缺失或无效 |
```

## 文档目录组织

```
/docs
├── README.md              # 文档入口与索引
├── api/
│   ├── README.md          # API 总览
│   ├── authentication.md  # 认证说明
│   └── {resource}.md      # 每个资源一篇
├── architecture/
│   ├── overview.md        # 架构总览
│   └── data-flow.md       # 数据流说明
├── guides/
│   ├── getting-started.md # 入门指南
│   └── troubleshooting.md # 排障手册
└── features/
    └── {NNN}-{feature}.md # 功能说明，带编号
```
