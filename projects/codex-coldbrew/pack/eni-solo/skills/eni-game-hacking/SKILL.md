---
description: "[DOCUMENTATION ONLY] [仅文档] 全局自动路由 | Game hacking techniques | 游戏逆向与内存工程参考"
name: eni-game-hacking
---

> 文档性质：本技能包仅提供研究方法、技术原理与代码范式（documentation-only），不附带可直接运行的脚本或程序。

# 游戏逆向与内存工程参考手册

本手册面向 Windows 游戏进程分析方向，系统梳理从内存扫描、代码注入、函数拦截，到渲染层集成、引擎逆向与保护机制剖析的完整技术链条。所有代码片段均为教学范式，用于说明 API 用法与工程组织方式。

## 适用场景与难度基线

| 场景 | 难度 | 说明 |
|------|------|------|
| 单机游戏修改器（Trainer） | ★ | 无服务端校验，纯本地内存读写即可 |
| 单机游戏注入式插件 | ★★ | 需要装载代码并拦截函数 |
| CTF 游戏安全赛题 | ★★ | 题目故意暴露缺陷，适合练手 |
| 停服/老式网络游戏 | ★★★ | 保护体系已停更，仍存在服务端校验 |
| 轻量联机游戏 | ★★★★ | 存在服务端校验，网络层操作受限 |
| 现代 3A 联机（EAC/BE 等） | ★★★★★ | 内核级保护，对抗成本极高 |
| 商业内核保护（TP/ACE/Vanguard 等） | ★★★★★ | 商业级内核对抗 |

## 核心认知：数据在哪里，决定修改是否有意义

```
单机游戏：数值与逻辑全部在本地内存 → 内存读写与代码拦截直接可见效果
联机游戏：关键数值由服务端验算 → 本地改动通常被服务端驳回
可操作面：服务端信任客户端的老协议、渲染层信息（ESP）、输入层逻辑（自瞄）
```

## 手册覆盖范围

1. 进程内存访问与扫描（ReadProcessMemory / WriteProcessMemory / 特征码定位）
2. 代码注入（远程线程装载 / 手动映射 / 代理 DLL）
3. 函数拦截（内联补丁 / 虚表替换 / 导入表重定向）
4. 覆盖层渲染（DirectX Hook / ImGui）
5. 引擎逆向（Unity Mono / IL2CPP / Unreal Engine）
6. 网络封包分析（send/recv 拦截 / Protobuf 识别）
7. 保护机制剖析（检测分层 / 内核内存访问 / 硬件标识）
8. 硬件辅助访问（DMA）
9. 移动端分析（APK 重打包 / Frida 插桩）

---

# 第一部分 环境与工具

## 1.1 开发工具链

```
编译与构建：
├── Visual Studio 2022 Community（C++ 桌面开发工作负载）
│   └── 组件: Windows 10/11 SDK、CMake、Clang tools
├── CMake 3.20+
├── Git
└── Python 3.10+（脚本与原型验证）

静态/动态分析：
├── Cheat Engine 7.5+    （内存扫描与定位）
├── x64dbg               （用户态动态调试）
├── IDA Pro / IDA Free   （静态反汇编与反编译）
├── Ghidra               （开源反编译备选）
├── ReClass.NET          （运行期结构体重建）
├── Process Hacker 2     （进程与句柄观测）
└── Detect It Easy (DIE) （壳与编译器识别）

配套工具：
├── HxD                  （十六进制编辑）
├── Wireshark            （网络抓包）
└── Fiddler / Burp       （HTTP 流量分析）
```

## 1.2 练习目标选择

| 目标 | 难度 | 练习重点 |
|------|------|----------|
| 自制的测试程序 | 入门 | 验证内存读写原语 |
| PWN Adventure 3 | 初级 | 单机 FPS，官方留洞，适合首练 |
| AssaultCube | 初级 | 开源 FPS，无保护，练习 ESP/自瞄 |
| CS 1.6 / CS:S | 初级 | 社区分析资料丰富 |
| Minecraft Java | 中级 | 非 native 程序的分析思路 |
| 老网游私服 | 中级 | 封包逆向与服务端模拟 |
| CTF 赛题 | 不定 | 在 CTFtime 检索 game-hacking / pwn |

入门顺序建议：先在自制程序上打通"扫描—定位—读写"链路，再迁移到小型开源游戏。

## 1.3 工程骨架（CMake）

```cmake
# CMakeLists.txt —— 注入式插件工程模板
cmake_minimum_required(VERSION 3.20)
project(gmh_toolkit)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_subdirectory(external/imgui)

add_library(toolkit SHARED
    src/dllmain.cpp
    src/memory.cpp
    src/detour.cpp
    src/renderer.cpp
    src/features.cpp
)

target_include_directories(toolkit PRIVATE
    external/imgui
    external/imgui/backends
    src/
)

target_link_libraries(toolkit PRIVATE
    imgui
    d3d11.lib
    dxgi.lib
)

# 以 DllMain 为入口，不链接 CRT main，减小体积
set_target_properties(toolkit PROPERTIES
    LINK_FLAGS "/ENTRY:DllMain"
    MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>"
)
```

---

# 第二部分 进程内存访问

> 外部进程内存访问是 Trainer 与信息采集的基础。核心只有三步：定位进程、打开句柄、读写地址。

## 2.1 目标定位与句柄封装

