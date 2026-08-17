# 自动化工作流

对本地原生工件使用包装脚本：

```powershell
python <skill>\scripts\cold_coffee_native_workflow.py <artifact.exe> --case-dir <case-dir> --dynamic
```

包装脚本只创建带时间戳的 run 目录。它会记录源哈希（前后各一次），动态作业前复制工件所在父目录，隐藏复制进程，每个有界探针结束后终止进程，并写出带各项返回码的清单。

不需要启动可执行文件时，省略 `--dynamic` 即走纯静态形态。
