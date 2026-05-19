from __future__ import annotations

import streamlit as st

from app.config import AppConfig, ProductRule, load_config, save_config
from app.monitor import DealMonitor, load_hits
from app.wx_client import WxClient


st.set_page_config(page_title="wx-deal-radar", page_icon="🛒", layout="wide")


def lines_to_list(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def list_to_lines(items: list[str]) -> str:
    return "\n".join(items)


def ensure_monitor(config: AppConfig) -> DealMonitor:
    monitor = st.session_state.get("monitor")
    if not monitor or monitor.config.to_dict() != config.to_dict():
        if monitor:
            monitor.stop()
        monitor = DealMonitor(config)
        st.session_state["monitor"] = monitor
    return monitor


def reset_monitor() -> None:
    monitor = st.session_state.get("monitor")
    if monitor:
        monitor.stop()
    st.session_state.pop("monitor", None)


config = load_config()
st.title("wx-deal-radar")
st.caption("本地微信群好价雷达：指定群 + 商品规则 + 价格阈值 + 黑名单词。")

with st.sidebar:
    st.header("运行状态")
    monitor = ensure_monitor(config)
    st.write("状态：", "运行中" if monitor.running() else "未运行")
    if monitor.last_check:
        st.write("上次检查：", monitor.last_check)
    if monitor.last_error:
        st.error(monitor.last_error)

    col_a, col_b = st.columns(2)
    if col_a.button("启动监控", use_container_width=True):
        monitor.start()
        st.rerun()
    if col_b.button("停止监控", use_container_width=True):
        monitor.stop()
        st.rerun()

    if st.button("单次扫描", use_container_width=True):
        hits = monitor.scan_once()
        st.success(f"本次命中 {len(hits)} 条")

page = st.tabs(["监控配置", "商品规则", "命中日志", "微信状态"])

with page[0]:
    st.subheader("基础配置")
    wx_exe = st.text_input("wx.exe 路径", value=config.wx_exe)
    col1, col2, col3 = st.columns(3)
    poll_interval = col1.number_input(
        "轮询间隔（秒）",
        min_value=5,
        max_value=600,
        value=config.poll_interval_seconds,
        step=5,
    )
    new_message_limit = col2.number_input(
        "每次读取新消息上限",
        min_value=20,
        max_value=1000,
        value=config.new_message_limit,
        step=20,
    )
    enable_notify = col3.toggle("Windows 弹窗提醒", value=config.enable_windows_notify)

    st.subheader("监控范围")
    groups_text = st.text_area(
        "目标群（每行一个，支持模糊匹配）",
        value=list_to_lines(config.target_groups),
        height=140,
    )
    keywords_text = st.text_area(
        "全局关键词（每行一个）",
        value=list_to_lines(config.global_keywords),
        height=140,
    )
    blacklist_text = st.text_area(
        "黑名单词（命中则不提醒，每行一个）",
        value=list_to_lines(config.blacklist_words),
        height=120,
    )

    if st.button("保存基础配置", type="primary"):
        updated = AppConfig(
            wx_exe=wx_exe,
            poll_interval_seconds=int(poll_interval),
            new_message_limit=int(new_message_limit),
            enable_windows_notify=enable_notify,
            target_groups=lines_to_list(groups_text),
            global_keywords=lines_to_list(keywords_text),
            blacklist_words=lines_to_list(blacklist_text),
            products=config.products,
        )
        save_config(updated)
        reset_monitor()
        st.success("已保存配置，并停止旧监控线程。请重新启动监控。")
        st.rerun()

with page[1]:
    st.subheader("商品 + 价格阈值")
    st.caption(
        "逻辑：商品关键词命中后，如果识别到价格且低于阈值，就提醒；"
        "未识别价格时也会提醒你人工确认。取消勾选“保留这条规则”并保存即可删除。"
    )
    products: list[ProductRule] = []
    for index, product in enumerate(config.products):
        with st.expander(product.name or f"商品规则 {index + 1}", expanded=True):
            keep_rule = st.checkbox("保留这条规则", value=True, key=f"keep_{index}")
            name = st.text_input("商品名", value=product.name, key=f"name_{index}")
            keywords = st.text_area(
                "商品关键词（每行一个）",
                value=list_to_lines(product.keywords),
                key=f"kw_{index}",
            )
            max_price = st.number_input(
                "最高提醒价",
                min_value=0.0,
                value=float(product.max_price or 0),
                step=10.0,
                key=f"price_{index}",
            )
            if keep_rule:
                products.append(
                    ProductRule(
                        name=name,
                        keywords=lines_to_list(keywords),
                        max_price=max_price or None,
                    )
                )

    with st.expander("新增商品规则"):
        new_name = st.text_input("新商品名")
        new_keywords = st.text_area("新商品关键词（每行一个）")
        new_price = st.number_input("新商品最高提醒价", min_value=0.0, value=0.0, step=10.0)

    if st.button("保存商品规则", type="primary"):
        if new_name.strip() and lines_to_list(new_keywords):
            products.append(ProductRule(new_name.strip(), lines_to_list(new_keywords), new_price or None))
        updated = config
        updated.products = [p for p in products if p.name.strip() and p.keywords]
        save_config(updated)
        reset_monitor()
        st.success("已保存商品规则，并停止旧监控线程。请重新启动监控。")
        st.rerun()

with page[2]:
    st.subheader("命中日志")
    rows = load_hits(limit=300)
    if not rows:
        st.info("暂无命中。启动监控或单次扫描后会在这里显示。")
    else:
        st.dataframe(rows, use_container_width=True, height=520)

with page[3]:
    st.subheader("微信状态")
    st.caption("这里只读取会话名和摘要，用来确认 wx-cli 链路正常。")
    if st.button("读取最近会话"):
        try:
            sessions = WxClient(config.wx_exe).sessions(limit=50)
            st.dataframe(sessions, use_container_width=True, height=520)
        except Exception as exc:
            st.error(str(exc))