```cpp
// target.hpp —— 目标进程的定位与访问封装
#pragma once
#include <Windows.h>
#include <TlHelp32.h>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace gmh {

// 通过映像名定位进程 ID
std::optional<uint32_t> LocatePid(std::wstring_view imageName) {
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) return std::nullopt;

    PROCESSENTRY32W rec{ sizeof(rec) };
    if (Process32FirstW(snap, &rec)) {
        do {
            if (_wcsicmp(rec.szExeFile, imageName.data()) == 0) {
                CloseHandle(snap);
                return rec.th32ProcessID;
            }
        } while (Process32NextW(snap, &rec));
    }
    CloseHandle(snap);
    return std::nullopt;
}

// 通过模块名定位基址
std::optional<uintptr_t> LocateModuleBase(uint32_t pid, std::wstring_view moduleName) {
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE | TH32CS_SNAPMODULE32, pid);
    if (snap == INVALID_HANDLE_VALUE) return std::nullopt;

    MODULEENTRY32W rec{ sizeof(rec) };
    if (Module32FirstW(snap, &rec)) {
        do {
            if (_wcsicmp(rec.szModule, moduleName.data()) == 0) {
                CloseHandle(snap);
                return reinterpret_cast<uintptr_t>(rec.modBaseAddr);
            }
        } while (Module32NextW(snap, &rec));
    }
    CloseHandle(snap);
    return std::nullopt;
}

// 句柄 RAII 封装 + 读写原语
class ProcessHandle {
    HANDLE h_ = nullptr;

public:
    ProcessHandle() = default;
    ~ProcessHandle() { if (h_) CloseHandle(h_); }
    ProcessHandle(const ProcessHandle&) = delete;
    ProcessHandle& operator=(const ProcessHandle&) = delete;

    bool Open(uint32_t pid,
              uint32_t access = PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION) {
        h_ = OpenProcess(access, FALSE, pid);
        return h_ != nullptr;
    }
    explicit operator bool() const { return h_ != nullptr; }
    HANDLE Raw() const { return h_; }

    bool ReadRaw(uintptr_t where, void* out, size_t len) const {
        SIZE_T done = 0;
        return ReadProcessMemory(h_, reinterpret_cast<LPCVOID>(where), out, len, &done)
            && done == len;
    }
    bool WriteRaw(uintptr_t where, const void* in, size_t len) const {
        SIZE_T done = 0;
        return WriteProcessMemory(h_, reinterpret_cast<LPVOID>(where), in, len, &done)
            && done == len;
    }

    template <class T>
    std::optional<T> Read(uintptr_t where) const {
        T value{};
        if (!ReadRaw(where, &value, sizeof(T))) return std::nullopt;
        return value;
    }

    template <class T>
    bool Write(uintptr_t where, const T& value) const {
        return WriteRaw(where, &value, sizeof(T));
    }

    // 多级指针链：依次解引用并累加偏移
    std::optional<uintptr_t> ResolveChain(uintptr_t root,
                                          const std::vector<uintptr_t>& offsets) const {
        uintptr_t cursor = root;
        for (size_t i = 0; i < offsets.size(); ++i) {
            auto next = Read<uintptr_t>(cursor);
            if (!next) return std::nullopt;
            cursor = *next + offsets[i];
        }
        return cursor;
    }

    std::optional<std::string> ReadString(uintptr_t where, size_t maxLen = 256) const {
        std::vector<char> buffer(maxLen, 0);
        if (!ReadRaw(where, buffer.data(), maxLen)) return std::nullopt;
        buffer[maxLen - 1] = '\0';
        return std::string(buffer.data());
    }

    // 特征码扫描：mask 中 'x' 表示必须匹配，'?' 表示通配
    std::optional<uintptr_t> ScanPattern(uintptr_t from, size_t span,
                                         const std::vector<uint8_t>& sig,
                                         std::string_view mask) const {
        if (sig.empty() || sig.size() != mask.size()) return std::nullopt;
        std::vector<uint8_t> buffer(span);
        SIZE_T got = 0;
        if (!ReadProcessMemory(h_, reinterpret_cast<LPCVOID>(from),
                               buffer.data(), span, &got))
            return std::nullopt;

        const size_t limit = got >= sig.size() ? got - sig.size() + 1 : 0;
        for (size_t i = 0; i < limit; ++i) {
            bool hit = true;
            for (size_t j = 0; j < sig.size(); ++j) {
                if (mask[j] == 'x' && buffer[i + j] != sig[j]) { hit = false; break; }
            }
            if (hit) return from + i;
        }
        return std::nullopt;
    }
};

} // namespace gmh
```

## 2.2 外部修改器完整示例

```cpp
// trainer.cpp —— 外部修改器示例：等待目标进程并锁定数值
#include "target.hpp"
#include <chrono>
#include <cstdio>
#include <thread>

int main() {
    const std::wstring kImage = L"SampleGame.exe";
    // 假设通过扫描定位到的链: [game.exe+0x2A80C0] + 0x2F0 + 0x14 = 金币(int32)
    constexpr uintptr_t kBaseOffset = 0x2A80C0;
    constexpr uintptr_t kChain[] = { 0x2F0, 0x14 };

    std::printf("waiting for %ls ...\n", kImage.c_str());
    std::optional<uint32_t> pid;
    while (!(pid = gmh::LocatePid(kImage))) {
        std::this_thread::sleep_for(std::chrono::seconds(1));
    }

    gmh::ProcessHandle target;
    if (!target.Open(*pid)) {
        std::fprintf(stderr, "open failed (elevate and retry)\n");
        return 1;
    }

    auto base = gmh::LocateModuleBase(*pid, kImage);
    if (!base) { std::fprintf(stderr, "module base not found\n"); return 1; }
    std::printf("base = 0x%llx\n", static_cast<unsigned long long>(*base));

    auto goldAddr = target.ResolveChain(*base + kBaseOffset, { kChain[0], kChain[1] });
    if (!goldAddr) { std::fprintf(stderr, "chain walk failed\n"); return 1; }
    std::printf("gold @ 0x%llx\n", static_cast<unsigned long long>(*goldAddr));

    std::printf("press ENTER to freeze gold at 999999\n");
    std::getchar();

    for (;;) {
        target.Write<int32_t>(*goldAddr, 999999);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}
```

## 2.3 扫描定位工作流

```
第一步：精确值扫描
  当前血量 100 → 以 4 字节精确值搜索 100

第二步：差分缩小
  受击后血量变为 80 → 继续搜索 80，候选集收敛到数个地址

第三步：验证与锁定
  手动改写候选值，观察游戏内变化，确认唯一地址

第四步：回推静态基址
  对地址使用"找出写入该地址的指令"，受击后命中断点
  看到类似 mov [rax+0x10], ecx 的写指令
  逐级回推 rax 的来源，最终链到 game.exe+固定偏移

第五步：固化特征码（AOB）
  记录目标地址附近的字节序列，供版本更新后自动重定位

常见坑：
  - 浮点数值要选 "Float" 而非 "4 Bytes"
  - 部分游戏用 double（8 字节）存数值
  - 加密/变换后的值无法直接搜索 → 改用 "Changed / Unchanged" 与 "Increased / Decreased" 组合
  - 场景化地址只在对应界面有效 → 在正确场景内扫描
```

---

# 第三部分 代码注入

> 把代码放进目标进程是函数拦截与渲染集成的前提。三种主流装载方式：远程线程 + LoadLibrary（最直接）、手动映射（无模块痕迹）、代理 DLL（零注入动作）。

## 3.1 远程线程装载

```cpp
// remote_load.cpp —— LoadLibrary 远程装载
#include <Windows.h>
#include <string>

namespace gmh {

bool InjectByRemoteThread(uint32_t pid, const std::string& modulePath) {
    HANDLE hProc = OpenProcess(PROCESS_CREATE_THREAD | PROCESS_QUERY_INFORMATION |
                               PROCESS_VM_OPERATION | PROCESS_VM_WRITE, FALSE, pid);
    if (!hProc) return false;

    const size_t need = modulePath.size() + 1;
    void* remote = VirtualAllocEx(hProc, nullptr, need,
                                  MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!remote) { CloseHandle(hProc); return false; }

    bool ok = false;
    SIZE_T written = 0;
    if (WriteProcessMemory(hProc, remote, modulePath.c_str(), need, &written)
        && written == need) {
        FARPROC loadLibrary =
            GetProcAddress(GetModuleHandleA("kernel32.dll"), "LoadLibraryA");
        HANDLE hThread = CreateRemoteThread(hProc, nullptr, 0,
            reinterpret_cast<LPTHREAD_START_ROUTINE>(loadLibrary), remote, 0, nullptr);
        if (hThread) {
            WaitForSingleObject(hThread, INFINITE);
            CloseHandle(hThread);
            ok = true;
        }
    }
    VirtualFreeEx(hProc, remote, 0, MEM_RELEASE);
    CloseHandle(hProc);
    return ok;
}

} // namespace gmh
```

要点：远程线程的创建动作本身是用户态保护系统最常监控的信号之一，模块装载后也会出现在进程模块列表中。理解这一点有助于评估装载方式的选择。

## 3.2 手动映射（Manual Mapping）

思路：由装载器在目标进程中手工复刻 LoadLibrary 的全部动作——拷贝映像、修复重定位、解析导入、执行入口，全程不经过系统装载器，因此不产生标准的模块登记痕迹。

```
手动映射流程：
1. 将 DLL 文件读入本进程内存，解析 DOS 头与 NT 头
2. 在目标进程分配空间，按节表（Section Alignment）逐节拷贝
3. 计算装载滑动量（实际基址 - 首选基址），遍历重定位目录修正绝对地址
4. 解析导入目录：逐依赖模块装载并回填 IAT（支持按名称与按序号）
5. 执行 TLS 回调（如存在）
6. 调用 DllMain(DLL_PROCESS_ATTACH)
7. 结果：映像不在 PEB 的模块链表里，VAD 记录为私有内存而非映像映射，且无文件映射对象关联
```

