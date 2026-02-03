import argparse
import os
import shutil
import subprocess
import sys


def load_adj(edgelist_path):
  adj = set()
  with open(edgelist_path, "r") as gfile:
    for line in gfile.readlines():
      if not line.strip():
        continue
      u, v = map(int, line.strip().split())
      adj.add((u, v))
      adj.add((v, u))  # ensure undirected edges
  return adj


def load_mapping(mapping_path):
  with open(mapping_path, "r") as f:
    names = [line.strip() for line in f.readlines() if line.strip()]
  return names


def id_to_name(names, node_id):
  if 0 <= node_id < len(names):
    return names[node_id]
  return str(node_id)


def parse_res(res_path):
  with open(res_path, "r") as f:
    lines = f.readlines()
  if len(lines) < 11:
    raise RuntimeError(
      f"Result file {res_path} is incomplete (lines={len(lines)}). "
      "Did main_edgelist.out run successfully?"
    )
  mapping1 = list(map(int, lines[3].strip().split()))
  mapping2 = list(map(int, lines[7].strip().split()))
  rmapping2 = {v: i for i, v in enumerate(mapping2)}
  mapping2 = [rmapping2[i] for i in range(len(mapping2))]

  cliques = []
  for l in lines[10:]:
    if l[0] == "#":
      break
    clique = list(map(int, l.strip().split()))
    clique = [mapping1[mapping2[u]] for u in clique]
    cliques.append(clique)
  return cliques


def main():
  parser = argparse.ArgumentParser(
    description="Predict missing edges in a PPI network using k-defective cliques."
  )
  parser.add_argument("ppi_edgelist", help="PPI network edgelist (u v per line)")
  parser.add_argument("mapping", help="mapping file (line i -> protein name for node i)")
  parser.add_argument("k", type=int, help="k for k-defective clique")
  parser.add_argument("q", type=int, help="minimum clique size (q)")
  parser.add_argument(
    "--out-dir", default="output", help="output directory (default: output)"
  )
  parser.add_argument(
    "--out-cliques", default=None, help="output cliques file (default: out-dir/cliques.txt)"
  )
  parser.add_argument(
    "--out-pred",
    default=None,
    help="output predicted edges (default: out-dir/predicted_missing_edges.txt)",
  )
  parser.add_argument(
    "--bin",
    default=None,
    help="path to main_edgelist.out (default: ./bin/main_edgelist.out)",
  )
  parser.add_argument(
    "--keep-tmp", action="store_true", help="keep tmp/res.txt for inspection"
  )
  args = parser.parse_args()

  script_dir = os.path.dirname(os.path.abspath(__file__))
  repo_dir = os.path.abspath(os.path.join(script_dir, "."))
  home = script_dir
  os.system(f"mkdir -p {home}/tmp")
  res_path = f"{home}/tmp/res.txt"
  bin_path = args.bin or os.path.join(repo_dir, "bin", "main_edgelist.out")
  if not os.path.exists(bin_path):
    raise FileNotFoundError(f"Missing binary: {bin_path}")

  with open(res_path, "w") as out_f:
    subprocess.run(
      [bin_path, args.ppi_edgelist, str(args.k), str(args.q)],
      check=True,
      stdout=out_f,
      cwd=home,
    )

  adj = load_adj(args.ppi_edgelist)
  names = load_mapping(args.mapping)

  out_dir = args.out_dir
  os.system(f"mkdir -p {out_dir}")
  out_cliques = args.out_cliques or os.path.join(out_dir, "defective_cliques.txt")
  out_pred = args.out_pred or os.path.join(out_dir, "predicted_missing_edges.txt")
  cliques = parse_res(res_path)

  missing_edges = set()
  kept_cliques = 0

  with open(out_cliques, "w") as out_c:
    for clique in cliques:
      if len(clique) < args.q:
        continue
      num_mis = 0
      clique_missing = []
      for i in range(len(clique)):
        for j in range(i + 1, len(clique)):
          if (clique[i], clique[j]) not in adj:
            num_mis += 1
            u, v = clique[i], clique[j]
            if u > v:
              u, v = v, u
            missing_edges.add((u, v))
            clique_missing.append((u, v))
      assert num_mis <= args.k
      kept_cliques += 1
      clique_str = " ".join(id_to_name(names, n) for n in clique)
      if clique_missing:
        miss_str = ",".join(
          f"{id_to_name(names, u)}-{id_to_name(names, v)}" for u, v in clique_missing
        )
      else:
        miss_str = ""
      out_c.write(f"{clique_str}\tmissing:{miss_str}\n")

  with open(out_pred, "w") as out_p:
    for u, v in sorted(missing_edges):
      out_p.write(f"{id_to_name(names, u)} {id_to_name(names, v)}\n")

  if not args.keep_tmp:
    try:
      os.remove(res_path)
    except OSError:
      pass
    try:
      shutil.rmtree(os.path.join(home, "tmp"))
    except OSError:
      pass
    try:
      os.remove(os.path.join(home, "graph.txt"))
    except OSError:
      pass

  print(f"cliques_written {kept_cliques}")
  print(f"predicted_missing_edges {len(missing_edges)}")
  print(f"cliques_file {out_cliques}")
  print(f"pred_file {out_pred}")


if __name__ == "__main__":
  sys.exit(main())
