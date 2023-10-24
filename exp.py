# %%
import json
from pathlib import Path
import traceback
from tree_sitter_cfg.base_visitor import BaseVisitor
from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.tree_sitter_utils import c_parser
import networkx as nx
from networkx.readwrite import json_graph
import matplotlib.pyplot as plt
import argparse
import os

filename = "test.c"

filename = Path(filename)
# %%

with open(filename, "rb") as f:
    tree = c_parser.parse(f.read())


draw = True
each_function = True
each_function = False
save_file = False

#%%
def draw_cfg(cfg, entry=None):
    print("nodes:", cfg.number_of_nodes(), "edge:", cfg.number_of_edges())
    if cfg.number_of_nodes() > 1000 or cfg.number_of_edges() > 1000:
        print("fuck man I'm not drawing that!")
        return
    pos = nx.spring_layout(cfg, seed=0)
    nx.draw(cfg, pos=pos)
    nx.draw_networkx_labels(cfg, pos=pos, labels={n: attr.get("label", "<NO LABEL>") for n, attr in cfg.nodes(data=True)})
    if entry is not None:
        plt.title(cfg.nodes[entry]["n"].text)
    plt.show()


v = CFGCreator()
print(type(tree), type(tree.root_node))
cfg = v.generate_cfg(tree.root_node)
print(cfg)
if draw:
    if each_function:
        funcs = [n for n, attr in cfg.nodes(data=True) if attr["label"] == "FUNC_ENTRY"]
        for func_entry in funcs:
            func_cfg = nx.subgraph(cfg, nx.descendants(cfg, func_entry) | {func_entry})
            draw_cfg(func_cfg, entry=func_entry)
    else:
        draw_cfg(cfg)

if save_file:
    for n in cfg.nodes():
        del cfg.nodes[n]["n"]
    with open(str(filename) + ".graph.json", "w") as of:
        json.dump(json_graph.node_link_data(cfg, attrs=None), of, indent=2)
# %%