```cpp
// mmap_shell.hpp —— 手动映射装载外壳
#pragma pack(push, 1)
struct MapShellContext {
    BYTE*  image;                 // 目标地址空间中的映像基址
    const IMAGE_NT_HEADERS* nt;   // 源映像的 NT 头
    IMAGE_BASE_RELOCATION* relocs;
    IMAGE_IMPORT_DESCRIPTOR* imports;
    HINSTANCE(WINAPI* pfnLoadLibrary)(LPCSTR);
    FARPROC(WINAPI* pfnGetProcAddress)(HMODULE, LPCSTR);
};
#pragma pack(pop)

// 在目标进程内执行：完成重定位、导入解析与入口调用
void __stdcall MapShellEntry(MapShellContext* ctx) {
    // 阶段 1：重定位表
    intptr_t slide = reinterpret_cast<intptr_t>(ctx->image)
                   - ctx->nt->OptionalHeader.ImageBase;
    if (slide != 0) {
        auto* block = ctx->relocs;
        while (block->SizeOfBlock != 0) {
            size_t entries = (block->SizeOfBlock - sizeof(IMAGE_BASE_RELOCATION))
                           / sizeof(WORD);
            auto* slots = reinterpret_cast<WORD*>(block + 1);
            for (size_t i = 0; i < entries; ++i) {
                if ((slots[i] >> 12) == IMAGE_REL_BASED_DIR64) {
                    auto* patch = reinterpret_cast<uintptr_t*>(
                        ctx->image + block->VirtualAddress + (slots[i] & 0xFFF));
                    *patch += slide;
                }
            }
            block = reinterpret_cast<IMAGE_BASE_RELOCATION*>(
                reinterpret_cast<uintptr_t>(block) + block->SizeOfBlock);
        }
    }

    // 阶段 2：导入表
    auto* desc = ctx->imports;
    while (desc->Name != 0) {
        HMODULE dep = ctx->pfnLoadLibrary(
            reinterpret_cast<LPCSTR>(ctx->image + desc->Name));
        auto* iat = reinterpret_cast<uintptr_t*>(ctx->image + desc->FirstThunk);
        auto* lookup = reinterpret_cast<IMAGE_THUNK_DATA*>(
            ctx->image + (desc->OriginalFirstThunk
                          ? desc->OriginalFirstThunk : desc->FirstThunk));
        while (lookup->u1.AddressOfData != 0) {
            if (IMAGE_SNAP_BY_ORDINAL(lookup->u1.Ordinal)) {
                *iat = reinterpret_cast<uintptr_t>(ctx->pfnGetProcAddress(
                    dep, reinterpret_cast<LPCSTR>(IMAGE_ORDINAL(lookup->u1.Ordinal))));
            } else {
                auto* named = reinterpret_cast<IMAGE_IMPORT_BY_NAME*>(
                    ctx->image + lookup->u1.AddressOfData);
                *iat = reinterpret_cast<uintptr_t>(
                    ctx->pfnGetProcAddress(dep, named->Name));
            }
            ++iat; ++lookup;
        }
        ++desc;
    }

    // 阶段 3：入口
    using EntryFn = BOOL(WINAPI*)(HINSTANCE, DWORD, LPVOID);
    auto entry = reinterpret_cast<EntryFn>(
        ctx->image + ctx->nt->OptionalHeader.AddressOfEntryPoint);
    entry(reinterpret_cast<HINSTANCE>(ctx->image), DLL_PROCESS_ATTACH, nullptr);
}
```

局限：手动映射解决的是模块登记层面的暴露。针对代码段完整性校验、VAD 特征扫描、句柄审计等更深入的检测手段，仍需结合内核层方案整体评估。

## 3.3 代理 DLL（Forwarder 方案）

```
适用场景：不需要注入器、随游戏自然装载

步骤：
1. 观察游戏 exe 同目录下的 DLL 集合
2. 用 Process Monitor 记录启动过程中从应用目录加载的模块
3. 选定候选：dinput8.dll / version.dll / winmm.dll 等
4. 生成代理 DLL：
   - 以转发器（forwarder）形式重导出原模块的全部函数
   - 在 DllMain 中执行自身初始化代码

工具与语法：
  - Dll_Wrapper_Generator（github.com/mavenlin）自动生成代理工程
  - 手动转发示例:
    #pragma comment(linker, "/EXPORT:DirectInput8Create=original.DirectInput8Create,@1")
```

## 3.4 装载后获取模块基址

```cpp
// in_process_base.cpp —— 进程内枚举模块基址
#include <Windows.h>
#include <Psapi.h>
#include <cstdint>

uintptr_t SelfModuleBase(const char* wanted) {
    HMODULE modules[512];
    DWORD bytes = 0;
    if (!EnumProcessModules(GetCurrentProcess(), modules, sizeof(modules), &bytes))
        return 0;

    char name[MAX_PATH] = {};
    for (DWORD i = 0; i < bytes / sizeof(HMODULE); ++i) {
        if (GetModuleBaseNameA(GetCurrentProcess(), modules[i], name, sizeof(name))
            && _stricmp(name, wanted) == 0)
            return reinterpret_cast<uintptr_t>(modules[i]);
    }
    return 0;
}
```

---

# 第四部分 函数拦截

> 拦截方案选择：内联补丁直接高效；虚表替换不触碰代码段；硬件断点最难被静态扫描发现。

## 4.1 x64 内联补丁与蹦床

```cpp
// detour.hpp —— 内联补丁与蹦床
#pragma once
#include <Windows.h>
#include <array>
#include <cstdint>
#include <cstring>

namespace gmh {

constexpr size_t kJumpSize = 14;  // mov rax,imm64 (10B) + jmp rax (2B)

class InlineDetour {
    std::array<uint8_t, kJumpSize> saved_{};
    uint8_t* site_ = nullptr;      // 被补丁的函数起始
    uint8_t* bridge_ = nullptr;    // 蹦床（原始指令 + 跳回）
    size_t patchLen_ = kJumpSize;

    static void EmitAbsJump(uint8_t* where, const void* dest) {
        where[0] = 0x48; where[1] = 0xB8;           // mov rax, imm64
        std::memcpy(where + 2, &dest, sizeof(dest));
        where[10] = 0xFF; where[11] = 0xE0;         // jmp rax
    }

public:
    InlineDetour() = default;
    ~InlineDetour() { Detach(); }
    InlineDetour(const InlineDetour&) = delete;
    InlineDetour& operator=(const InlineDetour&) = delete;

    bool Attach(void* target, void* hook) {
        DWORD old = 0;
        site_ = static_cast<uint8_t*>(target);
        if (!VirtualProtect(site_, patchLen_, PAGE_EXECUTE_READWRITE, &old)) return false;
        std::memcpy(saved_.data(), site_, patchLen_);

        // 蹦床：保存的原始字节 + 跳回补丁区之后
        bridge_ = static_cast<uint8_t*>(VirtualAlloc(nullptr, kJumpSize * 2,
                                                     MEM_COMMIT | MEM_RESERVE,
                                                     PAGE_EXECUTE_READWRITE));
        if (!bridge_) { VirtualProtect(site_, patchLen_, old, &old); return false; }
        std::memcpy(bridge_, saved_.data(), patchLen_);
        EmitAbsJump(bridge_ + patchLen_, site_ + patchLen_);

        // 目标：跳入 hook
        EmitAbsJump(site_, hook);
        VirtualProtect(site_, patchLen_, old, &old);
        return true;
    }

    void Detach() {
        if (!site_) return;
        DWORD old = 0;
        VirtualProtect(site_, patchLen_, PAGE_EXECUTE_READWRITE, &old);
        std::memcpy(site_, saved_.data(), patchLen_);
        VirtualProtect(site_, patchLen_, old, &old);
        if (bridge_) { VirtualFree(bridge_, 0, MEM_RELEASE); bridge_ = nullptr; }
        site_ = nullptr;
    }

    template <class Fn>
    Fn Callable() const { return reinterpret_cast<Fn>(bridge_); }
};

} // namespace gmh
```

