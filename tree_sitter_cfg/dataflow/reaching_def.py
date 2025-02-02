from tree_sitter_cfg.dataflow.dataflow_solver import DataflowSolver
import networkx as nx

def get_definition(ast_node):
    identifier = None
    if ast_node.type == "init_declarator":
        identifier = ast_node.children[0].text.decode()
        # rhs = ast_node.children[2].text
    elif ast_node.type == "expression_statement":
        assignment = ast_node.children[0]
        if assignment.type == "assignment_expression":
            identifier = assignment.children[0].text.decode()
            # rhs = assignment.children[2].text
    return identifier

class ReachingDefinitionSolver(DataflowSolver):
    """
    reaching definition
    https://en.wikipedia.org/wiki/Reaching_definition
    """

    def __init__(self, cfg, verbose):
        super().__init__(cfg, verbose)

        node2def = {}
        def2node = {}
        id2def = {}
        def2id = {}
        def2code = {}
        def_idx = 0
        for n in nx.dfs_preorder_nodes(cfg, source=cfg.graph["entry"]):
            ast_node = cfg.nodes[n]["n"]
            _id = get_definition(ast_node)
            print(n, _id)
            if _id is not None:
                node2def[n] = def_idx
                def2node[def_idx] = n

                if _id not in id2def:
                    id2def[_id] = set()
                id2def[_id].add(def_idx)
                def2id[def_idx] = _id
                def2code[def_idx] = ast_node.text.decode()

                def_idx += 1
        if verbose >= 1:
            print("node2def", node2def)
            print("def2node", def2node)
            print("id2def", id2def)
            print("def2id", def2id)
            print("def2code", def2code)
        self.node2def = node2def
        self.def2node = def2node
        self.id2def = id2def
        self.def2id = def2id
        self.def2code = def2code

    def gen(self, n) -> set:
        if n in self.node2def:
            d = self.node2def[n]
            if self.verbose >= 2:
                print("gen", n, d)
            return {d}
        else:
            return set()

    def kill(self, n) -> set:
        if n in self.node2def:
            d = self.node2def[n]
            if d in self.def2id:
                i = self.def2id[d]
                if i in self.id2def:
                    if self.verbose >= 2:
                        print("kill", n, self.id2def[i])
                    return self.id2def[i]
        else:
            return set()
