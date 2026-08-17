#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,shutil
TOOLS={
"reverse":[("ghidra",["analyzeHeadless"]),("frida",["frida","frida-trace"]),("capa",["capa"])],
"malware-ir":[("capa",["capa"]),("volatility3",["vol","vol.py"])],
"memory":[("volatility3",["vol","vol.py"])],
"pentest":[("nuclei",["nuclei"]),("zaproxy",["zap.sh","zap.bat"])],
"api":[("zaproxy",["zap.sh","zap.bat"])],
"fuzzing":[("aflplusplus",["afl-fuzz"]),("clang",["clang"])],
"code-security":[("semgrep",["semgrep"]),("trivy",["trivy"]),("osv-scanner",["osv-scanner"])],
"supply-chain":[("trivy",["trivy"]),("osv-scanner",["osv-scanner"])],
"cloud-container":[("trivy",["trivy"]),("prowler",["prowler"])],
"scraper":[("scrapy",["scrapy"]),("playwright",["playwright"])],
"browser":[("playwright",["playwright"])],
"mobile":[("frida",["frida"]),("mobsf",["mobsfscan"])],
}
def main():
 p=argparse.ArgumentParser(); p.add_argument("--workflow",required=True); p.add_argument("--json",action="store_true"); a=p.parse_args(); out=[]
 for name,candidates in TOOLS.get(a.workflow,[]):
  found=next((shutil.which(c) for c in candidates if shutil.which(c)),None); out.append({"tool":name,"available":bool(found),"path":found,"candidates":candidates})
 print(json.dumps({"workflow":a.workflow,"tools":out},ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
