# deltacfs

一个 Python 外壳程序，用于编排 **PSGRN/PSCMP** Fortran 代码，从地震震源模型计算库仑应力变化（ΔCFS）。

## 概述

`deltacfs` 自动化了一个多深度、多阶段的流程。所有功能均可通过单一交互式入口访问：

```bash
python3 main.py
```

流程包含五个阶段：

1. **格林函数** — 生成 PSGRN 输入文件并运行 `fomosto_psgrn2008a`，为每个观测深度计算层状地球模型的弹性格林函数。
2. **库仑应力** — 生成 PSCMP 输入文件并运行 `fomosto_pscmp2008a`，在每个深度计算接收断层面上的库仑应力变化（ΔCFS）。
3. **后处理** — 将各深度的快照输出合并到 `output/`，并写出 GMT 兼容的 XYZ 数据。
4. **绘图** — 通过 GMT 渲染 CMB_Fix 的断层面剖面图。
5. **清理** — 删除生成的 `temp/`、`logs/` 和 `output/` 目录。

每个阶段在运行时可独立切换（计算阶段为 `y` / `no-override` / `n`；绘图和清理为 `y` / `n`）。

## 环境配置

### 1. 克隆并进入项目

```bash
git clone <repo-url> deltacfs
cd deltacfs
```

### 2. Python 环境

需要 Python 3.12+。使用 conda：

```bash
conda create -n deltacfs python=3.12 -y
conda activate deltacfs
pip install -r requirements.txt
```

唯一的外部 Python 依赖是 `pyproj==3.7.0`。其余所有模块均来自标准库。

验证：

```bash
python3 -c "import pyproj; print('pyproj', pyproj.__version__)"
```

### 3. Fortran 可执行文件（PSGRN / PSCMP）

流程会调用 `fomosto_psgrn2008a` 和 `fomosto_pscmp2008a`。这两个文件必须位于 `$PATH` 中。

验证：

```bash
which fomosto_psgrn2008a fomosto_pscmp2008a
```

如果你是从源码构建的（例如 `fomosto-psgrn-pscmp` 仓库），请确保安装前缀的 `bin/` 目录在 `$PATH` 中，或将可执行文件软链接到 `/usr/local/bin/`。

### 4. GMT 6（可选 — 绘图阶段需要）

必须安装 GMT 6 且 `gmt` 可执行文件在 `$PATH` 中。

验证：

```bash
gmt --version
```

### 5. Ghostscript（可选 — PS 转 PDF 需要）

验证：

```bash
gs --version
```

没有 Ghostscript 时，绘图阶段会生成 `.ps` 文件，但不会将其转换为 `.pdf`。

## 快速开始

```bash
# 交互式运行 — 选择要执行的阶段
python3 main.py
```

启动后会显示：

```
Setup all files in config/ before running.
Phases available:
  1. Green's function computation   (PSGRN)
  2. Coulomb stress computation      (PSCMP)
  3. After-process                   (merge outputs)
  4. Plot Coulomb cross-section      (GMT)
  5. Clean generated files           (temp/ logs/ output/)

Run phase 1 — Green's function set? (y/no-override/n):
Run phase 2 — Coulomb stress ΔCFS? (y/no-override/n):
Run phase 3 — after-process? (y/no-override/n):
Run phase 4 — plot Coulomb cross-section? (y/n):
Run phase 5 — clean generated files? (y/n):
```

有效响应：

| 响应 | 含义 |
|------|------|
| `y` | 覆盖已有数据并运行 |
| `no-override` | 仅在输出不存在时运行 |
| `n` | 跳过此阶段 |

## 项目结构

```
deltacfs/
├── main.py              # 统一入口 — 全部五个阶段
├── src/
│   ├── constant.py      # 绝对路径常量、验证器
│   ├── settings.py      # 配置文件读取器
│   ├── error.py         # 自定义异常层级
│   ├── logger_all.py    # 日志、子进程、交互提示辅助
│   ├── grn_input.py     # PSGRN 输入生成器
│   ├── cmp_input.py     # PSCMP 输入生成器（观测点、预应力）
│   ├── consolidate.py   # 按深度合并 + GMT XYZ 写出
│   ├── plot_coulomb.py  # GMT 断层面剖面绘图
│   ├── run.sh           # 便捷封装（cd + python3 main.py）
│   ├── psgrn.sh         # PSGRN Fortran 启动器
│   ├── pscmp.sh         # PSCMP Fortran 启动器
│   └── clean.sh         # 删除生成文件（可迁移）
├── config/              # 用户可编辑的参数文件
│   ├── receiving_fault.dat
│   ├── source_fault.dat
│   ├── calculation_setting.dat
│   ├── config.dat
│   └── model.dat
├── output/              # 生成的结果（运行时创建）
│   ├── consolidated.dat
│   ├── gmt_coulomb.xyz
│   └── coulomb_fault_plane.pdf
├── temp/                # 中间文件（运行时创建）
│   ├── grn_input/       # .grn 文件
│   ├── grn/{depth}/     # 格林函数输出
│   ├── cmp_input/       # .cmp 文件
│   └── cmp/{depth}/     # 每个深度的 PSCMP 输出
└── logs/                # 带时间戳的日志文件
```

