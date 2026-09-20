# MolecularGUIBench-Dock

An offline-first benchmark for PyMOL protein–ligand pose diagnosis and interface
reasoning. Phase A provides schemas, leakage-safe data boundaries, deterministic
geometry/interface metrics, a Mock CUA, and an adapter for the official ARK CUA
CLI. Phase B docking integration is intentionally kept behind the future plugin
backend until Phase A is validated.

## Quickstart

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest
ruff check .
python scripts/check_environment.py
```

Real CUA requires the official skill and protected authentication; see
`docs/CUA_INTERFACE.md`. Ground truth belongs under `data/private` and is never
copied into episode objectives or public artifacts.

## Data preparation

The Phase A paper archive is published by PoseBusters on Zenodo. Download it to
`data/raw/posebusters` and verify the published MD5 before extraction:

```bash
python scripts/prepare_data.py \
  --url https://zenodo.org/api/records/8278563/files/posebusters_paper_data.zip/content \
  --output data/raw/posebusters/posebusters_paper_data.zip
python scripts/prepare_posebusters.py \
  data/raw/posebusters/posebusters_paper_data.zip \
  data/raw/posebusters/extracted \
  --skip-md5
```

The archive is raw source material. A later curation step creates anonymized
public episodes and evaluator-only private labels; extraction alone does not
publish any ground truth.

## Hands-on 联调测试指南

下面的流程不需要真实 API key，也不需要先连接云电脑；它先验证仓库和
evaluator，再把同一个 episode 交给 CUA。所有命令均在仓库根目录执行。

### 1. 安装和环境检查

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python scripts/check_environment.py
pytest -q
```

预期：测试全部通过。`pymol=False`、`vina=False` 或 `arkcli=False` 只表示
对应真实集成尚未安装，不影响离线 evaluator 测试。

### 2. 生成最小离线 episode

```bash
mkdir -p /tmp/pymoldock-demo
printf 'ATOM\n' > /tmp/pymoldock-demo/receptor.pdb
printf 'demo\n' > /tmp/pymoldock-demo/ligand.sdf
python - <<'PY'
import json
from pathlib import Path
p = Path('/tmp/pymoldock-demo/source.json')
p.write_text(json.dumps({'receptor_path': str(p.parent/'receptor.pdb'), 'ligand_path': str(p.parent/'ligand.sdf')}))
PY
python scripts/build_episodes.py /tmp/pymoldock-demo/source.json /tmp/pymoldock-demo/episode.json --episode-id DEMO_0001 --target-id DEMO
```

### 3. 运行 offline/mock smoke

```bash
python scripts/run_episode.py /tmp/pymoldock-demo/episode.json \
  --output /tmp/pymoldock-demo/submission.json
```

预期生成合法 `Submission`，状态为 `failed`（因为没有 agent answer），且
不会伪造成功。准备一个答案后再运行：

```bash
cat > /tmp/pymoldock-demo/submission.json <<'JSON'
{"episode_id":"DEMO_0001","status":"completed","interface_residues":["A:42"],"physical_plausibility":"yes","native_likeness":"yes","confidence":0.8}
JSON
python scripts/run_episode.py /tmp/pymoldock-demo/episode.json \
  --submission /tmp/pymoldock-demo/submission.json
```

### 4. 评估一个 diagnosis case

```bash
cat > /tmp/pymoldock-demo/ground_truth.json <<'JSON'
{"episode_id":"DEMO_0001","interface_residues":["A:42"],"pb_valid":true,"native_like":true}
JSON
python scripts/evaluate_episode.py \
  /tmp/pymoldock-demo/episode.json \
  /tmp/pymoldock-demo/submission.json \
  /tmp/pymoldock-demo/ground_truth.json
```

预期 JSON 中 `interface_f1=1.0`、`task_success=true`、
`pb_valid_correct=true`、`native_like_correct=true`。

### 5. CUA 联调四个固定 case

| case | 操作 | 预期结果 |
|---|---|---|
| `health` | 查询 desktop、PyMOL、artifact 和模型版本 | 只读成功，返回版本和路径，不产生长期 episode |
| `diagnosis_easy` | 提供正确 pose 和简单界面，发送标准 objective | `completed`；返回 structured answer；产生 `outputs/final.pse`；存在 `agent_interface` |
| `diagnosis_invalid` | 将 ligand 平移到明显 clash 的位置 | 仍然 `completed`；`physical_plausibility` 为 `no` 或 `uncertain`；保留失败说明 |
| `needs_input` | 使用会触发澄清问题的 mock task | `needs_input`，Controller 映射为 `HUMAN_ASSIST_REQUIRED`，不自动回答 |

每个 case 都必须使用全新 task；同一 desktop 不并发。测试日志只能包含脱敏
的 task ID、状态、模型版本和 artifact metadata，不能包含 API key。

### 6. 真实 CUA 前置检查

```bash
arkcli --version
python3 .agents/skills/byted-util-ark-cua/scripts/cua.py auth status
```

如果返回 `AUTH_REQUIRED`，请在本机真实终端执行 Skill 返回的
`setup_command`，通过隐藏输入完成登录；不要把 key 粘贴到聊天、objective
或仓库文件。认证完成后先运行 `health`，再运行 `diagnosis_easy`。
