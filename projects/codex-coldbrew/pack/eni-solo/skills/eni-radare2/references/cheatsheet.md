# radare2 速查表

## 第一轮侦察

```powershell
rabin2 -I sample.exe     # 格式、架构、入口点
rabin2 -S sample.exe     # 节区表
rabin2 -i sample.exe     # 导入表
rabin2 -E sample.exe     # 导出表
rabin2 -zz sample.exe    # 字符串（含交叉引用）
```

## 交互会话

```powershell
r2 sample.exe            # 只读打开
r2 -w sample.exe         # 写模式（明确要 patch 时）
```

```text
aaa          # 常规自动分析
afl          # 函数列表
iz           # 字符串
iS           # 节区
is           # 符号
s entry0     # 跳转到入口点
pdf          # 反汇编当前函数
VV           # 可视化模式
q            # 退出
```

## 字符串与引用定位

```text
iz~http       # 过滤字符串
iz~error
axt <addr>    # 谁引用了这个地址
s <addr>      # 跳过去
pdf           # 反汇编
```

## 查看

```text
px 64         # 64 字节十六进制
pd 20         # 20 条反汇编
psz           # 当前地址的字符串
pxa           # 友好十六进制视图
```

## 写操作（patch）

```text
s 0x401000
wa nop        # 写汇编
wx 9090       # 写字节
wq            # 保存并退出
```

## 非交互批处理

```powershell
r2 -A -q -c "afl;iz;ii;q" sample.exe
```

## 配套小工具

### rasm2 — 汇编/反汇编

```powershell
rasm2 -d "9090"
rasm2 -a x86 -b 64 "xor eax, eax"
```

### radiff2 — 二进制对比

```powershell
radiff2 old.exe new.exe
radiff2 -C old.exe new.exe
```

### rahash2 — 哈希

```powershell
rahash2 -a md5 sample.exe
rahash2 -a sha256 sample.exe
```

### rax2 — 进制/编码转换

```powershell
rax2 0x401000
rax2 4198400
rax2 -s hello
```