## 配置文件

### `receiving_fault.dat`
定义接收（目标）断层几何：参考点经纬度、深度、长度、宽度、走向、倾角。支持多个子断层段。观测深度范围由最浅参考点和最深下倾延伸计算得出。

### `source_fault.dat`
列出震源断层的子断层（当前最多 432 个），包括其位置、尺寸和滑动分布（*pos_s*、*pos_d*、*slip_strike*、*slip_downdip*、*opening*）。

### `calculation_setting.dat`
控制参数：
- **深度步长**（第 1 行，第 1 个值）— 也以 `depth_step × 2` km 决定水平观测间距。
- 观测距离设置（第 2 行）。
- 震源深度设置（第 3 行）。
- 时间采样和波数积分参数。

### `config.dat`
输出开关：
- `insar`（0/1）— 启用 InSAR 视线位移输出。
- `icmb`（0/1）— 启用库仑应力输出。启用时还提供：摩擦系数、Skempton 比率、控制性断层走向/倾角/滑动角，以及三个主应力（sigma1, sigma2, sigma3）。
- 快照数量和每个快照的时间 + 文件名。

### `model.dat`
层状粘弹性地球模型：深度、Vp、Vs、密度、瞬态粘滞度 η1、稳态粘滞度 η2 以及松弛比 α（当 η1 = η2 = 0 时所有层均为弹性）。

## 输出文件

| 文件 | 描述 |
|------|------|
| `output/consolidated.dat` | 所有深度合并；固定宽度 Fortran 格式，含新增 `Depth[km]` 列 |
| `output/gmt_coulomb.xyz` | 空格分隔：`lon lat depth CMB_Fix CMB_Op1 CMB_Op2` |
| `output/coulomb_fault_plane.pdf` | 断层面剖面图（通过 GMT） |

## 库仑应力列

当 `icmb = 1` 时，每个快照文件包含：

```
CMB_Fix    — 固定（控制性）断层上的库仑应力
Sig_Fix    — 固定断层上的法向应力
CMB_Op1    — 最佳定向断层 1 上的库仑应力
CMB_Op2    — 最佳定向断层 2 上的库仑应力
（每个最佳定向断层还包含 Sig、Str、Dip、Slp）
```

**CMB_Fix** 是主要诊断量：它是在用户指定的接收断层几何上解算的 ΔCFS。如果 `config.dat` 中三个主应力（sigma1、sigma2、sigma3）均设为 0，则输出仅包含同震应力变化，无背景预应力贡献。

## 绘图

图为接收断层面的剖面图：沿走向距离（x 轴，km） vs 深度（y 轴，km，反转使 0 在顶部）。色标为以 0 为中心的 divergent polar CPT。绘图阶段可独立运行——只需之前后处理阶段生成的 `output/gmt_coulomb.xyz` 存在即可。

## 可迁移性

- 所有内部路径在导入时通过 `src/constant.py` 解析为绝对路径。`main.py` 可从任何工作目录调用。
- Fortran 可执行文件预计在 `$PATH` 中。
- `src/` 中的 shell 脚本（`run.sh`、`clean.sh`、`psgrn.sh`、`pscmp.sh`）均在运行时解析项目根目录，可从任何工作目录调用。
- 标准库之外的唯一 Python 依赖是 `pyproj`。

## 注意事项

- 水平观测点间距按设计为 `depth_step × 2` km，与传递给 `build_cmp_input` 的 `observation_max_interval` 参数一致。
- 在深度 8 km 处，地球模型存在显著的地层界面（Vp/Vs/ρ 变化），这会导致该深度的 CMB_Fix 值出现可见的突变。如需突出浅部细节，可通过环境变量 `CMB_MIN` / `CMB_MAX` 缩小色标范围。
