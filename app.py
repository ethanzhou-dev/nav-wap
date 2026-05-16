from flask import Flask, Response, request, send_file, redirect
from flask_compress import Compress
import os
from datetime import datetime, timezone, timedelta
import threading
import urllib.request
import json
from pymongo import MongoClient

app = Flask(__name__)
Compress(app)

MONGO_URI = os.environ.get("MONGO_URI")
if not MONGO_URI:
    print("警告: 未设置 MONGO_URI 环境变量，数据库将无法连接！")

space_id_raw = os.environ.get("SPACE_ID", "default_space")
space_id_safe = space_id_raw.replace("/", "_").replace("-", "_").replace(".", "_")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["nav_sites_db"]
    nav_ips_collection = db[f"nav_ips_{space_id_safe}"]
    nav_meta_collection = db[f"nav_meta_{space_id_safe}"]
    print(f"成功连接到 MongoDB！当前数据库: nav_sites_db，隔离集合: {space_id_safe}")
except Exception as e:
    print(f"无法连接到 MongoDB: {e}")


def get_beijing_date():
    tz_bj = timezone(timedelta(hours=8))
    return datetime.now(tz_bj).date()


def get_greeting():
    tz_bj = timezone(timedelta(hours=8))
    hour = datetime.now(tz_bj).hour
    if 5 <= hour < 12:
        return "早上好，新的一天开始了"
    elif 12 <= hour < 18:
        return "下午好，喝杯茶休息下"
    elif 18 <= hour < 23:
        return "晚上好，欢迎来到本站"
    else:
        return "夜深了，注意保护视力"


def fetch_and_save_ip_location(ip):
    try:
        if (
            ip.startswith("127.")
            or ip.startswith("192.168.")
            or ip.startswith("10.")
            or ip.startswith("172.")
        ):
            try:
                nav_ips_collection.update_one(
                    {"_id": ip}, {"$set": {"location": "本地/局域网IP"}}
                )
            except Exception:
                pass
            return
        url = f"http://ip-api.com/json/{ip}?lang=zh-CN"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            location = "未知归属地"
            if data.get("status") == "success":
                location = f"{data.get('country', '')} {data.get('regionName', '')} {data.get('city', '')}".strip()

            try:
                nav_ips_collection.update_one(
                    {"_id": ip}, {"$set": {"location": location}}
                )
            except Exception:
                pass
    except Exception:
        try:
            nav_ips_collection.update_one(
                {"_id": ip}, {"$set": {"location": "查询超时或失败"}}
            )
        except Exception:
            pass


current_date = get_beijing_date()
ANNOUNCEMENT = "WAP AI站已更新，欢迎使用（具有搜索功能）"

try:
    meta = nav_meta_collection.find_one({"_id": "meta"})
    if meta:
        saved_date_str = meta.get("current_date")
        if saved_date_str != str(current_date):
            nav_ips_collection.delete_many({})
            nav_meta_collection.update_one(
                {"_id": "meta"},
                {"$set": {"current_date": str(current_date)}},
                upsert=True,
            )
    else:
        nav_meta_collection.insert_one(
            {"_id": "meta", "current_date": str(current_date)}
        )
except Exception as e:
    print(f"初始化数据库状态失败: {e}")

