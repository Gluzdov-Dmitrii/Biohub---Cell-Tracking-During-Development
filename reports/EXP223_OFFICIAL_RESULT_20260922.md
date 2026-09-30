# EXP223 final official175 comparison — 2026-09-22

COMPLETE all350predictions/175perarm; eightGPUruns released, finalCPUscorer exit0/no timeout/liveprocessgroupempty. Runtime812.73s. All350immutablefile/routing/graph/receipt gates completed beforelabels. Official EXP214 baseline reproduced everyrow within1e-12.

|Pipeline|Full175 official score|44b6 (59)|6bba (116)|Difference vsours|
|---|---:|---:|---:|---:|
|Horaz selected50/20|0.7949879415|0.8367193999|0.7873724522|+0.0522587928|
|Our EXP214|0.7427291486|0.8052068737|0.7318060132|0|
|Fixed classical EXP222|0.7409785635|0.7172813987|0.7453264974|-0.0017505851|
|Horaz fixedlast50,same decoder|0.7386985046|0.8367193999|0.7211955056|-0.0040306440|

Horazselected improves on bothembryos; largest gain6bba. Selected-minus-last0.0562894368 entirely from6bba direction, where checkpoints20vs50 differ. This is consistent with strong checkpointdependence; does not byitself quantify selectionoptimism or prove selectedgain is spurious. Selectedepochs were chosen onouterfold inauthortraining, decoderhistoricaltuning unverified. Fixedlastcontrol removes thisspecific selectiondependence but not allrecipe/postprocessingbias.

Score0.7949879 is directly comparable reproduced development-adapted175 metric, NOT independent unbiasedCV; goal>=0.8notreached (gap0.0050120585). Authorclaim0.8135597on199notreproducedbythisdifferentcohort; do not call itfalse solelyfrom175difference. Our pipeline also development-adapted. No change to models/routing aftertargetscoring, no embryo-specificrouter or hidden-test claims.

Meanannotatednode recall:selected0.927075 vsours0.929493 vsfixedlast0.891039. Divisions:selected12TP51FP126FN;ours4TP50FP134FN;fixedlast9TP44FP129FN. Physicalhybrid0.81022175 remains SOURCE8only and cannot be mixed into thisfull175table.

Result exported exactbytes outputs/research/exp223_official_score175_v2_20260922/output/result.json, SHA48e85cda0411325c7b420bc5faa9890e78dda33ac4a9beb7a0112b80848be9c0. GateSHA ccdd3606f46b47bb536e3ee88d23ec36bef18ea6d605e725d267c0769384da2a. Exit/processreceipt reports/exp223_official_score_v2_status_20260922.json. Earlierwrapperandrolloutnewlinepin failures preserved; bothbeforeGT, same scientificscorer retained. No resources remain occupied by theseexperiments. No timer/noKagglePOST.