工程注意点：补丁长度必须落在指令边界上（示例固定 14 字节，生产实现应内置长度反汇编器）；蹦床保存的原始字节若包含相对寻址指令，需额外做重定位。

使用示例——渲染入口拦截：

```cpp
// present_hook.cpp —— 渲染入口拦截示例
#include "detour.hpp"
#include <d3d11.h>

using PresentFn = HRESULT(STDMETHODCALLTYPE*)(IDXGISwapChain*, UINT, UINT);

gmh::InlineDetour g_PresentDetour;

HRESULT STDMETHODCALLTYPE PresentHook(IDXGISwapChain* chain, UINT sync, UINT flags) {
    RenderOverlay();   // 在原始画面之上绘制
    return g_PresentDetour.Callable<PresentFn>()(chain, sync, flags);
}

void InstallPresentHook() {
    void* present = LocatePresentAddress();   // 见第六部分
    g_PresentDetour.Attach(present, &PresentHook);
}
```

## 4.2 虚表槽位替换

```cpp
// vtable.hpp —— 虚表槽位替换（不修改代码段）
template <class Fn>
Fn SwapVtableSlot(void* object, size_t slot, Fn replacement) {
    auto* table = *reinterpret_cast<uintptr_t**>(object);
    DWORD old = 0;
    VirtualProtect(&table[slot], sizeof(void*), PAGE_READWRITE, &old);
    Fn original = reinterpret_cast<Fn>(table[slot]);
    table[slot] = reinterpret_cast<uintptr_t>(replacement);
    VirtualProtect(&table[slot], sizeof(void*), old, &old);
    return original;
}
```

## 4.3 常用拦截点清单

| 目标函数 | 定位途径 | 典型用途 |
|----------|----------|----------|
| `IDXGISwapChain::Present` / `vkQueuePresentKHR` | 虚表槽位 8 / 引擎导出 | 覆盖层渲染入口 |
| 伤害结算函数（TakeDamage 等） | 字符串交叉引用定位 | 伤害倍率 / 无敌 |
| `send` / `WSASend` | Ws2_32.dll 导出 | 封包拦截与改写 |
| `UGameEngine::Tick` | UE SDK | 每帧逻辑挂载 |
| `APlayerController::ProcessPlayerInput` | UE SDK | 输入处理观测 |
| `ServerMove` / `ServerFire` | 字符串 "Server" 检索 | 移动/射击封包分析 |
| `UpdateCamera` / `CalcView` | 虚表或字符串 | FOV 与视角修改 |
| `CEconItemSchema::GetItemDefinition`（CS） | 引擎已知偏移 | 外观数据修改 |
| `FireBullets`（Source） | NetVars + 特征码 | 弹道参数修改 |

---

# 第五部分 引擎逆向

## 5.1 Unity 后端识别

```
1. 用 DIE 检查 GameAssembly.dll 是否携带 Unity 签名
2. 看文件布局：
   - 存在 Assembly-CSharp.dll → Mono 后端
   - 存在 global-metadata.dat → IL2CPP 后端
3. 版本号：GameAssembly.dll 的文件版本属性
```

## 5.2 Unity Mono：程序集直接分析

```
工具：dnSpy（github.com/dnSpy/dnSpy）

步骤：
1. 用 dnSpy 打开 GameName_Data/Managed/Assembly-CSharp.dll
2. 左侧树展开后可见完整 C# 类与方法签名
3. 检索关键类：Player / GameManager / Weapon / Damage 等
4. 对目标方法右键 Edit Method，修改 IL 后保存

单机 Mono 游戏改程序集即可持久生效，无需注入器与 Hook。
常见修改模式：
  - Player.TakeDamage(float) → 置空函数体        // 无敌
  - Weapon.GetDamage() → 返回固定大值             // 秒杀
  - CurrencyManager.GetGold() → 返回固定大值      // 货币
```

## 5.3 Unity IL2CPP：元数据驱动的分析

```
IL2CPP 将 C# 转译为 C++，但元数据文件保留了符号信息。

工具链：
1. Il2CppDumper 输入 GameAssembly.dll + global-metadata.dat
   → 输出 dump.cs（类/方法/偏移总表）与 script.json（IDA/Ghidra 批注脚本）
2. 将 script.json 导入 IDA，自动完成符号与地址命名
3. 编写注入 + 拦截：
   - 在 dump.cs 中查目标方法偏移
   - GameAssembly.dll 基址 + RVA 得到实际地址
   - 直接内联补丁
4. 运行时 Hook 框架（非注入场景）：
   - MelonLoader（github.com/LavaGang）与 BepInEx（github.com/BepInEx）
   - 放入游戏目录即自动装载 mod DLL
```

## 5.4 Unity 导出符号速查

```
Mono:
  mono.dll + mono_runtime_invoke        动态调用托管方法
  mono.dll + mono_class_from_name       按名称获取类
  mono.dll + mono_compile_method        JIT 编译获取原生地址

IL2CPP:
  GameAssembly.dll + il2cpp_init
  GameAssembly.dll + il2cpp_class_from_name
  GameAssembly.dll + il2cpp_class_get_method_from_name
  GameAssembly.dll + il2cpp_runtime_invoke
  GameAssembly.dll + il2cpp_string_new

注意：不同 IL2CPP 版本导出符号可能被剥离。
  有符号 → 直接 GetProcAddress
  无符号 → 借助 Il2CppDumper 偏移 + 特征码定位
```

## 5.5 Unreal Engine：对象系统定位

```cpp
// 两个关键全局对象：GObjects 与 GNames

// 途径 1：特征码扫描
// GObjects 锚点：引用字符串 "Failed to find object Class %s.%s" 的代码
// GNames 锚点：引用 ByteProperty 的代码

// 途径 2：SDK Dumper 自动生成
// 使用 Dumper-7（github.com/Encryqed）一次性转储完整 SDK

// 途径 3：GEngine 定位
// 检索字符串 "Engine" → 交叉引用 → 回推 GEngine 指针
```

## 5.6 UE 对象遍历链

```
GEngine
  └→ GameViewport
       └→ World (UWorld)
            ├→ PersistentLevel (ULevel)
            │    └→ Actors (TArray<AActor*>)
            │         ├→ LocalPlayer → PlayerController → Pawn（本地玩家）
            │         └→ 其他 Pawn（其他玩家 / NPC）
            ├→ GameState (AGameState)
            │    └→ PlayerArray（全体玩家状态）
            └→ OwningGameInstance
                 └→ LocalPlayers
```

