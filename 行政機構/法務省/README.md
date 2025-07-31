# 法務省

出典: https://www.cas.go.jp/jp/gaiyou/jimu/jinjikyoku/satei_01_05.html

```mermaid
flowchart TB
  root["法務省"]
  subgraph g0["内部部局"]
    n0_0["大臣官房"]
    n0_1["民事局"]
    n0_2["刑事局"]
    n0_3["矯正局"]
    n0_4["保護局"]
    n0_5["人権擁護局"]
    n0_6["訟務局"]
  end
  root --> g0
  subgraph g1["外局"]
    n1_0["出入国在留管理庁"]
    n1_1["公安審査委員会"]
    n1_2["公安調査庁"]
  end
  root --> g1
  subgraph g2["特別の機関"]
    n2_0["検察庁"]
  end
  root --> g2
```
