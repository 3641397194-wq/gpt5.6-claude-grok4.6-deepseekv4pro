# GitHub 官方工作流来源目录

审阅并锁定时间：2026-07-14。只收录方法适配，不 vendor 上游仓库。

| 来源 | 工作流 | 许可证 | 锁定 commit |
|---|---|---|---|
| [ghidra](https://github.com/NationalSecurityAgency/ghidra) | reverse | Apache-2.0 | b2754160215c |
| [frida](https://github.com/frida/frida) | reverse, crack, mobile | Repository COPYING | fdd722a99100 |
| [capa](https://github.com/mandiant/capa) | reverse, malware-ir | Apache-2.0 | f850024b5604 |
| [volatility3](https://github.com/volatilityfoundation/volatility3) | memory, malware-ir | Volatility Software License | d61335e2a549 |
| [nuclei](https://github.com/projectdiscovery/nuclei) | pentest | MIT | 9c47e6c12241 |
| [nuclei-templates](https://github.com/projectdiscovery/nuclei-templates) | pentest | MIT | a5c2e8e4dab8 |
| [owasp-asvs](https://github.com/OWASP/ASVS) | pentest, api, architecture | CC-BY-SA-4.0 | 122d9e096946 |
| [owasp-wstg](https://github.com/OWASP/wstg) | pentest, api | CC-BY-SA-4.0 | 78e6b6733ee0 |
| [zaproxy](https://github.com/zaproxy/zaproxy) | pentest, api | Apache-2.0 | 0309ae8d88a2 |
| [oss-fuzz](https://github.com/google/oss-fuzz) | fuzzing | Apache-2.0 | 1062c7475796 |
| [aflplusplus](https://github.com/AFLplusplus/AFLplusplus) | fuzzing | Apache-2.0 | ad5304010ae3 |
| [semgrep](https://github.com/semgrep/semgrep) | code-security, software | LGPL-2.1 | 1d1202792202 |
| [trivy](https://github.com/aquasecurity/trivy) | cloud-container, supply-chain, code-security | Apache-2.0 | f06520353fc6 |
| [osv-scanner](https://github.com/google/osv-scanner) | supply-chain, code-security, software | Apache-2.0 | c4a9148518fc |
| [scrapy](https://github.com/scrapy/scrapy) | scraper | BSD-3-Clause | d8ba1571e714 |
| [playwright-python](https://github.com/microsoft/playwright-python) | scraper, browser | Apache-2.0 | bd499b293b93 |
| [prowler](https://github.com/prowler-cloud/prowler) | cloud-container | Apache-2.0 | 9822fd97d76b |
| [mobsf](https://github.com/MobSF/Mobile-Security-Framework-MobSF) | mobile | GPL-3.0 | 62563ca429a7 |

## 使用说明

- 按工作流关键词过滤本表，配合 `scripts/source_catalog.py`
- 安装上游工具时使用锁定 commit 或稳定 release
- 许可证与项目的兼容性在引入前确认
