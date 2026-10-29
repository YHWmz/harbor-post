# 送信人重制 QA

结论：通过。

- 原作者CC0 GLB来源、许可和SHA256保留；实际基底为完整Quaternius Casual Character。角色8768三角面、62骨骼、三个原生骨骼循环，原方块人物已移除。
- 所有输出顶点有规范化蒙皮权重，新增配件按材质合并为7批；无源写实贴图，无静态T姿态描边。
- Idle/Walk/Run各采13个相位：帽子绑定不漂移，肘膝/手部有实际动作。脚底相对地面范围：Idle 0.000m；Walk -0.012到0.019m；Run -0.002到0.066m。
- courier.mjs、courier-pose.py、walking.mjs及civic-districts.mjs通过；100585步行节点、20片陆地、24个目的地保持可达，全场景315657面。
- 浏览器正侧背与行走近景检查，实际游戏待机/走动/转身/快走与上下船检查；控制台无错误。
- 配色、纸纹与光照使用现有项目风格；脸部较淡排线，服装保留轻墨边。

图：courier-turnaround.png、courier-in-town.png。
