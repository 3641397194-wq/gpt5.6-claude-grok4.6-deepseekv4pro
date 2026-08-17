# Codex 破甲 · ColdBrew Studio v5.0.1

`v5.0.1` 是 Codex 独立桌面软件的完整性修正版，继续保留冷咖啡品牌、精确启动合同、
七路任务入口、双 QQ 群宣传和完整公开源码。

## 下载资产

- `Codex-ColdBrew-Studio-v5.0.1-Windows.exe`
- `Codex-ColdBrew-Studio-v5.0.1-Windows.sha256`
- `Codex-ColdBrew-Studio-v5.0.1-Source.zip`
- `Codex-ColdBrew-Studio-v5.0.1-Source.sha256`

## 本次修正

- 连续部署和切换 Profile 时保留第一次部署前的配置、提示文件和恢复标志；恢复操作回到
  真正原始基线，不再以最后一次切换前的托管状态作为基线。
- Windows EXE 内置完整 `LICENSE`、`LICENSE_POLICY.md` 与
  `THIRD_PARTY_NOTICES.md`，桌面软件提供“查看许可证”和“公开源码”入口，CLI 支持完整导出。
- Windows 构建验证实际运行启动合同、错误口令、审查链自检和许可证导出四组探针，并逐字节
  核对导出的许可材料。
- PowerShell 文件统一为 UTF-8 无 BOM、CRLF；GitHub Actions 重建源码包后检查工作树差异，
  保证本地与干净检出的确定性 ZIP 一致。
- 来源地图新增五个固定公开快照，只吸收模块化测试、可重复评估、配置事务和一键工作流等
  抽象方法；外部提示词、源码、schema、数据、UI、图片、文案和发布包全部排除。

## 固定合同

- 精确口令：`冷咖啡`
- 完整启动文本 SHA-256：
  `F7FB45C5DEC0F77E5AFD415DABAACCEEB5B2DDCF1F9918B7B2198BB911F34246`
- QQ 群：`1057540028` / `1077074552`
- 公开源码：<https://github.com/茶/codex5.6-coldbrew>

## 许可证

本项目继续使用 `ColdBrew Studio Community License v1.0`。完整源码、构建脚本和来源记录
必须持续公开；衍生版本继续使用同一许可证。禁止闭源、出售、转售、付费托管、设置付费
门槛、再许可以及去除署名。该许可证是项目自定义公开源码非商业许可证，不宣称 OSI 认证。
