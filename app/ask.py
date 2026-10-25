"""第1回: 素のLLMに1回だけ質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

ツールも会話履歴も持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
COMPARE_MODELS = (
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemma-4-26b-a4b-it",
    "gemini-flash-lite-latest",
)


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    usage = response.usage_metadata
    print(f"[トークン数] 入力: {usage.prompt_token_count} / 出力: {usage.candidates_token_count}")

    return response.text


def compare(question: str) -> None:
    """同じ質問を利用可能な生成モデルで実行し、性能を比較する。"""
    client = genai.Client(api_key=get_api_key())

    print("[比較結果]")
    print("モデル\t出力トークン数\t応答時間(秒)\ttokens/sec")
    skipped_models = 0
    outputs = []
    for model_name in COMPARE_MODELS:
        started_at = time.perf_counter()
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=question,
            )
            elapsed = time.perf_counter() - started_at
            usage = response.usage_metadata
            output_tokens = usage.candidates_token_count if usage else None
            if output_tokens is None:
                output_tokens_display = "計測不可"
                tokens_per_second_display = "計測不可"
            else:
                output_tokens_display = str(output_tokens)
                tokens_per_second_display = f"{output_tokens / elapsed:.2f}" if elapsed else "0.00"
            print(
                f"{model_name}\t{output_tokens_display}\t{elapsed:.2f}\t"
                f"{tokens_per_second_display}"
            )
            outputs.append((model_name, response.text or "（出力なし）"))
        except errors.APIError as e:
            skipped_models += 1

    if outputs:
        print("\n[各モデルのoutput]")
        for model_name, output in outputs:
            print(f"\n--- {model_name} ---")
            print(output)

    if skipped_models:
        print(f"\n{skipped_models} 個のモデルは利用できなかったため比較から除外しました。")


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("--compare", action="store_true", help="利用可能なモデルを比較する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[質問] {args.question}\n")
    try:
        if args.compare:
            compare(args.question)
        else:
            print(f"[model] {MODEL}")
            print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