```cpp
// world_walk.cpp —— 基于转储 SDK 的实体遍历
void WalkEntities() {
    UWorld* world = *GWorld;    // GWorld 为需先定位的全局指针
    if (!world) return;

    UGameInstance* gi = world->OwningGameInstance;
    if (!gi) return;

    for (int i = 0; i < gi->LocalPlayers.Num(); ++i) {
        ULocalPlayer* lp = gi->LocalPlayers[i];
        APlayerController* pc = lp->PlayerController;
        APawn* self = pc->AcknowledgedPawn;
        FVector selfLoc = self->K2_GetActorLocation();
    }

    ULevel* level = world->PersistentLevel;
    for (int i = 0; i < level->Actors.Num(); ++i) {
        AActor* actor = level->Actors[i];
        if (actor && actor->IsA(ACharacter::StaticClass())) {
            auto* chr = static_cast<ACharacter*>(actor);
            FVector loc = chr->K2_GetActorLocation();
            float hp = chr->Health;
            // ESP：ProjectToScreen(loc) → 绘制
        }
    }
}
```

## 5.7 SDK 转储流程

```
1. 下载并编译 Dumper-7（github.com/Encryqed）
2. 将 Dumper-7.dll 装载进游戏进程
3. 等待输出目录生成：
   ├── SDK/               所有类的 C++ 头文件
   ├── Globals.h          GObjects / GNames / GWorld 声明
   └── PropertyFixup.hpp
4. 将 SDK 目录并入工程，include "SDK.hpp"
5. 以原生 C++ 风格直接调用游戏函数
```

---

# 第六部分 渲染层与覆盖层

> 覆盖层渲染的通用路径：定位交换链 Present → 在其前后插入绘制 → ImGui 呈现。配合手动映射装载可减少模块层面的暴露。

## 6.1 定位 Present 地址

```cpp
// present_locate.cpp —— 通过临时交换链取虚表槽位
void* LocateD3D11Present() {
    WNDCLASSEX wc = { sizeof(WNDCLASSEX), CS_CLASSDC, DefWindowProc, 0, 0,
                      GetModuleHandle(nullptr), nullptr, nullptr, nullptr, nullptr,
                      L"ProbeWindow", nullptr };
    RegisterClassEx(&wc);
    HWND hwnd = CreateWindow(L"ProbeWindow", L"", WS_OVERLAPPEDWINDOW,
                             0, 0, 100, 100, nullptr, nullptr, wc.hInstance, nullptr);

    DXGI_SWAP_CHAIN_DESC sd = {};
    sd.BufferCount = 1;
    sd.BufferDesc.Width = 100;
    sd.BufferDesc.Height = 100;
    sd.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    sd.BufferDesc.RefreshRate = { 60, 1 };
    sd.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    sd.OutputWindow = hwnd;
    sd.SampleDesc.Count = 1;
    sd.Windowed = TRUE;

    ID3D11Device* device = nullptr;
    ID3D11DeviceContext* context = nullptr;
    IDXGISwapChain* chain = nullptr;

    D3D11CreateDeviceAndSwapChain(nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, 0,
                                  nullptr, 0, D3D11_SDK_VERSION, &sd,
                                  &chain, &device, nullptr, &context);

    // DX11 的 IDXGISwapChain::Present 位于虚表槽位 8
    void* present = (*reinterpret_cast<void***>(chain))[8];

    chain->Release();
    context->Release();
    device->Release();
    DestroyWindow(hwnd);
    UnregisterClass(L"ProbeWindow", wc.hInstance);
    return present;
}
```

## 6.2 ImGui 覆盖层集成

```cpp
// renderer.cpp —— Present 钩子内的 ImGui 生命周期
#include "imgui.h"
#include "imgui_impl_dx11.h"
#include "imgui_impl_win32.h"
#include <d3d11.h>

namespace {
    bool                g_ready = false;
    ID3D11Device*       g_device = nullptr;
    ID3D11DeviceContext* g_context = nullptr;
    ID3D11RenderTargetView* g_rtv = nullptr;
    gmh::InlineDetour  g_detour;
}

HRESULT STDMETHODCALLTYPE PresentHook(IDXGISwapChain* chain, UINT sync, UINT flags) {
    if (!g_ready) {
        // 从交换链取回设备与上下文
        chain->GetDevice(__uuidof(ID3D11Device), reinterpret_cast<void**>(&g_device));
        g_device->GetImmediateContext(&g_context);

        // 后备缓冲 → 渲染目标视图
        ID3D11Texture2D* back = nullptr;
        chain->GetBuffer(0, __uuidof(ID3D11Texture2D), reinterpret_cast<void**>(&back));
        g_device->CreateRenderTargetView(back, nullptr, &g_rtv);
        back->Release();

        DXGI_SWAP_CHAIN_DESC sd;
        chain->GetDesc(&sd);

        ImGui::CreateContext();
        ImGui_ImplWin32_Init(sd.OutputWindow);
        ImGui_ImplDX11_Init(g_device, g_context);
        ImGui::StyleColorsDark();
        g_ready = true;
    }

    ImGui_ImplDX11_NewFrame();
    ImGui_ImplWin32_NewFrame();
    ImGui::NewFrame();

    DrawEspLayer();          // 见 6.4

    ImGui::Render();
    g_context->OMSetRenderTargets(1, &g_rtv, nullptr);
    ImGui_ImplDX11_RenderDrawData(ImGui::GetDrawData());

    return g_detour.Callable<decltype(&PresentHook)>()(chain, sync, flags);
}
```

## 6.3 世界坐标到屏幕坐标

```cpp
// view.hpp —— 投影变换
struct Vec2 { float x = 0.f, y = 0.f; };
struct Vec3 { float x = 0.f, y = 0.f, z = 0.f; };

// viewProj 为 4x4 行主序 View*Projection 矩阵
inline bool ProjectToScreen(const Vec3& world, const float viewProj[16],
                            float vpWidth, float vpHeight, Vec2& out) {
    const float clipW =
        world.x * viewProj[3] + world.y * viewProj[7] + world.z * viewProj[11] + viewProj[15];
    if (clipW < 0.001f) return false;   // 位于相机后方

    const float clipX =
        world.x * viewProj[0] + world.y * viewProj[4] + world.z * viewProj[8] + viewProj[12];
    const float clipY =
        world.x * viewProj[1] + world.y * viewProj[5] + world.z * viewProj[9] + viewProj[13];

    out.x = (clipX / clipW + 1.f) * 0.5f * vpWidth;
    out.y = (1.f - (clipY / clipW + 1.f) * 0.5f) * vpHeight;
    return true;
}
```

## 6.4 叠加绘制

