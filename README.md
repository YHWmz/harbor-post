# 水巷来信 · Harbor Post

手绘风格的欧洲水乡送信游戏。驾驶小船穿行运河、湖泊和海湾，靠岸投递五封信；也可以在悬崖码头换乘马车，沿山路到城堡送信。

场景采用 **Blender 建模 → GLB 导出 → Three.js 加载 → 统一手绘渲染**。游戏可直接部署到静态托管，无需服务器或构建步骤。

![小镇月夜](docs/moonlit-canal-town.png)

## 本地运行

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory dist
```

打开 http://127.0.0.1:8765/ 。网页和模型均随仓库提供，无需安装 npm 依赖或运行 Blender。

- W / S：前进与倒船；A / D：转舵；空格：刹船。
- E：靠岸送信、换乘马车或返回小船；马车沿山路行驶。
- Esc：菜单；M：河道图；滚轮：调整视野。
- 菜单可调船速（默认 1.5×，范围 0.75～2.5×）、跟随/全景、日光/夜晚、晴天/雨天、声音和任务追踪。
- 访问 `/?route=castle` 可从悬崖码头开始体验；原邮路进度单独保存在当前浏览器。

## 部署到 Cloudflare Pages

在 Cloudflare 创建 **Pages** 项目并连接 `YHWmz/harbor-post`，设置：

| 项目 | 值 |
| --- | --- |
| 生产分支 | `main` |
| 根目录 | 仓库根目录（留空） |
| 框架预设 | `None` |
| 构建命令 | `exit 0` |
| 构建输出目录 | `dist` |
| 环境变量 | 无需设置 |

部署只使用 `dist/`。Blender、源素材和测试无需在 Cloudflare 上执行。这里提供的是 Pages 部署方式；本次上传不会创建或部署 Cloudflare 项目。

参考：[Cloudflare 静态 HTML 指南](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/)、[构建设置](https://developers.cloudflare.com/pages/configuration/build-configuration/)。

## 当前场景

- 弯曲且宽窄不同的运河、山后湖泊、主入海口与海滨码头。
- 70 栋六种轮廓的住宅、城市道路、喷泉中心广场、集市与树木。
- 左上方悬崖城堡，229 米可往返的马车山路。
- 三座贴湖近山与雪线附近约42米高的融水源，溪流沿真实山谷汇入湖泊；雪山远景、太阳、月亮、云和雨天。
- 27 盏沿街及山路路灯，夜晚暖光与亮窗；流动水面和场景倒影。
- 8 艘泊岸帆船/渔船、水上装饰和 12 处有碰撞的浅滩石头。
- 原先确认的 Blender v5 邮船、码头及地标继续复用。

![场景全景](docs/civic-gardens-v3.png)

## 文件结构

```text
dist/             可直接发布的网页、Three.js、GLB 与许可文件
tests/            航路、碰撞、马车和本次场景优化验证
tools/            可移植的 Blender Python 构建脚本
blender/          当前城镇、马车、山景和原 v5 可编辑源文件
source-assets/    实际复用的 Kenney CC0 原始 GLB 组件与许可证
docs/             预览截图
ART_DIRECTION.md  美术方向
asset-audit.json  场景网格和导航导出审计
```

## 验证

安装 Node.js 后，在仓库根目录运行：

```sh
node tests/navigation.mjs
node tests/carriage.mjs
node tests/town-upgrade.mjs
python3 tests/alpine-terrain.py
node tests/civic-districts.mjs
node tests/walking.mjs
node tests/courier.mjs
```

覆盖全部五封信、返航、城堡码头、湖泊、河口、海滨及近海的实际驾驶，最高船速碰撞，229 米马车上下山和建筑净空，以及河口封闭、原生灯位、广场、住宅和山泉坡度。主城镇导出为 219,182 个三角面、26 个材质，限制为 220,000 个三角面。

## 修改与重建模型

使用 Blender 4.5 LTS，`blender` 命令需在 PATH 中，或替换为本机 Blender 可执行文件路径：

```sh
blender -b --python tools/build_european_town.py
blender -b --python tools/build_painted_hills.py
blender -b --python tools/build_carriage.py
blender -b --python tools/build_walking.py
```

脚本相对仓库根目录解析路径，可在其他电脑运行。主城镇脚本读取 `blender/harbor_expanded_v5.blend`、`source-assets/` 和已有的 approved GLB 模块，输出到 `blender/` 与 `dist/assets/`，同时更新 `dist/world.mjs` 的导航数据。不要只在 Three.js 中修改可见岸线而不更新碰撞；也不要手动修改生成的 `world.mjs` 地形数据。

Blender 负责建筑、地形、车辆和碰撞的真实网格；Three.js 负责纸纹、墨线、水面反射、天气、光照与游戏逻辑。

## 第三方素材

- [Kenney Fantasy Town Kit](https://kenney.nl/assets/fantasy-town-kit)：CC0，原始许可随 `source-assets/fantasy-town/` 和 `dist/assets/` 提供。
- [Kenney Watercraft Kit](https://kenney.nl/assets/watercraft-kit)：CC0，原始许可随 `source-assets/watercraft/` 和 `dist/assets/` 提供。
- Three.js：MIT，见 `dist/vendor/THREE-LICENSE.txt`。

公开组件在 Blender 中统一为纸色材质并按材质合并；使用清单见 `dist/assets/public-assets.json`。未使用参考视频作者的模型。

## 版本与湖岸近山优化

[`v1`](https://github.com/YHWmz/harbor-post/tree/v1) 固定保存提交 `6ce44e9` 的完整版本，后续优化在 `main` 继续，避免覆盖 v1。

湖泊北岸新增三座36～55米的近山；约42米高的雪线融水顺着弯曲山谷流下。`tools/alpine_terrain.py` 同时定义山体、溪床、雪线和水源，导出的水面与山谷网格逐段对齐，移除了旧版直立石槽。山景共10,204个三角面，主城镇219,182个三角面；全景取景已纳入完整近山轮廓。新增 Python 检查直接读取山景 GLB，确认溪床高度和水面贴合。

## 湖岸封口与公共街区

根据两张截图封闭山边通往左右外海的两个横向水口，新增连续地面与对应船体碰撞，保留湖泊、城堡码头、镇内河网和主河口。东侧湖岸增加庄园、轴线花园、菜圃果园及带条纹遮棚的临湖餐厅；镇街外侧新增钟楼市政厅与前庭；西侧封口加入酒庄、葡萄园和果树；外围街区补五处庭园及一间花园餐厅，崖顶西缘加入玫瑰庭园。

这些建筑与景观仍由 Blender 原生生成，脚本 `tools/build_civic_districts.py` 由城镇构建脚本自动调用，独立导出 `dist/assets/civic-districts.glb`（47,574三角面，预算50,000），复用纸色材质、墨线和夜晚窗光。主城镇219,182三角面，仍在220,000预算内。没有新增界面按钮。

验证：`node tests/civic-districts.mjs` 检查两个封口、建筑占地位于陆地、庭园与崖顶地面高度、湖泊可航行空间和原生模型预算；全套原邮路与马车检查继续通过。

## 精修街区与公开素材

庄园细化拱窗、百叶窗、门廊、石饰、老虎窗与烟囱；市政厅补齐钟盘、柱廊、山花和石雕前庭。花园使用立体修篱、分层花叶、藤架和曲径，五处公园具有不同布局。

复用 Quaternius 凉亭与 Poly Haven 长椅、马雕塑（CC0），经 Blender 比例统一、减面和纸色材质重绘后合并导出，再由 Three.js 统一墨线、纸纹与夜间光照。原始素材、许可、优化记录和生成脚本均保留，详见[素材清单](docs/curated-assets.md)。精修街区版本297,931三角面；加入步行桥与人物后全场景315,657三角面（上限320,000）。

![庄园近景](docs/refined-manor.png)
![市政厅近景](docs/refined-hall.png)
![庄园花园](docs/refined-garden.png)

## 连通小镇与陆地步行

首页可选「先在镇里走走」，也可以驾船靠近河岸、慢下来按 F 下船。步行 W/S 前后走、A/D 转身、Shift 快走；靠近原船按 F 返回。E 保留送信和换乘马车等上下文交互。地图 M 显示停船处和步桥；远离小船后隐藏回船按钮。原有邮路进度继续保存。

新增8座有栏杆和接坡的步桥，结合原4座石桥与山路，将20片城镇陆地接入同一陆地步行网络。人物可以到庄园、花园、公园、市政厅、两处码头，沿山路上城堡。建筑墙面、桥栏杆和水边参与碰撞，不允许直接踏水。房屋内部不开放。

`tools/build_walking.py`在现有Blender场景上生成独立源文件`blender/walking-town.blend`，导出`walking-town.glb`、`walker.glb`和`walking-navigation.json`。步行地面按0.45m多层网格采样原地形、桥面和山路，由实际网格的BVH排除墙体及道具，再验证完整连通性；运行时不重新生成桥梁建筑。人物采用经改造的Quaternius CC0骨骼角色，使用实际待机/走路/跑步动画。步桥8958三角面，现送信人8768三角面，沿用现有纸纹、墨线和日夜光照。

`node tests/walking.mjs`独立检查100585个步行节点的连通性、20片陆地、24个目的地（含山顶和邮路点）、上下船距离/限速、逐帧跨桥、海水碰撞及全场景预算。

![陆地步行](docs/walking-town.png)
![步桥与街区全景](docs/walking-network.png)

## 送信人角色重制

以 [Quaternius Casual Character](https://poly.pizza/m/kZ3DmIoGip)（CC0）替换264面的方块角色。保留原作者完整人物网格、62根骨骼及原始权重，导出Idle/Walk/Run三个循环，由速度平滑混合，支持倒退播放步态。面部、头发、手指、肩肘与膝盖沿用完整角色结构。

在Blender中统一灰绿制服、蓝灰帽裤、暖肤色和棕皮革，新增曲面便帽/帽檐、徽章、衬领、袖口、纽扣、前后肩带与圆角翻盖邮包（信件、缝线、扣件）。帽子跟随Head，邮包跟随Hips，肩带混合胸部/髋部权重。细配件按材质合并为7个批次。脸部采用较淡纸纹，衣物保留轻排线；蒙皮人物不添加停留在T姿态的静态描边几何。

原始文件、来源、SHA256和许可位于source-assets/quaternius；可编辑源为blender/courier.blend。单独重建：`blender -b --python tools/build_courier.py`；完整步行重建脚本会自动调用它。角色8768面，全场景315657面，仍小于320000预算。

验证：`node tests/courier.mjs`检查来源摘要、许可、网格/权重与动画通道；`blender -b blender/courier.blend --python tests/courier-pose.py`检查三种动作13个相位中的脚底高度、手臂动作和帽子绑定。

![送信人正侧背与步态](docs/courier-turnaround.png)
![游戏中的送信人](docs/courier-in-town.png)
