# MolecularGUIBench-Dock CUA 联调需求

版本 0.1.0，Phase A Pose Diagnosis MVP。

## 目标

CUA 需要在固定云电脑中自主打开 PyMOL，观察蛋白质–配体 pose，识别 binding interface，判断物理合理性和 native-likeness，并保存结构化结果与 PyMOL session。Phase A 不要求实现 docking algorithm；Vina redocking 属于 Phase B。

## 必须提供的能力

1. 指定 desktop 后创建全新的 task，每个 episode 独立运行。
2. 接收完整 objective 文本并返回稳定 task/invocation ID。
3. 轮询并明确返回 `in_progress`、`completed`、`failed`、`cancelled`、`needs_input`。
4. `needs_input` 返回问题文本；benchmark 不自动回答，直接记为 `HUMAN_ASSIST_REQUIRED`。
5. 完成后返回结构化文本结果，并支持 artifact 列表和下载。
6. 提供模型版本、runtime 版本、时间戳和 desktop 标识。
7. 同一 desktop 同时只运行一个 benchmark task。

当前仓库适配官方 `byted-util-ark-cua` Skill 1.0.7 的 Python CLI。若内部接口不同，请提供等价映射和 JSON 示例。

## 云电脑环境

固定 image 至少包含 PyMOL、AutoDock-Vina、Python 3.10+，可打开 `.pdb`/`.sdf`/`.mol2`，可保存 `.pse`，可访问 episode public 目录和 `outputs/`，并固定屏幕分辨率、缩放比例和初始布局。Phase A 不要求访问 `data/private`；native ligand、native interface、PoseBusters 标签、RMSD 和 evaluator 只存在 Controller 侧。

## Episode 输入

目录包含 `episode.json`、`receptor.pdb`、`ligand.sdf`、`candidate_pose.sdf`。JSON 至少有 `schema_version`、`episode_id`、`target_id`、`task=diagnosis`、`track=vision_only`、三个相对路径和 `objective`。文件名和 target ID 已匿名化。CUA 不应访问外部网络、PDB 数据库、native ligand 或 private ground truth。

## Phase A objective

```text
Inspect the protein–ligand complex in the provided episode using PyMOL.
Identify the protein residues that directly form the observed ligand-binding interface.
Judge whether the candidate ligand pose is physically plausible and whether it appears native-like.
Record any apparent clash, strain, missing contact, or other failure mode.
Create a PyMOL selection named `agent_interface` containing the interface residues.
Save the final PyMOL session as `outputs/final.pse`.
Write a structured answer containing interface residue identifiers, physical plausibility,
native-likeness, confidence, and failure notes. Do not access external resources.
```

## 完成结果

成功 task 至少需要 structured answer、`outputs/final.pse`、`agent_interface` selection；导出的 ligand 必须位于 `outputs/`。建议 answer 字段为 `interface_residues`、`physical_plausibility`、`native_likeness`、`confidence`、`failure_notes`。

## 最小验收用例

| 用例 | 预期 |
|---|---|
| health | 返回 desktop、PyMOL、artifact 版本和路径，不创建长期 task |
| diagnosis_easy | completed、selection、final.pse |
| diagnosis_invalid | `physical_plausibility=no` 或 `uncertain` |
| needs_input | 返回 needs_input，不自动代答 |

请附脱敏 request、status、result schema 和 artifact metadata 示例，并确认 task 参数、`next.command`、needs_input、artifact 流程、desktop 稳定周期/并发限制、版本查询、网络隔离、失败和超时错误码。

## 安全边界

API key 不得出现在聊天、objective、episode、result 或日志中。认证使用 ARK CLI profile 或官方 Skill 保护流程。Controller 只保存脱敏 task metadata 和 evaluator 结果。

## 仓库材料

`src/pymoldock_bench/schemas/`、`src/pymoldock_bench/cua/ark_client.py`、`src/pymoldock_bench/runner/`、`src/pymoldock_bench/eval/`、`pymol_plugin/pymoldockbench/` 和 `docs/CUA_INTERFACE.md`。

## Hands-on 测试步骤

对接团队拿到仓库后，可按以下顺序验收：

1. `pip install -e '.[dev,docking]'`，运行 `pytest -q`；预期所有测试通过。
2. 运行 `python scripts/check_environment.py`；记录 Python、PyMOL、Vina、arkcli 版本。

## 本机依赖与联调工具

Controller 侧建议使用 Python 3.10+、RDKit、Pydantic、PyYAML、NumPy、PoseBusters、Meeko 和 Gemmi。
Phase B 还需要 Open Babel（命令 `obabel`）或 Meeko 的 `mk_prepare_*` 工具，将 PDB/SDF 转为
Vina 所需的 PDBQT；禁止用文本拼接伪造 PDBQT。Vina 1.1.2 与 PyMOL 必须在联调 desktop
中可执行。仓库提供 `scripts/prepare_pdbqt.py` 作为 Meeko 包装器，Open Babel 可作为人工
或 desktop-side fallback。

本机已验证的安装位置：

```text
PyMOL: /Users/judy/project/miniconda3/bin/pymol
Vina:  /Users/judy/project/autodock_vina_1_1_2/bin/vina
Open Babel: /Users/judy/project/miniconda3/bin/obabel
```

联调顺序：先运行 `python scripts/check_environment.py`，再用 `data/public/dev` 的一个
episode 准备 PDBQT，确认 Vina 输出和 PyMOL 可加载；最后才启动 Ark CUA。CUA workspace
只能挂载 `data/public` 和 episode 输出目录，不能挂载 `data/private`。

PoseBusters test selection 使用 `scripts/select_posebusters_test.py` 生成确定性 308-case
索引。该索引及 native/ground-truth 文件必须放在 `data/private/test` 或外部受控存储，
不能提交到仓库或复制到 CUA workspace。
3. 使用 `scripts/build_episodes.py` 生成 `DEMO_0001`，用 `scripts/run_episode.py` 做 offline smoke。
4. 用 `scripts/evaluate_episode.py` 评估 demo submission；正确的 demo label 应得到 interface F1 1.0、task success true。
5. 在 CUA desktop 上依次运行 `health`、`diagnosis_easy`、`diagnosis_invalid`、`needs_input`，每个 case 创建新 task。

最小 offline 命令示例：

```bash
python scripts/build_episodes.py /tmp/pymoldock-demo/source.json /tmp/pymoldock-demo/episode.json --episode-id DEMO_0001 --target-id DEMO
python scripts/run_episode.py /tmp/pymoldock-demo/episode.json --submission /tmp/pymoldock-demo/submission.json
python scripts/evaluate_episode.py /tmp/pymoldock-demo/episode.json /tmp/pymoldock-demo/submission.json /tmp/pymoldock-demo/ground_truth.json
```

`diagnosis_easy` 的成功证据是 `completed`、structured answer、
`outputs/final.pse` 和 `agent_interface` selection。`diagnosis_invalid` 应报告
`physical_plausibility=no` 或 `uncertain`。`needs_input` 必须停在
`HUMAN_ASSIST_REQUIRED`，不能由 Controller 代答。每个 case 的日志只保留
脱敏 task ID、状态、版本和 artifact metadata。
