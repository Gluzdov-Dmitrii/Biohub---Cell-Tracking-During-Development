# Biohub EXP209 pooled-OOF frontier model pack

Private runtime pack for the production audit of EXP209. It contains the two
reciprocal competition-trained fold checkpoints, the independently trained
reverse-fold DeepCenter gap gate, exact postprocessing modules, and a SHA-256
manifest. It contains no competition images, labels, cached predictions, or
submission files.

The validated score `0.6815218332750073` is a 175-movie reciprocal
embryo-held-out pooled OOF score. Hidden embryos are unseen, so the production
runner must not claim that number as an exact score for its label-free
unknown-embryo routing rule.
