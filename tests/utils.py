from tree_sitter_cfg.base_visitor import BaseVisitor
from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.tree_sitter_utils import c_parser
import networkx as nx
import matplotlib.pyplot as plt

def draw(cfg, dataflow_solution=None, ax=None):
    pos = nx.spring_layout(cfg, seed=0)
    nx.draw_networkx_nodes(cfg, pos=pos, ax=ax)
    double_edges = [(u, v) for u, v in cfg.edges() if u in cfg.successors(v) and v in cfg.successors(u)]
    single_edges = [e for e in cfg.edges() if e not in double_edges]
    nx.draw_networkx_edges(cfg, pos=pos, edgelist=single_edges, ax=ax)
    nx.draw_networkx_edges(cfg, pos=pos, edgelist=double_edges, connectionstyle=f"arc3,rad=0.1")
    nx.draw_networkx_labels(cfg, pos=pos, labels={n: attr.get("label", "<NO LABEL>") for n, attr in cfg.nodes(data=True)}, ax=ax)
    if dataflow_solution is not None:
        nx.draw_networkx_labels(cfg, pos=pos, font_color="r", labels={n: "\n\n\n{" + ", ".join(dataflow_solution[n]) + "}" if dataflow_solution[n] else "" for n in cfg.nodes()}, ax=ax)
    plt.show()


def parse_and_create_cfg(code, print_ast=False, draw_cfg=False):
    tree = c_parser.parse(bytes(code, "utf8"))
    if print_ast:
        ast_v = BaseVisitor()
        ast_v.visit(tree.root_node)
    v = CFGCreator()
    cfg = v.generate_cfg(tree.root_node)
    if draw_cfg:
        draw(cfg)
    return cfg