#!/bin/bash
# ノアの着物版を元のnowa.blend(gitのHEAD)から全工程で再現する。
# 使い方: build_all.sh <作業ディレクトリ> <出力先(source/calude)>
# Blender 4.0 + mmd_tools v4.0.0 前提。落ちた工程は成功するまで数回再実行する。
set -u
S=$1; D=$2; H=$(cd "$(dirname "$0")" && pwd); REPO=$(cd "$H/../../.." && pwd); SK=$REPO/.claude/skills/blender-cloud-render/scripts
run(){ local tag=$1; shift; for i in 1 2 3; do "$@" 2>&1 | tee $S/last.log | grep -q "$tag" && return 0; echo "retry $tag"; done; echo "FAILED $tag"; exit 1; }
mkdir -p $S; cd $S
[ -f nowa_orig.blend ] || git -C $REPO show HEAD:source/calude/nowa.blend > nowa_orig.blend      # 元のモデル(コミット済み)
run DONE1  blender -b nowa_orig.blend -P $H/build_strip.py -- $S                 # 旧衣装の撤去
run DONE2  blender -b nowa_s1.blend -P $H/build_kimono.py -- $S                  # 着物・素足・サンダル・揺れ物ボーン
run DONEP  blender -b nowa_s2.blend -P $H/build_physics.py -- $S/nowa_s3.blend   # 剛体+ジョイント+表示枠
run DONEF  blender -b nowa_s3.blend -P $H/build_finalize.py -- $S/nowa_s4.blend  # 名前・レスト姿勢
rm -rf $S/pmx; blender -b nowa_s4.blend -P $SK/blend_to_mmd.py -- $S/pmx/nowa_kimono.pmx >/dev/null 2>&1
blender -b -P $SK/mmd_to_blend.py -- $S/pmx/nowa_kimono.pmx $S/rt_kimono.blend >/dev/null 2>&1      # PMX往復(書き出せて読み込めることの確認も兼ねる)
# 1つの.blendに通常+着物をコレクションで同梱(通常が既定で表示)
run DONEM  blender -b nowa_orig.blend -P $H/merge_outfits.py -- $S/merged.blend "着物 (kimono)=$S/rt_kimono.blend"
blender -b merged.blend -P $H/finalize.py -- $D/nowa.blend >/dev/null 2>&1
rm -rf $D/nowa_pmx/kimono; mkdir -p $D/nowa_pmx/kimono; cp -r $S/pmx/* $D/nowa_pmx/kimono/
echo ALLDONE
