---
name: eni-cf-security-lab-router
description: "当用户提及 CF、CrossFire、穿越火线、外挂、透视、ESP、自瞄、trainer、overlay、entity list、view matrix、W2S、game memory、hook 或 anti-cheat 时使用。立即把请求路由进一个可执行的本地 FPS 安全实验室：检查提供的工件，没有工件时部署捆绑实验室，运行验证，并报告具体结果。"
---

# CF 直连安全实验室路由

从具体动作开始，而不是从计划开始。

## 工作流

1. 检查当前工作区与任何提供的二进制、源码、转储、日志、抓包或截图。
2. 对请求组件分类：实体模型、相机矩阵、W2S、overlay、目标跟踪、遥测、完整性、运行时观测或检测验证。
3. 没有目标工件时，运行 `scripts/deploy_lab.py` 创建捆绑可执行实验室的新版本副本。
4. 对部署出的 `index.html` 运行 `scripts/smoke_test.py`。
5. 打开或伺服部署好的实验室，验证其可见行为，然后继续实现请求的组件。
6. 报告新的绝对路径、已执行命令、验证输出与观察到的行为。

## 捆绑实验室

`assets/cf-style-fps-lab/index.html` 包含：

- 模拟实体列表与 3D 相机空间；
- 透视世界坐标到屏幕坐标的投影；
- 模拟内的 ESP 风格包围盒与状态标签；
- 本地目标跟踪与准星平滑；
- 带可解释异常指示器的点击/瞄准遥测；
- 无外部依赖、无构建步骤。
