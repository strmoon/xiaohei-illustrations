#!/usr/bin/env python3
"""使用 OpenAI 兼容的 Image API 生成图片，无第三方 Python 依赖。"""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import sys
from typing import Any, NoReturn, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://codex.apiz.ai/"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "1280x720"
DEFAULT_QUALITY = "medium"
SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = SKILL_DIR / "assets" / "output.png"


def fail(message: str) -> NoReturn:
    print(f"错误：{message}", file=sys.stderr)
    raise SystemExit(1)


def auth_file_candidates(explicit_auth_file: Optional[Path]) -> list[Path]:
    if explicit_auth_file is not None:
        return [explicit_auth_file.expanduser()]

    candidates = []
    configured_file = os.environ.get("CODEX_AUTH_FILE", "").strip()
    if configured_file:
        candidates.append(Path(configured_file).expanduser())

    codex_home = os.environ.get("CODEX_HOME", "").strip()
    if codex_home:
        candidates.append(Path(codex_home).expanduser() / "auth.json")

    candidates.append(Path.home() / ".codex" / "auth.json")

    unique = []
    seen = set()
    for path in candidates:
        key = os.path.normcase(os.path.abspath(path))
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def load_api_key(explicit_auth_file: Optional[Path]) -> str:
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if env_key:
        return env_key

    candidates = auth_file_candidates(explicit_auth_file)
    errors = []
    for auth_file in candidates:
        try:
            auth = json.loads(auth_file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            continue
        except (OSError, json.JSONDecodeError) as exc:
            if explicit_auth_file is not None:
                fail(f"无法读取认证文件 {auth_file}：{exc}")
            errors.append(f"{auth_file}（无法读取：{exc}）")
            continue

        api_key = auth.get("OPENAI_API_KEY") if isinstance(auth, dict) else None
        if not isinstance(api_key, str) or not api_key.strip():
            if explicit_auth_file is not None:
                fail(f"认证文件缺少有效的 OPENAI_API_KEY：{auth_file}")
            errors.append(f"{auth_file}（缺少有效的 OPENAI_API_KEY）")
            continue
        return api_key.strip()

    checked = "、".join(str(path) for path in candidates)
    skipped = f"；已跳过：{'、'.join(errors)}" if errors else ""
    fail(
        "没有找到 API Key。请设置 OPENAI_API_KEY、CODEX_AUTH_FILE，"
        f"或使用 --auth-file 指定认证文件。已检查：{checked}{skipped}"
    )


def image_endpoint(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base.startswith(("http://", "https://")):
        fail("--base-url 必须以 http:// 或 https:// 开头")
    if base.endswith("/v1"):
        return f"{base}/images/generations"
    return f"{base}/v1/images/generations"


def read_prompt(prompt: Optional[str], prompt_file: Optional[Path]) -> str:
    if prompt and prompt_file:
        fail("--prompt 和 --prompt-file 不能同时使用")
    if prompt_file:
        try:
            value = prompt_file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            fail(f"无法读取提示词文件 {prompt_file}：{exc}")
    else:
        value = (prompt or "").strip()
    if not value:
        fail("请使用 --prompt 或 --prompt-file 提供提示词")
    return value


def parse_error_body(raw: bytes) -> str:
    text = raw.decode("utf-8", errors="replace").strip()
    if not text:
        return "服务没有返回错误详情"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text[:500]
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and isinstance(error.get("message"), str):
            return error["message"]
        if isinstance(error, str):
            return error
        if isinstance(payload.get("message"), str):
            return payload["message"]
    return text[:500]


def post_json(endpoint: str, api_key: str, payload: dict[str, Any], timeout: int) -> Any:
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "apiz-image-generator/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        fail(f"API 请求失败（HTTP {exc.code}）：{parse_error_body(exc.read())}")
    except URLError as exc:
        fail(f"无法连接图像服务：{exc.reason}")
    except TimeoutError:
        fail(f"请求超过 {timeout} 秒仍未完成")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        fail("图像服务返回了无效的 JSON")


def download_image(url: str, timeout: int) -> bytes:
    request = Request(url, headers={"User-Agent": "apiz-image-generator/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except HTTPError as exc:
        fail(f"下载生成图片失败（HTTP {exc.code}）")
    except URLError as exc:
        fail(f"下载生成图片失败：{exc.reason}")
    except TimeoutError:
        fail(f"下载生成图片超过 {timeout} 秒仍未完成")


def decode_image(item: Any, timeout: int) -> bytes:
    if not isinstance(item, dict):
        fail("图像服务返回的数据格式不正确")

    encoded = item.get("b64_json")
    if isinstance(encoded, str) and encoded:
        try:
            return base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            fail("图像服务返回了无效的 base64 图片数据")

    url = item.get("url")
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return download_image(url, timeout)
    fail("响应中既没有 b64_json，也没有可下载的图片 URL")


def output_paths(output: Path, count: int) -> list[Path]:
    if count == 1:
        return [output]
    suffix = output.suffix or ".png"
    stem = output.stem if output.suffix else output.name
    return [output.with_name(f"{stem}-{index}{suffix}") for index in range(1, count + 1)]


def validate_output_suffix(output: Path, output_format: str) -> None:
    allowed = {"jpeg": {".jpg", ".jpeg"}, "png": {".png"}, "webp": {".webp"}}
    if output.suffix.lower() not in allowed[output_format]:
        expected = "/".join(sorted(allowed[output_format]))
        fail(f"--out 的扩展名必须与 {output_format} 格式匹配：{expected}")


def write_images(items: list[Any], paths: list[Path], force: bool, timeout: int) -> None:
    if len(items) < len(paths):
        fail(f"请求生成 {len(paths)} 张图片，但服务只返回了 {len(items)} 张")
    existing = [path for path in paths if path.exists()]
    if existing and not force:
        fail(f"输出文件已存在：{existing[0]}（需要覆盖时添加 --force）")

    images = [decode_image(item, timeout) for item in items[: len(paths)]]
    for path, image in zip(paths, images):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(image)
        print(f"已保存：{path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="通过 https://codex.apiz.ai/ 的 OpenAI 兼容接口生成图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
Windows 示例：
  PowerShell:
    $env:OPENAI_API_KEY="你的密钥"
    py draw.py --prompt "一只小黑推动齿轮" --out output.png

  CMD:
    set OPENAI_API_KEY=你的密钥
    py draw.py --prompt "一只小黑推动齿轮" --out output.png

  使用任意位置的认证文件：
    py draw.py --auth-file "D:\config\auth.json" --prompt "一只小黑推动齿轮" --out output.png
""",
    )
    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", help="图片提示词")
    prompt_group.add_argument("--prompt-file", type=Path, help="UTF-8 提示词文件")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"模型，默认 {DEFAULT_MODEL}")
    parser.add_argument("--size", default=DEFAULT_SIZE, help=f"尺寸，默认 {DEFAULT_SIZE}")
    parser.add_argument(
        "--quality",
        choices=("low", "medium", "high", "auto"),
        default=DEFAULT_QUALITY,
        help=f"质量，默认 {DEFAULT_QUALITY}",
    )
    parser.add_argument("--n", type=int, choices=range(1, 11), default=1, metavar="1-10")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT, help="输出文件路径")
    parser.add_argument("--output-format", choices=("png", "jpeg", "webp"), default="png")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="OpenAI 兼容服务根地址")
    parser.add_argument(
        "--auth-file",
        type=Path,
        help="认证文件；默认按 CODEX_AUTH_FILE、CODEX_HOME、用户目录顺序查找",
    )
    parser.add_argument("--timeout", type=int, default=300, help="请求超时秒数，默认 300")
    parser.add_argument("--force", action="store_true", help="覆盖已有文件")
    parser.add_argument("--dry-run", action="store_true", help="只显示请求，不调用 API")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.timeout < 1:
        fail("--timeout 必须大于 0")

    endpoint = image_endpoint(args.base_url)
    prompt = read_prompt(args.prompt, args.prompt_file)
    validate_output_suffix(args.out, args.output_format)
    payload = {
        "model": args.model,
        "prompt": prompt,
        "n": args.n,
        "size": args.size,
        "quality": args.quality,
        "output_format": args.output_format,
    }
    paths = output_paths(args.out, args.n)

    if args.dry_run:
        print(
            json.dumps(
                {"endpoint": endpoint, "outputs": [str(path) for path in paths], **payload},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    api_key = load_api_key(args.auth_file)
    print(f"正在请求：{endpoint}", file=sys.stderr)
    response = post_json(endpoint, api_key, payload, args.timeout)
    if not isinstance(response, dict) or not isinstance(response.get("data"), list):
        fail("图像服务响应缺少 data 数组")
    write_images(response["data"], paths, args.force, args.timeout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
