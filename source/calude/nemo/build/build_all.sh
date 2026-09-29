#!/bin/bash
# nemoの全服装を素体(Seed-san)から生成する。使い方: build_all.sh <作業ディレクトリ(seed.blendを置く)> <出力先(source/calude/nemo)>
# Blender 4.0 + mmd_tools v4.0.0 前提。ブーリアン演算でBlenderがまれに落ちるため、落ちた工程は成功するまで再実行する。
set -u
S=$1; D=$2; H=$(cd "$(dirname "$0")" && pwd); SK=$(cd "$H/../../../.." && pwd)/.claude/skills/blender-cloud-render/scripts
run(){ local tag=$1; shift; for i in 1 2 3 4 5; do "$@" 2>&1 | tee $S/last.log | grep -q "$tag" && return 0; echo "retry $tag"; done; echo "FAILED $tag"; exit 1; }
cd $S
run DONE  blender -b seed.blend -P $H/build1.py -- $S
run DONE2 blender -b nemo_s1.blend -P $H/build2.py -- $S
run DONEF blender -b nemo_s2.blend -P $H/build_face.py -- $S
# 服装A: 軍服
run DONEB blender -b nemo_s2f.blend -P $H/build_base.py -- $S
run DONEC blender -b nemo_s2o.blend -P $H/build_coat.py -- $S
run DONE3 blender -b nemo_s2c.blend -P $H/build3.py -- $S
rm -rf $S/pmxA; blender -b nemo_s3.blend -P $SK/blend_to_mmd.py -- $S/pmxA/nemo_military.pmx >/dev/null 2>&1
blender -b -P $SK/mmd_to_blend.py -- $S/pmxA/nemo_military.pmx $S/rt_military.blend >/dev/null 2>&1
# 服装C: 赤コート(軍服と同じ土台に長い裾+揺れ物、左腕の黒革とベルト、サングラス)
cp nemo_s2o.blend nemo_s2o_A.blend
export NEMO_OUTFIT=red
run DONEC blender -b nemo_s2o_A.blend -P $H/build_coat_red.py -- $S
run DONE3 blender -b nemo_s2c_red.blend -P $H/build3.py -- $S
run DONEP blender -b nemo_s3.blend -P $H/build_physics.py -- $S $S/nemo_s3p_red.blend
unset NEMO_OUTFIT
rm -rf $S/pmxC; blender -b nemo_s3p_red.blend -P $SK/blend_to_mmd.py -- $S/pmxC/nemo_redcoat.pmx >/dev/null 2>&1
blender -b -P $SK/mmd_to_blend.py -- $S/pmxC/nemo_redcoat.pmx $S/rt_red.blend >/dev/null 2>&1
# 服装B: 白礼装(マント+物理)
export NEMO_OUTFIT=white
run DONEB blender -b nemo_s2f.blend -P $H/build_base.py -- $S
run DONEC blender -b nemo_s2o.blend -P $H/build_coat.py -- $S
cp nemo_s2c.blend nemo_s2c_white.blend
run DONEK blender -b nemo_s2c_white.blend -P $H/build_cape.py -- $S
run DONE3 blender -b nemo_s2k_white.blend -P $H/build3.py -- $S
run DONEP blender -b nemo_s3.blend -P $H/build_physics.py -- $S $S/nemo_s3p_white.blend
unset NEMO_OUTFIT
rm -rf $S/pmxB; blender -b nemo_s3p_white.blend -P $SK/blend_to_mmd.py -- $S/pmxB/nemo_formal.pmx >/dev/null 2>&1
blender -b -P $SK/mmd_to_blend.py -- $S/pmxB/nemo_formal.pmx $S/rt_formal.blend >/dev/null 2>&1
# 1つの.blendに3服装をコレクションで同梱
run DONEM blender -b rt_military.blend -P $H/merge_outfits.py -- $S/merged.blend "白礼装 (formal)=$S/rt_formal.blend" "赤コート (red coat)=$S/rt_red.blend"
blender -b merged.blend -P $H/finalize.py -- $D/nemo.blend >/dev/null 2>&1
rm -rf $D/pmx; mkdir -p $D/pmx/military $D/pmx/formal $D/pmx/redcoat; cp -r $S/pmxA/* $D/pmx/military/; cp -r $S/pmxB/* $D/pmx/formal/; cp -r $S/pmxC/* $D/pmx/redcoat/
echo ALLDONE
