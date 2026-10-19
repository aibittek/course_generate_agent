# -*- coding: utf-8 -*-
"""
把 .urdf 包成可直接 <script src> 加载的 .js

为什么需要：课程页面要求"双击 html 就能看"（file:// 协议），
浏览器在 file:// 下禁止 fetch/XHR 读本地文本，所以 URDF 文本必须
以脚本形式内联进来。URDF 本身仍然是独立的 .urdf 文件（唯一事实源），
这个脚本只是给它生成一个 8 KB 的包装。

用法：
  python tools/urdf_to_js.py <输入.urdf> [输出.js]
不写输出时，默认生成同目录下的 <名字>.urdf.js
"""
import json
import os
import sys


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: python tools/urdf_to_js.py <input.urdf> [output.js]")
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src + ".js"

    text = open(src, encoding="utf-8").read()
    name = os.path.basename(src)

    out = (
        "/* 自动生成，勿手改 —— 源文件是本目录的 %s\n"
        "   改完 URDF 后重跑：python tools/urdf_to_js.py <path>/%s */\n"
        "window.URDF_ARM_TEXT = %s;\n" % (name, name, json.dumps(text, ensure_ascii=False))
    )
    open(dst, "w", encoding="utf-8").write(out)
    print("%s -> %s (%d bytes)" % (src, dst, len(out.encode("utf-8"))))


if __name__ == "__main__":
    main()
