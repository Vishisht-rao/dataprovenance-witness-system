import argparse
import json
import os
import re

def norm_text(s: str) -> str:
    s = "" if s is None else str(s)
    return re.sub(r"\s+", " ", s).strip()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("survey_id")
    parser.add_argument("--base_url", default="https://cmu.yul1.qualtrics.com")
    args = parser.parse_args()
    survey_id = args.survey_id
    out_dir = os.path.join("outputs", survey_id)
    os.makedirs(out_dir, exist_ok=True)

    out = []
    with open(os.path.join(out_dir, f"{survey_id}_srr.jsonl"), "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            rec = obj.get("record", obj)

            response_id = rec.get("response_id", "")

            answers_raw = rec.get("answers", {})
            answers = {}
            for qid, blob in answers_raw.items():
                if isinstance(blob, dict) and "answer_text" in blob:
                    answers[qid] = norm_text(blob["answer_text"])
                else:
                    answers[qid] = norm_text(blob)

            answers = {k: answers[k] for k in sorted(answers.keys())}
            out.append({"response_id": response_id, "answers": answers})

    out.sort(key=lambda x: x["response_id"])

    with open(os.path.join(out_dir, f"{survey_id}_canonical.jsonl"), "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n")

    print(f"wrote outputs/{survey_id}/{survey_id}_canonical.jsonl count:", len(out))
    if out:
        print("sample:", out[0])

if __name__ == "__main__":
    main()
