# 公开素材选用与手绘统一

| 选用模型 | 来源与作者 | 许可 | 实际使用 |
| --- | --- | --- | --- |
| Gazebo | [Quaternius · Poly Pizza](https://poly.pizza/m/xYZB1TmGMv) | CC0 1.0，历史模型页标注2022-07-11 | 两处公园凉亭 |
| Horse Statue 01 | [Poly Haven](https://polyhaven.com/a/horse_statue_01)，原作者见源目录SOURCE.json | [CC0](https://polyhaven.com/license) | 市政厅前庭石雕 |
| Painted Wooden Bench | [Poly Haven](https://polyhaven.com/a/painted_wooden_bench)，Kirill Sannikov | CC0 | 三张公园长椅 |

原始文件及依赖保存在 `source-assets/quaternius/`、`source-assets/polyhaven/`，许可证与来源URL随目录提供。下载的Poly Haven文件逐项核对API提供的MD5。实际使用次数、原面数、优化面数和纸色材质见 `dist/assets/curated-assets.json`。

马雕塑从22388三角面简化为1800三角面，保留抬蹄剪影；凉亭698三角面，长椅630三角面。Blender中统一米制比例、地面原点和朝向，去掉源材质，分别映射到现有Stone、Wood、Slate纸色。街区最终导出不含原始写实贴图，继续使用Three.js统一纸纹、墨线及夜间光照。几何按共享材质合并。

庄园与市政厅的主体继续采用项目定制建筑：细化四坡屋顶、老虎窗、烟囱、拱窗、百叶窗、门廊、石饰、钟盘与山花。花园与公园采用圆角修篱、多层花叶、曲径、藤架和花钵，使公开素材与整体空间比例相符。

## 送信人

[Casual Character / Quaternius](https://poly.pizza/m/kZ3DmIoGip)，作者原始上传2022-02-22，CC0 1.0。原始GLB保存在`source-assets/quaternius/casual-character.glb`，来源和SHA256见CHARACTER-SOURCE.json，许可见CHARACTER-LICENSE.txt。比较Adventurer与Man in Suit后，选择日常服装结构更适合的Casual。

实际使用原人物网格、手指、62骨骼/权重及Idle/Walk/Run三个原动画。项目订制服装配色、邮政便帽、衬领袖口、邮包/信件和肩带，移除原展示用球体及无关战斗动画；8768面，配件按材质合并为7批。Blender源和可重复构建脚本随库提供。
