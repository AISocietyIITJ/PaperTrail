import networkx as nx
from itertools import combinations

def reallocate_seeds(G, initial_seeds, co_occurrence_threshold=2):
    """
    Find papers that are co-cited by multiple initial seeds and add them to the seed list.
    """
    initial_seed_ids = set(p['paperId'] for p in initial_seeds if p.get('paperId'))
    compulsory_nodes = set(initial_seed_ids)
    
    # Check for nodes in G that have high in-degree from the initial seeds
    # Or just high in-degree in the subgraph.
    # Since we added edges as u -> v when u cites v.
    co_cited_counts = {}
    for seed in initial_seed_ids:
        if G.has_node(seed):
            for successor in G.successors(seed):
                co_cited_counts[successor] = co_cited_counts.get(successor, 0) + 1
                
    for node, count in co_cited_counts.items():
        if count >= co_occurrence_threshold:
            compulsory_nodes.add(node)
            
    # Also ensure all compulsory_nodes are actually in G
    valid_compulsory = [n for n in compulsory_nodes if G.has_node(n)]
    return valid_compulsory

def create_undirected_distance_graph(G):
    """
    Convert directed G to undirected and set edge weight = edge.weight + (node.u.weight + node.v.weight)/2
    so that standard shortest path approximates node+edge costs.
    """
    U = G.to_undirected()
    for u, v, data in U.edges(data=True):
        u_w = U.nodes[u].get('weight', 0)
        v_w = U.nodes[v].get('weight', 0)
        e_w = data.get('weight', 1)
        U.edges[u, v]['distance'] = e_w + (u_w + v_w) / 2.0
    return U

def newst_heuristic(G, terminals):
    """
    Node-Edge Weighted Steiner Tree (NEWST) Heuristic.
    """
    import networkx as nx
    from itertools import combinations
    
    if not terminals:
        return nx.Graph()
        
    U = create_undirected_distance_graph(G)
    
    # Steiner tree requires a connected graph.
    # Connect disconnected components with pseudo-edges of high weight.
    components = list(nx.connected_components(U))
    if len(components) > 1:
        print(f"Graph has {len(components)} disconnected components. Adding pseudo-edges to connect them.")
        # Connect the components in a chain to ensure connectivity
        for i in range(len(components) - 1):
            # Pick one terminal from the component if possible, otherwise any node
            comp1 = components[i]
            comp2 = components[i+1]
            u = next(iter(comp1.intersection(terminals)), list(comp1)[0])
            v = next(iter(comp2.intersection(terminals)), list(comp2)[0])
            U.add_edge(u, v, distance=999999)
            
    # Now the graph U is fully connected.
    valid_terminals = list(terminals)
    
    # 1. Metric closure on terminals
    metric_closure = nx.Graph()
    # Add nodes first in case there's only 1 terminal
    for t in valid_terminals:
        metric_closure.add_node(t)
        
    for u, v in combinations(valid_terminals, 2):
        try:
            length = nx.shortest_path_length(U, source=u, target=v, weight='distance')
            metric_closure.add_edge(u, v, weight=length)
        except nx.NetworkXNoPath:
            pass
            
    if metric_closure.number_of_nodes() == 0:
        return nx.Graph()
        
    # 2. MST of metric closure
    mst_metric = nx.minimum_spanning_tree(metric_closure, weight='weight')
    
    # 3. Subgraph of G by replacing edges in MST with shortest paths
    subgraph = nx.Graph()
    for u, v in mst_metric.edges():
        path = nx.shortest_path(U, source=u, target=v, weight='distance')
        nx.add_path(subgraph, path)
        
    # 4. Find MST of the resulting subgraph
    for u, v in subgraph.edges():
        subgraph.edges[u, v]['distance'] = U.edges[u, v]['distance']
        
    final_mst = nx.minimum_spanning_tree(subgraph, weight='distance')
    
    return final_mst
def get_reading_path(G, final_mst):
    """
    Extract a reading path (a linear or topological order) from the Steiner Tree.
    Since MST is undirected, we use the original directed graph G to find a reading order (topological sort).
    """
    # Create a directed subgraph from the original G using the nodes and edges present in final_mst
    directed_subgraph = nx.DiGraph()
    mst_nodes = set(final_mst.nodes())
    for u in mst_nodes:
        directed_subgraph.add_node(u, **G.nodes[u])
        
    for u, v in final_mst.edges():
        if G.has_edge(u, v):
            directed_subgraph.add_edge(u, v)
        elif G.has_edge(v, u):
            directed_subgraph.add_edge(v, u)
            
    # The reading order can be a topological sort. 
    # If there are cycles (rare in citation graphs, but possible), we break them.
    try:
        path = list(nx.topological_sort(directed_subgraph))
    except nx.NetworkXUnfeasible:
        # If there's a cycle, just use a fallback heuristic (e.g. sort by year)
        path = sorted(mst_nodes, key=lambda x: G.nodes[x].get('year') or 0)
        
    return path
