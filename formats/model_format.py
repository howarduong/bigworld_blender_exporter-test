# 文件位置: bigworld_blender_exporter/formats/model_format.py
# Model file format for BigWorld export (aligned to official grammar)

import xml.etree.ElementTree as ET
from ..utils.logger import get_logger
from ..utils.xml_writer import write_xml_file

logger = get_logger("model_format")


def export_model_file(filepath, model_data):
    """
    Export model data to BigWorld .model file

    model_data dict expected keys:
      - visual: str (path to .visual file)
      - bbox_min, bbox_max: str ("x y z")
      - extent: float
      - parent: str
      - bsp_model: str
      - animations: list of {
            name, nodes, frameRate, firstFrame, lastFrame,
            alpha?: bool, cognate?: bool
        }
      - actions: list of {
            name, animation, blendInTime, blendOutTime,
            track?, isMovement?, isCoordinated?, isImpacting?,
            match_trigger?: dict, match_cancel?: dict,
            scalePlaybackSpeed?, feetFollowDirection?,
            oneShot?, promoteMotion?
        }
      - materialNames: list[str] (optional)
    """
    logger.info(f"Exporting model file: {filepath}")

    root = ET.Element("model")

    # metaData
    meta = ET.SubElement(root, "metaData")
    ET.SubElement(meta, "copyright").text = (
        "Copyright BigWorld Pty Ltd. Use freely in any BigWorld licensed game."
    )
    ET.SubElement(meta, "created_by").text = "blender_exporter"
    ET.SubElement(meta, "created_on").text = "0"
    ET.SubElement(meta, "modified_by").text = "blender_exporter"
    ET.SubElement(meta, "modified_on").text = "0"

    # Visual reference
    ET.SubElement(root, "nodefullVisual").text = model_data.get("visual", "")

    # Material names
    mats = model_data.get("materialNames", [])
    if mats:
        mat_elem = ET.SubElement(root, "materialNames")
        for m in mats:
            ET.SubElement(mat_elem, "m").text = m
    else:
        ET.SubElement(root, "materialNames").text = ""

    # Visibility box
    visbox = ET.SubElement(root, "visibilityBox")
    ET.SubElement(visbox, "min").text = model_data.get("bbox_min", "-1.0 -1.0 -1.0")
    ET.SubElement(visbox, "max").text = model_data.get("bbox_max", "1.0 1.0 1.0")

    # Extent
    ET.SubElement(root, "extent").text = f"{model_data.get('extent', 10.0):.6f}"

    # Parent
    ET.SubElement(root, "parent").text = model_data.get("parent", "")

    # Animations
    anims = model_data.get("animations", [])
    if anims:
        anims_elem = ET.SubElement(root, "animations")
        for a in anims:
            anim_elem = ET.SubElement(anims_elem, "animation")
            ET.SubElement(anim_elem, "name").text = a["name"]
            ET.SubElement(anim_elem, "nodes").text = a["nodes"]
            ET.SubElement(anim_elem, "frameRate").text = str(a.get("frameRate", 30))
            ET.SubElement(anim_elem, "firstFrame").text = str(a.get("firstFrame", 0))
            ET.SubElement(anim_elem, "lastFrame").text = str(a.get("lastFrame", 0))
            if "alpha" in a:
                ET.SubElement(anim_elem, "alpha").text = str(bool(a["alpha"])).lower()
            if "cognate" in a:
                ET.SubElement(anim_elem, "cognate").text = str(bool(a["cognate"])).lower()

    # Actions
    acts = model_data.get("actions", [])
    if acts:
        acts_elem = ET.SubElement(root, "actions")
        for ac in acts:
            act_elem = ET.SubElement(acts_elem, "action")
            ET.SubElement(act_elem, "name").text = ac["name"]
            ET.SubElement(act_elem, "animation").text = ac["animation"]
            ET.SubElement(act_elem, "blendInTime").text = str(ac.get("blendInTime", 0.1))
            ET.SubElement(act_elem, "blendOutTime").text = str(ac.get("blendOutTime", 0.1))
            if "track" in ac:
                ET.SubElement(act_elem, "track").text = str(ac["track"])
            ET.SubElement(act_elem, "isMovement").text = str(ac.get("isMovement", False)).lower()
            ET.SubElement(act_elem, "isCoordinated").text = str(ac.get("isCoordinated", False)).lower()
            ET.SubElement(act_elem, "isImpacting").text = str(ac.get("isImpacting", False)).lower()

            # match.trigger / cancel (optional structured)
            if "match_trigger" in ac or "match_cancel" in ac:
                match_elem = ET.SubElement(act_elem, "match")
                if "match_trigger" in ac:
                    trig = ET.SubElement(match_elem, "trigger")
                    for k, v in ac["match_trigger"].items():
                        ET.SubElement(trig, k).text = str(v)
                if "match_cancel" in ac:
                    canc = ET.SubElement(match_elem, "cancel")
                    for k, v in ac["match_cancel"].items():
                        ET.SubElement(canc, k).text = str(v)

            # optional flags
            if "scalePlaybackSpeed" in ac:
                ET.SubElement(act_elem, "scalePlaybackSpeed").text = str(ac["scalePlaybackSpeed"]).lower()
            if "feetFollowDirection" in ac:
                ET.SubElement(act_elem, "feetFollowDirection").text = str(ac["feetFollowDirection"]).lower()
            if "oneShot" in ac:
                ET.SubElement(act_elem, "oneShot").text = str(ac["oneShot"]).lower()
            if "promoteMotion" in ac:
                ET.SubElement(act_elem, "promoteMotion").text = str(ac["promoteMotion"]).lower()

    # EditorOnly / BSP reference
    editor = ET.SubElement(root, "editorOnly")
    bsp = ET.SubElement(editor, "bspModels")
    ET.SubElement(bsp, "model").text = model_data.get("bsp_model", "")

    # Write XML
    write_xml_file(root, filepath)
    logger.info(f".model written: {filepath}")
