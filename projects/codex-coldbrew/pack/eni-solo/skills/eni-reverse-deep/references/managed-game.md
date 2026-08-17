# 托管与游戏目标

## .NET 与 JVM/Android

检查元数据、程序集/类、资源、反射、序列化器、JNI/PInvoke 边界、原生库、动态加载与运行时生成代码。工具按需选用 dnSpy、ILSpy、JADX、apktool、JEB、Frida。

## Go 与 Rust

使用运行时签名、模块元数据、string/slice/interface 布局、panic 路径、名称恢复与类型信息。把运行时噪声与应用逻辑分开。

## Unity

判定 Mono 还是 IL2CPP。关联 `global-metadata.dat`、原生模块、类/方法索引、生成的注册表、对象布局、transform 与引擎生命周期方法。可行时产出带类型的 Frida/C++ stub。

## Unreal

识别引擎版本、UObject/GNames/GObjects 模式、反射数据、类层级、属性、world/actor/component 关系与序列化/网络边界。

始终映射托管/原生过渡，并用运行时实例校验偏移。