XHTML_CONTENT = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//WAPFORUM//DTD XHTML Mobile 1.0//EN" "http://www.wapforum.org/DTD/xhtml-mobile10.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN" lang="zh-CN">
    <head>
        <title>WAP导航页</title>
        <link rel="apple-touch-icon" href="/speeddial-icon.png?v=3" />
        <link rel="icon" type="image/png" sizes="128x128" href="/speeddial-icon.png?v=3" />
        <link rel="shortcut icon" href="/favicon.ico?v=3" type="image/x-icon" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=2.0, user-scalable=yes" />
        <style type="text/css">
            body { background-color: whitesmoke; color: black; margin: 0; padding: 0; }
            a { color: darkblue; text-decoration: none; }
            a:visited { color: darkblue; }
            a:hover { text-decoration: underline; }
            .header { background-color: #3B5998; color: white; padding: 4px 6px; font-weight: bold; }
            .content { padding: 6px; line-height: 1.5; }
            .content b { color: black; }
            hr { border: 0; border-bottom: 1px solid silver; margin: 6px 0; }
            .announce { background-color: lightyellow; border: 1px dashed goldenrod; padding: 4px; margin: 6px 0; color: darkorange; font-size: small; }
            .nav { background-color: gainsboro; padding: 6px; border-top: 1px solid silver; text-align: center; }
            .item { padding: 1px 1px; display: block; }
            .odd { background-color: lightgray; }
            .even { background-color: white; }
        </style>
    </head>
    <body>
        <div class="header">WAP导航页</div>
        <div class="content">
            <i>__GREETING__</i><br/>
            <small style="color: dimgray;">今日访客: __VISIT_COUNT__</small>

            <div style="margin: 8px 0; text-align: center; background-color: gainsboro; padding: 3px; border: 1px solid silver;">
                <form action="//wap.baidu.com/s" method="get" style="margin: 0; padding: 0;">
                    <input type="hidden" name="pu" value="sz@1321_1001" />
                    <input type="text" name="word" style="width: 50%;" align="absmiddle" />
                    <input type="submit" value="百度一下" align="absmiddle" />
                </form>
            </div>
            <hr/>
            <b>:: 社交互动 ::</b>
            <div class="item even">[1] <a href="/redirect?url=//qq.ekiz.top&amp;name=QQ群互通" accesskey="2">QQ群互通</a></div>
            <div class="item odd">[2] <a href="/redirect?url=//qq.ekiz.top/wml&amp;name=互通(WAP版)" accesskey="3">互通(WAP版)</a></div>
            <hr/>
            <b>:: 资讯生活 ::</b>
            <div class="item odd">[3] <a href="/redirect?url=//news.ekiz.top&amp;name=新闻网站" accesskey="4">新闻网站</a></div>
            <div class="item even">[4] <a href="/redirect?url=//weather.ekiz.top&amp;name=天气预报" accesskey="5">天气预报</a></div>
            <hr/>
            <b>:: 工具娱乐 ::</b>
            <div class="item odd">[5] <a href="/redirect?url=//ai.ekiz.top&amp;name=AI普通版(账密a)" accesskey="9">AI普通版</a></div>
            <div class="item even">[6] <a href="/redirect?url=//ai.ekiz.top/nokia&amp;name=AI(WAP版)" accesskey="0">AI(WAP版)</a></div>
        </div>
        <div class="nav">
            <small>浙ICP备08012345号-1</small><br/>
            <small>&copy; 2026 Ekiz WAP</small>
        </div>
    </body>
</html>
"""


@app.route("/")
def index():
    global current_date
    now_date = get_beijing_date()
    if now_date != current_date:
        current_date = now_date
        try:
            nav_ips_collection.delete_many({})
            nav_meta_collection.update_one(
                {"_id": "meta"},
                {"$set": {"current_date": str(current_date)}},
                upsert=True,
            )
        except Exception as e:
            print(f"清理跨天数据失败: {e}")

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip:
        ip = ip.split(",")[0].strip()
        try:
            result = nav_ips_collection.update_one(
                {"_id": ip},
                {"$inc": {"count": 1}, "$setOnInsert": {"location": "查询中..."}},
                upsert=True,
            )
            if result.upserted_id is not None:
                threading.Thread(target=fetch_and_save_ip_location, args=(ip,)).start()
        except Exception as e:
            print(f"数据库记录失败: {e}")

    try:
        visit_count = nav_ips_collection.count_documents({})
    except Exception:
        visit_count = 0

    accept_header = request.headers.get("Accept", "")
    if "application/vnd.wap.xhtml+xml" in accept_header:
        mimetype = "application/vnd.wap.xhtml+xml"
    elif "application/xhtml+xml" in accept_header:
        mimetype = "application/xhtml+xml"
    else:
        mimetype = "text/html"

    html_output = XHTML_CONTENT.replace("__VISIT_COUNT__", str(visit_count))
    html_output = html_output.replace("__NOTICE__", ANNOUNCEMENT)
    html_output = html_output.replace("__GREETING__", get_greeting())
    return Response(html_output, mimetype=mimetype)


@app.route("/redirect")
def redirect_to():
    url = request.args.get("url")
    name = request.args.get("name")
    if not url:
        return "Missing URL", 400

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip:
        ip = ip.split(",")[0].strip()
        if name:
            try:
                nav_ips_collection.update_one(
                    {"_id": ip}, {"$inc": {f"clicks.{name}": 1}}, upsert=True
                )
            except Exception as e:
                print(f"数据库记录点击失败: {e}")

    return redirect(url)


@app.route("/health")
def health():
    return "OK", 200


@app.route("/favicon.ico")
def favicon():
    if os.path.exists("favicon.ico"):
        return send_file("favicon.ico", mimetype="image/x-icon")
    return "", 404


@app.route("/speeddial-icon.png")
def speeddial_icon():
    if os.path.exists("speeddial-icon.png"):
        return send_file("speeddial-icon.png", mimetype="image/png")
    return "", 404


@app.route("/admin/ips")
def view_ips():
    try:
        cursor = nav_ips_collection.find()
        db_ips = {}
        for doc in cursor:
            db_ips[doc["_id"]] = {
                "location": doc.get("location", "未知"),
                "count": doc.get("count", 0),
                "clicks": doc.get("clicks", {}),
            }
        data = {
            "current_date": str(current_date),
            "total_visitors": len(db_ips),
            "source": "database",
            "ips": db_ips,
        }
    except Exception as e:
        data = {
            "current_date": str(current_date),
            "total_visitors": 0,
            "source": "error",
            "error": str(e),
            "ips": {},
        }
    return Response(
        json.dumps(data, ensure_ascii=False, indent=4),
        mimetype="application/json; charset=utf-8",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
