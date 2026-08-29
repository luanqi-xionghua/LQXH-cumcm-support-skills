# -*- coding: utf-8 -*-
"""smoke_test_review.py — paper-review CUMCM 冒烟自检（v2.1，自包含）
验证：① 旧 schema(numbers-list) 兼容；② 嵌套 dict schema；③ FROZEN-SCHEMA 空查必报；
④ IMG-REF-MISSING 图片缺失触发；⑤ CUMCM 默认 AI-LOG-MISSING 触发；
⑥ --no-ai-log-check 可关闭；⑦ 真实包回归（提供 --frozen 时）。
用法: python smoke_test_review.py [--pdf <真实论文PDF>] [--frozen <真实frozen>]
不传 --pdf 时自动用 fitz 生成合成论文 PDF（自包含，无需真实论文）。
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "review_paper.py"


def make_synthetic_pdf(out_path):
    """用 fitz 生成一页合成论文（含 摘要/关键词/数值 0.824），供自包含测试"""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "摘要：本文提出一种方法，AUC = 0.824。", fontsize=12)
    page.insert_text((72, 100), "关键词：评审测试；合成论文", fontsize=12)
    page.insert_text((72, 128), "1 引言 这是用于 paper-review 冒烟测试的合成论文正文。", fontsize=12)
    doc.save(str(out_path))
    doc.close()
    return out_path


def run(directory, pdf, frozen=None, expect_issues=(), extra=()):
    cmd = [sys.executable, str(SCRIPT), "--dir", str(directory), "--pdf", str(pdf), "--json"] + list(extra)
    if frozen:
        cmd += ["--frozen", str(frozen)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        out = json.loads(r.stdout)
    except Exception:
        return False, "JSON 解析失败: %s" % (r.stdout or r.stderr)[:200]
    kinds = [k for k, _ in out.get("issues", [])]
    ok = all(e in kinds for e in expect_issues)
    return ok, "kinds=%s" % kinds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", help="真实论文 PDF（可选；用于真实包回归，不传则生成合成 PDF）")
    ap.add_argument("--frozen", help="真实 frozen_numbers.json（可选，用于 ②⑦）")
    args = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="paper_review_smoke_"))
    results = []
    try:
        # 主 PDF：真实或合成
        if args.pdf:
            pdf = Path(args.pdf)
        else:
            pdf = make_synthetic_pdf(tmp / "synthetic_paper.pdf")

        # ① 旧 schema numbers-list（值 0.824 应出现在论文中）
        d1 = tmp / "pkg_numbers_list"
        d1.mkdir(parents=True)
        (d1 / "frozen_numbers.json").write_text(
            json.dumps({"numbers": [{"id": "T1", "key": "AUC", "value": 0.824, "verified": True}]}),
            encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "--dir", str(d1), "--pdf", str(pdf),
                            "--frozen", str(d1 / "frozen_numbers.json"), "--json", "--no-consistency"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        o = json.loads(r.stdout)
        s = o["pdf_check"]["stats"]
        results.append(("① numbers-list 旧 schema 兼容", s.get("frozen_schema") == "numbers-list" and s.get("frozen_missing_in_pdf") == 0,
                        "schema=%s missing=%s" % (s.get("frozen_schema"), s.get("frozen_missing_in_pdf"))))

        # ② 嵌套 dict schema（真实 frozen）
        if args.frozen:
            d2 = tmp / "pkg_nested"
            d2.mkdir(parents=True)
            shutil.copy(args.frozen, d2 / "frozen_numbers.json")
            r = subprocess.run([sys.executable, str(SCRIPT), "--dir", str(d2), "--pdf", str(pdf),
                                "--frozen", str(d2 / "frozen_numbers.json"), "--json", "--no-consistency"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            o = json.loads(r.stdout)
            s = o["pdf_check"]["stats"]
            results.append(("② 嵌套 dict schema 执行数字检查", s.get("frozen_schema") == "nested-dict" and s.get("frozen_sampled", 0) > 0,
                            "schema=%s sampled=%s missing=%s" % (s.get("frozen_schema"), s.get("frozen_sampled"), s.get("frozen_missing_in_pdf"))))

        # ③ FROZEN-SCHEMA 空查必报（frozen 为空 dict）
        d3 = tmp / "pkg_empty"
        d3.mkdir(parents=True)
        (d3 / "frozen_numbers.json").write_text("{}", encoding="utf-8")
        ok, info = run(d3, pdf, d3 / "frozen_numbers.json", expect_issues=("FROZEN-SCHEMA",), extra=("--no-consistency",))
        results.append(("③ FROZEN-SCHEMA 空查必报", ok, info))

        # ④ IMG-REF-MISSING（tex 引用不存在的图）+ ⑤ CUMCM 默认 AI-LOG-MISSING
        d4 = tmp / "pkg_img"
        d4.mkdir(parents=True)
        paper = d4 / "paper"
        paper.mkdir(parents=True)
        (paper / "test.tex").write_text("\\includegraphics{figures/fig_missing_xx.png}\n", encoding="utf-8")
        ok, info = run(d4, pdf, expect_issues=("IMG-REF-MISSING",), extra=("--no-consistency",))
        results.append(("④ IMG-REF-MISSING 图片缺失触发", ok, info))

        ok, info = run(d4, pdf, expect_issues=("AI-LOG-MISSING",), extra=("--no-consistency",))
        results.append(("⑤ CUMCM 默认 AI-LOG-MISSING 触发", ok, info))

        # ⑥ 可选关闭：传 --no-ai-log-check 后不应报 AI-LOG-MISSING
        r = subprocess.run([sys.executable, str(SCRIPT), "--dir", str(d4), "--pdf", str(pdf), "--json", "--no-consistency", "--no-ai-log-check"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        kinds = [k for k, _ in json.loads(r.stdout).get("issues", [])]
        results.append(("⑥ --no-ai-log-check 可关闭 AI 检查", "AI-LOG-MISSING" not in kinds, "kinds=%s" % kinds))

        # ⑦ 真实包回归（提供 --frozen 时）：真实论文 + 真实 frozen 无 FROZEN-SCHEMA
        if args.frozen and args.pdf:
            real = Path(args.pdf).resolve().parents[1]
            r = subprocess.run([sys.executable, str(SCRIPT), "--dir", str(real), "--pdf", str(args.pdf),
                                "--frozen", str(args.frozen), "--json", "--no-consistency"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            o = json.loads(r.stdout)
            kinds = [k for k, _ in o.get("issues", [])]
            ok = "FROZEN-SCHEMA" not in kinds and "IMG-REF-MISSING" not in kinds
            results.append(("⑦ 真实包回归：无 FROZEN-SCHEMA/IMG-REF-MISSING", ok, "kinds=%s" % kinds))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("===== paper-review smoke test =====")
    failed = 0
    for name, ok, info in results:
        print("  [%s] %s — %s" % ("PASS" if ok else "FAIL", name, info))
        if not ok:
            failed += 1
    print("结论: %s" % ("ALL PASSED" if failed == 0 else "%d FAILED" % failed))
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
