from tree_sitter_cfg.base_visitor import BaseVisitor
import networkx as nx

def assert_boolean_expression(n):
    assert n.type.endswith("_statement") or n.type.endswith("_expression") or n.type in ("true", "false", "identifier"), n.type
def assert_branch_target(n):
    assert n.type.endswith("_statement") or n.type.endswith("_expression") or n.type in ("else",), n.type

class CFGCreator(BaseVisitor):
    """
    AST visitor which creates a CFG.
    After traversing the AST by calling visit() on the root, self.cfg has a complete CFG.
    """

    def __init__(self):
        super(CFGCreator).__init__()

    def generate_cfg(self, ast_root_node):
        self.cfg = nx.DiGraph()
        self.node_id = 0
        self.fringe = []
        self.break_fringe = []
        self.continue_fringe = []
        self.visit(ast_root_node)
        cfg = self.cfg
        # Postprocessing

        # pass through dummy nodes
        nodes_to_remove = []
        for n, attr in cfg.nodes(data=True):
            if attr.get("dummy", False):
                preds = list(cfg.predecessors(n))
                succs = list(cfg.successors(n))
                for pred in preds:
                    for succ in succs:
                        cfg.add_edge(pred, succ)
                nodes_to_remove.append(n)
        cfg.remove_nodes_from(nodes_to_remove)
        return cfg
    
    def add_dummy_node(self):
        """dummy nodes are nodes whose connections should be forwarded in a post-processing step"""
        node_id = self.node_id
        self.cfg.add_node(node_id, dummy=True)
        self.node_id += 1
        return node_id
    
    def add_cfg_node(self, ast_node, label=None):
        node_id = self.node_id
        if label is None:
            label = f"{node_id}: {ast_node.type} ({ast_node.start_point}, {ast_node.end_point})\n`{ast_node.text.decode()}`"
        self.cfg.add_node(node_id, n=ast_node, label=label)
        self.node_id += 1
        return node_id
    
    def add_edge_from_fringe_to(self, node_id):
        # TODO: assign edge type
        self.cfg.add_edges_from(zip(self.fringe, [node_id] * len(self.fringe)))
        self.fringe = []
    
    """
    VISITOR RULES
    """

    def visit_function_definition(self, n, **kwargs):
        entry_id = self.add_cfg_node(n, "FUNC_ENTRY")
        self.cfg.graph["entry"] = entry_id
        self.fringe.append(entry_id)
        self.visit_children(n, **kwargs)
        exit_id = self.add_cfg_node(n, "FUNC_EXIT")
        self.add_edge_from_fringe_to(exit_id)
        for n in nx.descendants(self.cfg, entry_id):
            attr = self.cfg.nodes[n]
            if attr.get("n", None) is not None and attr["n"].type == "return_statement":
                self.cfg.add_edge(n, exit_id)

    def visit_default(self, n, indentation_level, **kwargs):
        self.visit_children(n, indentation_level)

    """STRAIGHT LINE STATEMENTS"""

    def enter_statement(self, n):
        node_id = self.add_cfg_node(n)
        self.add_edge_from_fringe_to(node_id)
        self.fringe.append(node_id)

    def visit_expression_statement(self, n, **kwargs):
        self.enter_statement(n)
        self.visit_default(n, **kwargs)

    def visit_init_declarator(self, n, **kwargs):
        self.enter_statement(n)
        self.visit_default(n, **kwargs)

    """STRUCTURED CONTROL FLOW"""

    def visit_if_statement(self, n, **kwargs):
        condition = n.children[1].children[1]
        assert_boolean_expression(condition)
        condition_id = self.add_cfg_node(condition)
        self.add_edge_from_fringe_to(condition_id)
        self.fringe.append(condition_id)

        compound_statement = n.children[2]
        assert_branch_target(compound_statement)
        self.visit(compound_statement)
        # NOTE: this assert doesn't work in the case of an if with an empty else
        # assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"

        if n.children is not None and len(n.children) > 4:
            # print("------------------------------", type(n.children), n.children[3], len(n.children))
            else_compound_statement = n.children[4]
            assert_branch_target(else_compound_statement)
            old_fringe = self.fringe
            self.fringe = [condition_id]
            self.visit(else_compound_statement)
            self.fringe = old_fringe + self.fringe
        else:
            self.fringe.append(condition_id)

    def visit_for_statement(self, n, **kwargs):
        initial_offset = 2
        init = n.children[initial_offset]
        if init.type == ";":
            init = None
        else:
            assert init.type in ("declaration", "assignment_expression", "comma_expression"), init.type
        initial_offset += 1
        if init is not None and init.type != "declaration":
            initial_offset += 1
        cond = n.children[initial_offset]
        if cond.type == ";":
            cond = None
            initial_offset += 1
        else:
            initial_offset += 2
            assert_boolean_expression(cond)
        incr = n.children[initial_offset]
        if incr.type == ")":
            initial_offset += 1
            incr = None
        else:
            initial_offset += 2
            assert incr.type in ("update_expression", "binary_expression", "call_expression"), incr.type

        if cond is not None:
            cond_id = self.add_cfg_node(cond)
        else:
            cond_id = self.add_cfg_node(None, f"<TRUE>")

        if init is not None:
            init_id = self.add_cfg_node(init)
            self.add_edge_from_fringe_to(init_id)
            self.cfg.add_edge(init_id, cond_id)
        else:
            self.add_edge_from_fringe_to(cond_id)
        self.fringe.append(cond_id)

        compound_statement = n.children[initial_offset]
        assert_branch_target(compound_statement)
        self.visit(compound_statement)
        # NOTE: this assert doesn't work in the case of an if with an empty else
        # assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"
        if incr is not None:
            incr_id = self.add_cfg_node(incr)
            self.add_edge_from_fringe_to(incr_id)
            self.cfg.add_edge(incr_id, cond_id)
            self.cfg.add_edges_from(zip(self.continue_fringe, [incr_id] * len(self.continue_fringe)))
            self.continue_fringe = []
        else:
            self.add_edge_from_fringe_to(cond_id)
            self.cfg.add_edges_from(zip(self.continue_fringe, [cond_id] * len(self.continue_fringe)))
            self.continue_fringe = []
        self.fringe.append(cond_id)

        self.fringe += self.break_fringe
        self.break_fringe = []

    def visit_while_statement(self, n, **kwargs):
        cond = n.children[1].children[1]
        
        assert_boolean_expression(cond)

        cond_id = self.add_cfg_node(cond)

        self.add_edge_from_fringe_to(cond_id)
        self.fringe.append(cond_id)

        compound_statement = n.children[2]
        assert_branch_target(compound_statement)
        self.visit(compound_statement)
        # NOTE: this assert doesn't work in the case of an if with an empty else
        # assert len(self.fringe) == 1, "fringe should now have last statement of compound_statement"
        self.add_edge_from_fringe_to(cond_id)
        self.fringe.append(cond_id)

        self.cfg.add_edges_from(zip(self.continue_fringe, [cond_id] * len(self.continue_fringe)))
        self.continue_fringe = []
        self.fringe += self.break_fringe
        self.break_fringe = []

    def visit_do_statement(self, n, **kwargs):
        dummy_id = self.add_dummy_node()
        self.add_edge_from_fringe_to(dummy_id)
        self.fringe.append(dummy_id)

        compound_statement = n.children[1]
        assert_branch_target(compound_statement)
        self.visit(compound_statement)

        cond = n.children[3].children[1]
        
        assert_boolean_expression(cond)

        cond_id = self.add_cfg_node(cond)
        self.add_edge_from_fringe_to(cond_id)
        self.cfg.add_edge(cond_id, dummy_id)
        self.fringe.append(cond_id)

        self.cfg.add_edges_from(zip(self.continue_fringe, [cond_id] * len(self.continue_fringe)))
        self.continue_fringe = []
        self.fringe += self.break_fringe
        self.break_fringe = []

    def visit_switch_statement(self, n, **kwargs):
        cond = n.children[1].children[1]
        cond_id = self.add_cfg_node(cond)
        self.add_edge_from_fringe_to(cond_id)
        cases = n.children[2].children[1:-1]
        default_was_hit = False
        for case in cases:
            if len(case.children) == 0:
                continue
            if case.children[0].type == "default":
                default_was_hit = True
                case_body_idx = 2
            else:
                case_body_idx = 3
            self.fringe.append(cond_id)
            for case_body in case.children[case_body_idx:]:
                should_continue = self.visit(case_body)
                if should_continue == False:
                    break
        if not default_was_hit:
            self.fringe.append(cond_id)
        self.fringe += self.break_fringe
        self.break_fringe = []

    def visit_return_statement(self, n, **kwargs):
        node_id = self.add_cfg_node(n)
        self.add_edge_from_fringe_to(node_id)
        self.visit_default(n, **kwargs)
        # This is meant to skip adding subsequent statements to the CFG.
        # TODO: consider how to handle this with goto statements.
        return False

    def visit_break_statement(self, n, **kwargs):
        node_id = self.add_cfg_node(n)
        self.add_edge_from_fringe_to(node_id)
        self.break_fringe.append(node_id)
        self.visit_default(n, **kwargs)
        return False

    def visit_continue_statement(self, n, **kwargs):
        node_id = self.add_cfg_node(n)
        self.add_edge_from_fringe_to(node_id)
        self.continue_fringe.append(node_id)
        self.visit_default(n, **kwargs)
        return False
