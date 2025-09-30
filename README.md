好的 ✅。我已经把你仓库里原有的 [README.md](https://github.com/howarduong/bigworld_blender_exporter-test/blob/main/README.md) 内容梳理过一遍，去掉了重复的部分，重新排版，融合了我们前面改进过的插件架构和使用说明。下面是一个完整的、结构清晰的 **新版 README.md**：  

---

# 🛠️ BigWorld Blender Exporter (Blender 4.5.3)

为 **BigWorld Engine 2.0.1** 开发的 **Blender 4.5.3 插件**，支持将 Blender 模型、骨骼、动画、材质导出为 BigWorld 引擎可识别的格式。  
目标是复刻 3ds Max/Maya 插件的功能，并适配 Blender 的工作流。

---

## ✨ 功能特性

- **静态模型导出**：`.model` + `.visual` + `.primitives`  
- **骨骼动画导出**：`.animation`  
- **材质系统**：`.mfm` 材质文件，支持贴图路径、DDS 转换  
- **碰撞体导出**：支持 BSP 碰撞模型  
- **LOD 支持**：可配置多级 LOD  
- **批量导出**：支持场景/选中对象批量导出  
- **UI 面板**：直观的 Blender 界面，带中文提示  

---

## 📂 插件目录结构

```
bigworld_blender_exporter/
├── __init__.py              # 插件入口
├── config.py                # 配置常量
├── core/                    # 核心逻辑
│   ├── exporter.py          # 主导出器
│   ├── model_processor.py   # 模型处理
│   ├── animation_processor.py # 动画处理
│   └── material_processor.py  # 材质处理
├── formats/                 # 文件格式生成
│   ├── model_format.py      # .model
│   ├── visual_format.py     # .visual
│   ├── primitives_format.py # .primitives
│   ├── animation_format.py  # .animation
│   └── material_format.py   # .mfm
├── ui/                      # 用户界面
│   ├── panels.py            # 面板
│   ├── operators.py         # 操作器
│   ├── properties.py        # 自定义属性
│   └── preferences.py       # 插件偏好设置
├── utils/                   # 工具函数
│   ├── math_utils.py        # 坐标系/压缩
│   ├── binary_writer.py     # 二进制写入
│   ├── xml_writer.py        # XML 写入
│   ├── validation.py        # 数据验证
│   └── logger.py            # 日志系统
└── README.md
```

---

## 🔑 核心文件格式

- **`.model`**：XML，模型配置，引用 `.visual`，包含动画、碰撞、extent  
- **`.visual`**：XML，渲染配置，包含节点树、geometry、primitiveGroups、材质绑定  
- **`.primitives`**：二进制，顶点/索引缓冲，支持压缩法线、骨骼权重  
- **`.animation`**：二进制，骨骼动画关键帧数据  
- **`.mfm`**：XML，材质定义（EffectMaterial），包含 fx、materialKind、property  

---

## 🖥️ 使用方法

1. **安装插件**  
   - 下载本仓库  
   - 在 Blender 中 `编辑 > 偏好设置 > 插件 > 安装`，选择 `bigworld_blender_exporter` 文件夹  

2. **设置导出路径**  
   - 在 `3D 视图 > 侧边栏 > BigWorld` 面板中，设置 `Export Path`  

3. **配置导出选项**  
   - 勾选需要导出的内容：Mesh、Skeleton、Animation、Materials、Collision  
   - 设置坐标系（默认 Y-up）、缩放、顶点格式  

4. **材质设置**  
   - 在 `Material Settings` 面板中配置贴图路径  
   - 可选择复制贴图、转换为 DDS  

5. **动画设置**  
   - 设置帧率、起止帧  
   - 可选择烘焙动画、优化关键帧、循环  

6. **导出**  
   - 点击 `Export Selected` 或 `Export All`  
   - 导出的文件结构：  
     ```
     export_path/
     ├── models/
     │   ├── example.model
     │   ├── example.visual
     │   ├── example.primitives
     ├── materials/
     │   └── example.mfm
     └── animations/
         └── example.animation
     ```

---

## 📖 参考资料

- [教学文档：完整流程](https://howarduong.github.io/github.io/doc/documentation_roadmap.html)  
- [教学文档：模型创建](https://howarduong.github.io/github.io/content_creation_page.html)  
- [BigWorld Engine 2.0.1 源码](https://github.com/howarduong/BigWorld-Engine-2.0.1.git)  
- [标准示例 `.model`](https://github.com/howarduong/github.io/blob/main/base.model)  
- [标准示例 `.visual`](https://github.com/howarduong/github.io/blob/main/base.visual)  
- [标准示例 `.mfm`](https://github.com/howarduong/github.io/blob/main/handrails.mfm)  

---

## 🗺️ 开发计划

- [x] 插件基础框架  
- [x] 静态模型导出  
- [x] 材质系统  
- [x] 动画导出  
- [ ] LOD 支持  
- [ ] 碰撞体导出  
- [ ] 批量导出优化  

---

## ⚠️ 注意事项

- Blender 使用 **Z-up**，BigWorld 使用 **Y-up**，插件会自动转换。  
- 骨骼权重最多支持 **3 个影响骨骼**，权重会自动归一化并量化为 byte。  
- 法线/切线/副法线会压缩为 **short2** 格式。  
- `.animation` 文件必须和 `.model` 文件中的 `animations` 节点保持一致。  

---

## 📌 总结

本插件为 BigWorld 引擎提供了 **Blender 4.5.3 的现代化导出工具链**，覆盖了模型、材质、动画的完整流程，参考了官方 Max/Maya 插件的逻辑，并对齐了引擎源码的文件格式定义。  

---

👉 这样整理后，README.md 就既包含了原有的参考资料，又有清晰的 **功能说明、目录结构、使用方法**，去掉了重复的长篇描述。  

要不要我帮你再写一个 **快速上手示例**（比如导出一个带骨骼动画的角色的完整流程），放在 README 的最后，方便新用户直接跟着操作？
