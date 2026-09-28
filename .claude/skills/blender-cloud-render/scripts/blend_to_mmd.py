"""
Blender(.blend) -> MMD(.pmx) 変換スクリプト

使い方:
  blender --background input.blend --python blend_to_mmd.py -- output.pmx [root_object_name]

root_object_nameを省略した場合、シーン内のmmd_rootオブジェクト
(bpy.data.objects中でmmd_type=='ROOT'のもの)を自動検出する。
複数存在する場合はエラーになるため、その場合は明示的に指定すること。

前提: mmd_toolsアドオンが導入済みであること(cloud_setup_script.sh参照)。
"""
import sys
import os
import bpy


def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    if len(argv) < 1:
        raise SystemExit(
            "使い方: blender --background input.blend --python blend_to_mmd.py -- output.pmx [root_object_name]"
        )
    pmx_path = os.path.abspath(argv[0])
    root_name = argv[1] if len(argv) > 1 else None
    return pmx_path, root_name


def _patch_get_normals_for_blender_40():
    """Blender 4.0系ではmesh.corner_normalsが遅延計算(空)のままで、
    evaluated_get().to_mesh()で得た評価済みメッシュにも計算済みの状態が
    引き継がれない。mmd_toolsのexporter(v4.0.0)はBlender 4.1+の自動計算を
    前提にしており、これが無いと"assert len(loop_normals) == len(mesh.loops)"
    で失敗する。exporter内部の__get_normals呼び出し直前にcalc_normals_split()を
    挟むようパッチする。Blender 4.1+ではcalc_normals_split()は非推奨だが
    呼んでも無害(no-op相当)なため、バージョン分岐は行わない。
    """
    from mmd_tools.core.pmx import exporter as pmx_exporter_mod

    target_cls = getattr(pmx_exporter_mod, "__PmxExporter")
    original = getattr(target_cls, "_PmxExporter__get_normals")

    def patched(mesh, matrix):
        if hasattr(mesh, "calc_normals_split"):
            mesh.calc_normals_split()
        return original(mesh, matrix)

    setattr(target_cls, "_PmxExporter__get_normals", staticmethod(patched))


def find_root_object(root_name):
    if root_name:
        obj = bpy.data.objects.get(root_name)
        if obj is None:
            raise SystemExit(f"指定されたrootオブジェクトが見つかりません: {root_name}")
        if obj.mmd_type != "ROOT":
            raise SystemExit(f"指定オブジェクトはmmd_root(ROOT)ではありません: {root_name}")
        return obj

    roots = [o for o in bpy.data.objects if o.mmd_type == "ROOT"]
    if len(roots) == 0:
        raise SystemExit("シーン内にmmd_root(ROOT)オブジェクトが見つかりません。mmd_tools経由で作成されたモデルか確認してください。")
    if len(roots) > 1:
        names = ", ".join(o.name for o in roots)
        raise SystemExit(f"mmd_rootが複数見つかりました。root_object_nameで明示指定してください: {names}")
    return roots[0]


def main():
    pmx_path, root_name = parse_args()

    ok = bpy.ops.preferences.addon_enable(module="mmd_tools")
    if "FINISHED" not in ok:
        raise SystemExit("mmd_toolsアドオンの有効化に失敗しました。導入状態を確認してください。")

    root_obj = find_root_object(root_name)
    print(f"[blend_to_mmd] exporting root: {root_obj.name} -> {pmx_path}")

    bpy.ops.object.select_all(action="DESELECT")
    root_obj.select_set(True)
    bpy.context.view_layer.objects.active = root_obj

    _patch_get_normals_for_blender_40()

    os.makedirs(os.path.dirname(pmx_path), exist_ok=True)
    bpy.ops.mmd_tools.export_pmx(
        filepath=pmx_path,
        scale=1.0 / 0.08,  # mmd_to_blend.pyのデフォルトscaleの逆数(MMD標準スケールへ戻す)
        copy_textures=True,
        sort_materials=False,
        disable_specular=False,
        visible_meshes_only=False,
        overwrite_bone_morphs_from_pose_library=False,
        translate_in_presets=False,
        sort_vertices="NONE",
    )
    print(f"[blend_to_mmd] saved: {pmx_path}")


if __name__ == "__main__":
    main()
