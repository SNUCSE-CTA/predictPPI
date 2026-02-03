predictPPI
=============================================================

This prototype predicts missing protein-protein interactions (PPIs) by:
1) finding k-defective cliques of size >= q in a PPI network, and
2) treating the missing edges inside those cliques as "noisy/missing" interactions.

Requirements
------------
- Python 3
- `bin/main_edgelist.out` (binary of WODC used to enumerate k-defective cliques)

Inputs
------
- PPI edgelist: space-separated `u v` pairs, zero-based integer node IDs.
- Mapping file: one protein name per line, where line i corresponds to node i.

Example mapping (line-based)
----------------------------
YAL001C
YBR123C
YDR362C
...

Usage
-----
From the repository:

```
python3 predictPPI.py PPI/edgelist.txt PPI/mapping.txt 1 11 
```

Arguments
---------
- `ppi_edgelist`: PPI network edgelist
- `mapping`: mapping file (line i -> protein name for node i)
- `k`: allowed number of missing edges per clique
- `q`: minimum clique size

Optional flags
--------------
- `--out-dir`: output directory (default: `output`)
- `--out-cliques`: output cliques file (default: `output/defective_cliques.txt`)
- `--out-pred`: output predicted edges file (default: `output/predicted_missing_edges.txt`)
- `--bin`: path to `main_edgelist.out` (default: `./bin/main_edgelist.out`)
- `--keep-tmp`: keep temporary files for debugging

Outputs
-------
- `output/defective_cliques.txt`
  - Each line lists protein names in a defective clique, followed by its missing edges.
  - Format: `protein1 protein2 ... proteinN<TAB>missing:p1-p2,p3-p4,...`
- `output/predicted_missing_edges.txt`
  - Each line is a predicted missing edge: `proteinA proteinB`

Notes
-----
- The script cleans up temporary files by default (`tmp/` and `graph.txt`).
- If `main_edgelist.out` is missing or fails, the script raises an error.
