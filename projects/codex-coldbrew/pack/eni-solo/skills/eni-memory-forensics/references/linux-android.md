# Linux 与 Android 内存分析

## Linux

可用面：`/proc/<pid>/maps`、`/proc/<pid>/mem`、process_vm_readv/writev、ptrace、core dump、gdb、rr、perf、uprobes/eBPF、分配器 hook 与 LD_PRELOAD。解析 ELF 映射时要区分文件偏移与虚拟地址。

## Android

可用面：ADB、Frida、LLDB、ART/JNI 边界、原生 linker 模块、`/proc` maps、Java 对象、原生缓冲区与运行时 hook。Unity IL2CPP 场景下，把 metadata、注册表、类/方法索引、对象布局、transform 与运行时实例互相关联起来。

## 稳定性注意

处理进程重启、ASLR、模块重载、线程竞态、GC、过期对象引用与架构差异。当生命周期事件使缓存指针失效时，重新解析地址。
