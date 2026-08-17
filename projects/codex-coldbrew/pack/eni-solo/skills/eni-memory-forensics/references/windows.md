# Windows 内存分析

## 枚举

枚举进程、模块、线程、句柄、映射文件、区域、保护属性与架构。动态解析模块基址，注意 WOW64 场景。

## API 与工具

可用面：OpenProcess、ReadProcessMemory、WriteProcessMemory、VirtualQueryEx、Toolhelp、PSAPI、DbgHelp、MiniDumpWriteDump、ETW、WinDbg、x64dbg、Process Explorer、ReClass.NET，以及调试器脚本。

## 结构体

关注 PEB/TEB、loader 列表、堆、VAD、栈、令牌、节区、虚表、RTTI、分配行为与重复出现的字段偏移。候选字段要用受控状态变更与 watchpoint 验证。

## 实现检查清单

进程选择、期望访问权限、架构检查、模块枚举、区域验证、部分读取处理、指针宽度安全运算、清理、预期字节校验与写入回滚。