```cpp
// esp.cpp —— 覆盖层绘制示例
void DrawEspLayer() {
    const ImGuiIO& io = ImGui::GetIO();
    const float vpW = io.DisplaySize.x;
    const float vpH = io.DisplaySize.y;
    auto* canvas = ImGui::GetBackgroundDrawList();

    Vec3 self = LocalPlayerPosition();
    for (const auto& ent : EnemySnapshot()) {
        if (!ent.valid || ent.dead) continue;

        Vec2 head{}, root{};
        if (!ProjectToScreen(ent.bones[BONE_HEAD],  g_ViewProj, vpW, vpH, head)) continue;
        if (!ProjectToScreen(ent.bones[BONE_PELVIS], g_ViewProj, vpW, vpH, root)) continue;

        const float h = root.y - head.y;
        const float w = h * 0.5f;
        const ImVec2 topLeft    { head.x - w * 0.5f, head.y };
        const ImVec2 bottomRight{ head.x + w * 0.5f, head.y + h };

        // 方框：敌我着色
        const bool hostile = ent.team != LOCAL_TEAM;
        const ImU32 outline = hostile ? IM_COL32(255, 84, 84, 220)
                                      : IM_COL32(120, 255, 120, 220);
        canvas->AddRect(topLeft, bottomRight, outline, 0.f, 0, 1.4f);

        // 生命条：左侧竖条
        const float ratio = static_cast<float>(ent.health)
                          / static_cast<float>(ent.maxHealth);
        const ImVec2 barMin{ topLeft.x - 7.f, topLeft.y };
        const ImVec2 barMax{ topLeft.x - 3.f, bottomRight.y };
        canvas->AddRectFilled(barMin, barMax, IM_COL32(0, 0, 0, 140));
        const float fillTop = barMax.y - h * ratio;
        canvas->AddRectFilled({ barMin.x, fillTop }, barMax, IM_COL32(96, 255, 96, 255));

        // 距离标签
        const float meters = (ent.origin - self).Len() * 0.01f;
        char label[32];
        std::snprintf(label, sizeof(label), "%.0fm", meters);
        canvas->AddText({ bottomRight.x + 3.f, topLeft.y },
                        IM_COL32(255, 255, 255, 230), label);

        // 骨骼连线
        DrawBoneLines(canvas, ent, vpW, vpH);
    }
}

void DrawBoneLines(ImDrawList* canvas, const Entity& ent, float vpW, float vpH) {
    static constexpr std::pair<int, int> kSegments[] = {
        { BONE_HEAD, BONE_NECK }, { BONE_NECK, BONE_SPINE },
        { BONE_SPINE, BONE_L_SHOULDER }, { BONE_L_SHOULDER, BONE_L_ELBOW },
        { BONE_L_ELBOW, BONE_L_WRIST },
        { BONE_SPINE, BONE_R_SHOULDER }, { BONE_R_SHOULDER, BONE_R_ELBOW },
        { BONE_R_ELBOW, BONE_R_WRIST },
        { BONE_SPINE, BONE_PELVIS },
        { BONE_PELVIS, BONE_L_KNEE }, { BONE_L_KNEE, BONE_L_ANKLE },
        { BONE_PELVIS, BONE_R_KNEE }, { BONE_R_KNEE, BONE_R_ANKLE },
    };
    for (auto [a, b] : kSegments) {
        Vec2 pa{}, pb{};
        if (ProjectToScreen(ent.bones[a], g_ViewProj, vpW, vpH, pa)
            && ProjectToScreen(ent.bones[b], g_ViewProj, vpW, vpH, pb)) {
            canvas->AddLine({ pa.x, pa.y }, { pb.x, pb.y },
                            IM_COL32(255, 255, 255, 190), 1.f);
        }
    }
}
```

---

# 第七部分 瞄准辅助与输入

## 7.1 视角角度计算

```cpp
// aim.cpp —— 视角修正
struct EulerAngles { float pitch = 0.f, yaw = 0.f, roll = 0.f; };

EulerAngles AngleTo(const Vec3& from, const Vec3& to) {
    const float dx = to.x - from.x;
    const float dy = to.y - from.y;
    const float dz = to.z - from.z;
    const float horiz = std::sqrt(dx * dx + dy * dy);

    EulerAngles out;
    out.pitch = -std::atan2(dz, horiz) * (180.f / 3.14159265f);
    out.yaw   =  std::atan2(dy, dx) * (180.f / 3.14159265f);
    return out;
}

float NormalizeDeg(float deg) {
    while (deg > 180.f) deg -= 360.f;
    while (deg < -180.f) deg += 360.f;
    return deg;
}

// 指数平滑：alpha 越小越"跟手"
EulerAngles SmoothToward(const EulerAngles& current, const EulerAngles& goal, float alpha) {
    EulerAngles out = current;
    out.yaw   += NormalizeDeg(goal.yaw   - current.yaw)   * alpha;
    out.pitch += NormalizeDeg(goal.pitch - current.pitch) * alpha;
    return out;
}
```

## 7.2 目标筛选与视角写入

```cpp
// 屏幕空间 FOV 筛选 → 计算角度 → 平滑写入
void AimAssistTick() {
    const Vec3 eye = LocalPlayerBone(BONE_HEAD);
    float bestDist = std::numeric_limits<float>::max();
    Vec3 chosen{};

    for (const auto& ent : EnemySnapshot()) {
        if (!ent.valid || ent.team == LOCAL_TEAM) continue;

        Vec2 screen{};
        if (!ProjectToScreen(ent.bones[BONE_HEAD], g_ViewProj, ViewportW(), ViewportH(), screen))
            continue;   // 不在屏幕内

        const float dx = screen.x - ViewportW() * 0.5f;
        const float dy = screen.y - ViewportH() * 0.5f;
        const float dist = std::sqrt(dx * dx + dy * dy);
        if (dist < bestDist && dist < g_AimRadius) {   // g_AimRadius 为用户设定半径
            bestDist = dist;
            chosen = ent.bones[BONE_HEAD];
        }
    }

    if (bestDist < std::numeric_limits<float>::max()) {
        EulerAngles goal = AngleTo(eye, chosen);
        EulerAngles cur  = ReadViewAngles();
        WriteViewAngles(SmoothToward(cur, goal, g_Smoothing));
        // UE 对应路径：APlayerController::SetControlRotation
    }
}
```

## 7.3 触发式开火（Triggerbot）

```cpp
// 准星指向实体时自动开火
void TriggerTick() {
    int id = LocalPlayer()->CrosshairEntityId();
    if (id <= 0) return;

    Entity* t = EntityById(id);
    if (!t || !t->alive || t->team == LOCAL_TEAM) return;

    // 方案 A：用户态输入模拟（通用，但特征明显）
    SendInput 风格按键序列，按下与抬起之间插入随机间隔 20~50ms

    // 方案 B：直接调用引擎开火入口（更可靠）
    // LocalPlayer()->Weapon()->StartFire();
}
```

## 7.4 后座力补偿

```cpp
// 每帧读取 punch 角增量并反向修正
void RecoilCompensate() {
    static Vec3 prevPunch{};

    Vec3 punch = LocalPlayer()->AimPunchAngle();
    Vec3 delta = punch - prevPunch;      // 本帧新增的后座分量
    Vec3 view  = ReadViewAngles();

    Vec3 corrected = view - delta * g_Compensation;   // 补偿系数可调
    WriteViewAngles(corrected);
    prevPunch = punch;
}
```

---

# 第八部分 网络封包分析

> 前提：封包改写只对信任客户端数据的协议有效。现代联机游戏多为服务端权威，本地篡改易被驳回；读取方向（信息雷达）受加密影响但适用范围更广。

## 8.1 不同封包操作的可生效范围

| 操作 | 有效场景 | 受限场景 |
|------|----------|----------|
| 坐标篡改 | P2P 主机模型的老游戏 | 现代服务端权威 FPS |
| 伤害数值篡改 | 老游戏 / 单机 | 服务端结算 |
| 重放发包刷取 | 缺少幂等校验的老网游 | 有请求去重校验的游戏 |
| 客户端模拟 | 私服 / 无加密老协议 | TLS + 私有协议 |
| 选择性丢包（Lag Switch） | P2P 对局 | 专用服务器 |
| 读取方向（雷达/信息） | 大部分游戏 | 仅受封包加密影响 |

## 8.2 send/recv 拦截

