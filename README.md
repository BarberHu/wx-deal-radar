# wx-deal-radar

本地优先的微信群好价雷达。它通过 `wx-cli` 读取本机微信增量消息，在 Streamlit GUI 中配置监控群、关键词、商品价格阈值和黑名单词，命中后进行 Windows 本地提醒并记录日志。

## 能力边界

- 本项目只做本地过滤、提醒和日志。
- 本项目不破解微信、不注入微信、不自动下单、不自动加群。
- 微信数据读取由用户自行配置的 `wx-cli` 完成。
- 命中结果只保存在本机 `data/hits.jsonl`。

## 快速启动

```powershell
cd /d E:\wx-deal-radar
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 当前 MVP

- 目标群白名单
- 全局关键词
- 商品关键词
- 价格阈值
- 黑名单词
- Windows 弹窗
- 本地 JSONL 命中日志