```cpp
// packet_hook.cpp —— 收发拦截示例
int WSAAPI SendHook(SOCKET s, const char* buf, int len, int flags) {
    TracePacket("OUT", buf, len);
    // 若协议无签名保护，可在此改写缓冲内容
    return RealSend(s, buf, len, flags);
}

int WSAAPI RecvHook(SOCKET s, char* buf, int len, int flags) {
    int got = RealRecv(s, buf, len, flags);
    if (got > 0) {
        // 解析入站数据：如提取实体坐标用于雷达呈现
        TracePacket("IN", buf, got);
    }
    return got;
}

void InstallPacketHooks() {
    HMODULE ws2 = GetModuleHandleA("ws2_32.dll");
    void* sendAddr = GetProcAddress(ws2, "send");
    void* recvAddr = GetProcAddress(ws2, "recv");
    g_SendDetour.Attach(sendAddr, &SendHook);
    g_RecvDetour.Attach(recvAddr, &RecvHook);
}
```

## 8.3 协议逆向流程

```
1. 抓取：Wireshark 过滤 ip.dst == 服务器IP；对走路、跳跃、射击、换弹、
   使用道具各抓 3-5 组样本
2. 差分：同操作多包对比 → 固定字节（包头/命令字）；跨操作对比 → 变化字节（参数）
3. 结构假设：[2B 长度][2B 命令][4B 序号][N 字节负载（可能为 Protobuf）]
4. 验证：改字段 → 发包 → 观察服务器响应 → 确认字段语义
5. 解密：若负载为密文，在 IDA 中回溯 send 调用点，向上定位加密函数，
   提取密钥/IV 后编写解密脚本
6. 原型：用 Python + scapy 构造测试包；注意沿用游戏客户端自身的 socket 发送
```

## 8.4 Protobuf 识别

```
许多游戏采用 Google Protobuf 序列化，识别特征：
1. 明显的 varint 编码模式：
   - 每字节高位置 1 表示后续字节仍属于同一数值
   - 字段头结构：[field_number << 3 | wire_type]
2. 常见 wire_type：
   0 = Varint（整数）
   2 = Length-delimited（字符串/嵌套消息/字节数组）
3. 有 .proto 定义时：
   protoc --decode_raw < packet.bin            自动推断解析
   protoc --decode PackageName msg.proto < packet.bin   按 schema 解析
```

---

# 第九部分 保护机制剖析

> 现代联机游戏普遍部署多层保护体系。理解检测面的构成，是评估任何技术方案可行性的前提。

## 9.1 检测体系分层

```
第 0 层：启动前环境检查
  → 反作弊驱动开机常驻（Vanguard 等）
  → 检查已加载驱动签名、虚拟化环境（Hypervisor）存在性

第 1 层：装载期拦截
  → 游戏文件完整性校验（.text 段哈希）
  → 加载内核驱动并注册回调：
      ObRegisterCallbacks（句柄操作）
      PsSetCreateProcessNotifyRoutine（进程创建）
      PsSetCreateThreadNotifyRoutine（线程创建）
      PsSetLoadImageNotifyRoutine（模块装载）

第 2 层：运行期周期扫描
  → 内存面：PEB 模块链表、VAD 树、代码段校验和
  → 线程面：全线程枚举、起始地址审计
  → 句柄面：进程句柄枚举与权限复核
  → 窗口面：叠加窗口检查（WS_EX_LAYERED / WS_EX_TRANSPARENT）
  → 调试面：调试寄存器读取（NtGetContextThread）
  → 行为面：API 调用频率、内存访问模式统计

第 3 层：服务端
  → 战绩统计异常（K/D 突增、爆头率、反应时间）
  → 输入行为分析（鼠标轨迹、按键间隔分布）
  → 举报 → 人工复核 → 观战监管系统
```

## 9.2 检测点与对抗概念对照

| 检测手段 | 对抗概念 | 难度 |
|----------|----------|------|
| 句柄权限控制 | 内核侧读写路径（MmCopyVirtualMemory） | 中 |
| 模块链表枚举 | 手动映射装载，清除 PE 头痕迹 | 中 |
| VAD 特征扫描 | 构造与映像加载一致的映射特征 | 高 |
| 代码段完整性校验 | 时序博弈或拦截读取路径 | 高 |
| 线程起始地址审计 | 挂靠既有合法线程执行 | 高 |
| 调试寄存器检查 | 规避硬件断点或拦截读取 API | 中 |
| 覆盖窗口检测 | DWM 合成层叠加 | 中 |
| 驱动黑名单 | 更换未被拉黑的装载器 | 极高 |
| 行为统计 | 拟人化输入曲线、随机延迟 | 低 |
| 服务端行为分析 | 维持类人水平 | 极高 |

## 9.3 内核侧跨进程读写

```c
// kb_io.c —— 内核侧跨进程读写示例
// 生产实现还需处理：IRQL 约束、异常边界（__try/__except）、
// 页表锁定，以及隐蔽通信通道（共享内存 / .data 指针交换）

#include <ntddk.h>

NTSTATUS KbReadProcessMemory(HANDLE pid, PVOID src, PVOID dst, SIZE_T bytes) {
    PEPROCESS proc = NULL;
    NTSTATUS st = PsLookupProcessByProcessId(pid, &proc);
    if (!NT_SUCCESS(st)) return st;

    SIZE_T moved = 0;
    st = MmCopyVirtualMemory(proc, src, IoGetCurrentProcess(),
                             dst, bytes, KernelMode, &moved);
    ObDereferenceObject(proc);
    return st;
}

NTSTATUS KbWriteProcessMemory(HANDLE pid, PVOID src, PVOID dst, SIZE_T bytes) {
    PEPROCESS proc = NULL;
    NTSTATUS st = PsLookupProcessByProcessId(pid, &proc);
    if (!NT_SUCCESS(st)) return st;

    SIZE_T moved = 0;
    st = MmCopyVirtualMemory(IoGetCurrentProcess(), src,
                             proc, dst, bytes, KernelMode, &moved);
    ObDereferenceObject(proc);
    return st;
}

// 通信建议：避免使用特征明显的 IOCTL 通道，
// 可采用共享内存 + 低关注度系统函数的旁路交换，或 .data 指针交换
```

## 9.4 硬件标识（HWID）采集机制

```
反作弊常用硬件指纹来源：
  - 注册表 MachineGuid（HKLM\SOFTWARE\Microsoft\Cryptography）
  - 注册表 HwProfileGuid（IDConfigDB\Hardware Profiles\0001）
  - SMBIOS 信息（UUID、序列号）
  - 卷序列号（GetVolumeInformationW）
  - 网卡 MAC（GetAdaptersAddresses）

对抗概念：在内核层拦截上述读取 API，返回随机化后的伪造值。
每项标识需单独处理，且检测方更新采集方式后需同步跟进。
```

---

# 第十部分 硬件辅助访问（DMA）

> 以 FPGA 板卡直接经 PCIe 总线读取物理内存，数据面完全绕开主机 CPU 与操作系统，软件层几乎无迹可寻。仅少数保护体系尝试从 PCIe 时序异常角度检测。

## 10.1 原理对比

```
软件路径：
  你的代码 → OpenProcess → RPM/WPM → 游戏进程内存
                                      ↑
                            反作弊在内核层监控

硬件路径：
  第二台 PC（分析端） ← 网线/USB ← FPGA 板卡（插在目标机主板）
                                        ↓
                              PCIe 总线直读物理内存
                                        ↓
                              不经过 CPU，主机 OS 无感知
```

## 10.2 组成部件

```
- FPGA 开发板：Screamer / LeetDMA / ZDMA 等（约 ¥1000-5000）
- 第二台 PC：数据处理与渲染
- 视频采集卡：将分析端的叠加画面送回游戏显示器
- 输入模拟器：KMBox / Arduino（硬件级键鼠注入）
总计投入：约 ¥3000-10000+
```

## 10.3 软件栈概念

```cpp
// 伪代码 —— 实际实现基于 pcileech 或自制固件
#include "dma.h"

int main() {
    DMA dev;
    dev.init("fpga_device");

    uint32_t pid = dev.find_pid("game.exe");
    uint64_t dtb = dev.process_dirbase(pid);   // 页表目录基址

    // 手动遍历页表完成虚拟地址解析
    VmmSession vmm(dev, dtb);
    uint64_t base = vmm.module_base("game.exe");

    // 指针链读取
    uint64_t gold = vmm.chain(base + 0x2A80C0, { 0x2F0, 0x14 });
    int32_t value = vmm.read<int32_t>(gold);

    // 实体列表批量读取
    for (uint64_t e : vmm.read_array<uint64_t>(entityList, entityCount)) {
        Vec3 pos = vmm.read<Vec3>(e + 0x100);
        // 投影后渲染到采集卡叠加画面
    }
}
```

---

# 第十一部分 移动端分析（Android）

## 11.1 APK 拆解与重打包

```bash
# 适用：单机手游与无服务端强校验的手游。
# 服务端权威的游戏（如主流 MOBA）核心逻辑在服务器，客户端改动效果有限。

# 1. 反编译
apktool d game.apk -o game_src

# 2. 浏览 Java 源码
jadx-gui game.apk

# 3. 修改 smali（示例：改写伤害结算）
#    搜索 "calcDamage" 定位方法
#    将返回值改写为常量: const/4 v0, 0x1

# 4. 如涉及 native 逻辑：
#    IDA 加载 lib/arm64-v8a/libil2cpp.so
#    定位关键函数后修改 arm64 指令

# 5. 重打包
apktool b game_src -o game_mod.apk

# 6. 签名
uber-apk-signer --apks game_mod.apk
```

## 11.2 Frida 运行时插桩

```javascript
// hook.js —— 无需重打包的运行时插桩
// 启动: frida -U -l hook.js com.game.package

Java.perform(() => {
    // 改写 Java 方法返回值
    const Wallet = Java.use("com.game.Wallet");
    Wallet.getGold.implementation = function () {
        console.log("[hook] getGold -> 99999");
        return 99999;
    };

    // 改写传入参数
    const Player = Java.use("com.game.Player");
    Player.applyDamage.implementation = function (amount) {
        console.log("[hook] applyDamage(", amount, ") -> 0");
        return this.applyDamage(0);
    };
});

// Hook native 函数（IL2CPP 产物）
const il2cpp = Module.findBaseAddress("libil2cpp.so");
if (il2cpp) {
    // Player::ApplyDamage 偏移来自 Il2CppDumper 输出
    const applyDamage = il2cpp.add(0x12345678);
    Interceptor.attach(applyDamage, {
        onEnter(args) {
            console.log("[native] damage arg =", args[1].toInt32());
            args[1] = ptr(0);
        },
        onLeave(retval) {
            console.log("[native] return =", retval);
        }
    });
}

// SSL Pinning 去除（流量分析场景）
// 替换 TrustManager 为全信任实现，配合抓包工具观察明文流量
```

---

# 第十二部分 工程组织、调试与排障

## 12.1 项目目录结构

```
gmh-toolkit/
├── CMakeLists.txt
├── external/
│   └── imgui/                  # Dear ImGui
├── src/
│   ├── dllmain.cpp             # 模块入口
│   ├── target.hpp              # 进程访问封装
│   ├── detour.hpp              # 内联补丁
│   ├── view.hpp                # 投影变换
│   ├── renderer.cpp            # 渲染初始化与 Present 钩子
│   ├── esp.cpp                 # 覆盖层绘制
│   ├── aim.cpp                 # 瞄准辅助
│   ├── packet_hook.cpp         # 网络拦截
│   └── features.cpp            # 功能汇总与菜单
├── injector/
│   ├── remote_load.cpp         # 远程线程装载
│   └── mmap_loader.cpp         # 手动映射装载器
└── tests/
    └── probe_target.cpp        # 自制测试目标
```

## 12.2 装载态调试

```
方法 1：Visual Studio 附加调试
  Debug → Attach to Process → 选择目标进程
  → 在模块代码处下断点 → 触发装载 → 命中断点

方法 2：OutputDebugString + DebugView
  代码中埋 OutputDebugStringA 日志
  用 Sysinternals DebugView 实时查看
  不依赖调试器，适合排查装载阶段问题

方法 3：消息框探针
  在关键路径弹出 MessageBox 确认执行到达
  不同位置使用不同文案以追踪路径
```

## 12.3 常见故障定位

```
装载阶段崩溃：
  → 核对调用约定是否一致
  → 检查是否破坏非易失寄存器（x64: rbx/rbp/rdi/rsi/r12-r15）
  → 用 __try/__except 包裹钩子函数

钩子函数内崩溃：
  → 蹦床字节数须落在指令边界（不能截断指令）
  → x64 栈需 16 字节对齐
  → 多线程场景检查重入

RPM/WPM 失败：
  → 指针链中出现空指针 → 逐级校验
  → 写入只读页 → 先 VirtualProtectEx 调整属性
```

## 12.4 交付前的工程加固

```
测试策略：
  - 先于无保护游戏验证功能正确性
  - 再于受保护环境验证装载与隐蔽性
  - 全程在受控账号与环境中进行

二进制加固（进阶）：
  - 编译期字符串加密（xorstr / skCrypter）
  - 代码虚拟化（VMProtect / Themida）
  - 反调试检测（IsDebuggerPresent / NtQueryInformationProcess）
```

---

# 附录：学习路线

```
第一阶段：内存基础（1-2 周）
  □ 完成自制程序的外部修改器，锁定一个数值
  □ 熟练 Cheat Engine 的扫描与指针链回溯
  □ 理解进程虚拟地址空间布局

第二阶段：装载与拦截（2-4 周）
  □ 编写远程线程装载器，向自制程序注入模块
  □ 完成 Hook MessageBox 的入门练习
  □ 拦截单机游戏的伤害函数并修改倍率

第三阶段：引擎逆向（4-8 周）
  □ 用 dnSpy 分析 Unity Mono 游戏并修改程序集
  □ 用 Il2CppDumper + IDA 分析 IL2CPP 游戏
  □ 转储 UE 游戏 SDK，遍历 Actor 列表

第四阶段：渲染与瞄准（4-8 周）
  □ 钩住 DX11 Present，绘制首个矩形
  □ 实现投影变换与方框 ESP
  □ 实现 FOV 筛选 + 平滑瞄准

第五阶段：网络与内核（8 周+）
  □ 拦截 send/recv 分析协议格式
  □ 逆向一款轻量保护的用户态检测逻辑
  □ 编写内核驱动，经装载器加载后实现内核读写
  □ 手动映射并完成链表摘除

第六阶段：进阶研究
  □ 剖析商业反作弊驱动的检测流程
  □ 研究 DMA 硬件方案
  □ 整理输出安全研究报告
```

---

## 参考资源

```
工具与项目索引（持续更新的开源游戏安全资源列表）：
https://raw.githubusercontent.com/gmh5225/awesome-game-security/refs/heads/main/README.md
```

---

> 手册定位声明
>
> 本文档面向游戏逆向工程、安全研究、CTF 竞赛与游戏修改方向的技术参考。
> 覆盖主题：进程内存读写、代码注入、函数拦截、覆盖层渲染、网络封包分析、
> 内核内存访问、硬件辅助访问与保护机制剖析。
> 文中代码均为教学范式；实际落地时应结合目标环境完成适配与验证。
