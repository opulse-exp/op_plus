from collections import defaultdict, deque
from pyvis.network import Network
from operatorplus.operator_manager import OperatorManager
import json
from config import LogConfig, ParamConfig

class OperatorDependencyGraph:
    def __init__(
        self,
        logger: LogConfig,
        operator_manager: "OperatorManager" = None,
    ):
        """
        Initializes the OperatorDependencyGraph class.

        Parameters:
            logger (LogConfig): Logger object for logging operations.
            operator_manager (OperatorManager, optional): An instance of OperatorManager to manage operators and their dependencies (default: None).
        """
        self.logger = logger.get_logger()
        self.operator_manager = operator_manager

    def build_dependency_graph(self):
        """
        Constructs a directed acyclic graph (DAG) representing the operator dependencies.
        
        The graph is built based on the operators managed by the OperatorManager, 
        and a topological sorting of the graph is performed.

        Returns: 
            (tuple(dict[int, list[int]], list[int)): A tuple (graph, topo_sorted), where graph is the adjacency list 
                 representation of the DAG and topo_sorted is the topologically sorted list of operators.
        """
        graph = defaultdict(list)  # Adjacency list to store graph
        in_degree = defaultdict(int)  # Dictionary to store the in-degree of each node

        self.logger.debug("Building the dependency graph.")
        
        # Construct the graph
        for operator_id, operator_info in self.operator_manager.operators.items():
            if operator_info.dependencies:
                for dep_id in operator_info.dependencies:
                    graph[dep_id].append(operator_id)
                    in_degree[operator_id] += 1
                    self.logger.debug(f"Operator {operator_id} depends on {dep_id}.")
            else:
                in_degree[operator_id] = 0  # If no dependencies, set in-degree to 0
                self.logger.debug(f"Operator {operator_id} has no dependencies.")
        
        # Perform topological sorting
        topo_sorted = self.topological_sort(graph, in_degree)
        
        self.logger.info("Dependency graph built successfully.")
        
        return graph, topo_sorted

    def topological_sort(self, graph, in_degree):
        """
        Performs a topological sort on the graph using Kahn's algorithm.

        Parameters:
            graph (dict[int, list[int]]): The adjacency list representation of the graph.
            in_degree (dict[int, int]): A dictionary that tracks the in-degree of each node.
        
        Returns: 
            (list[int]): A topologically sorted list of operators.
        
        Raises:
            ValueError: If the graph contains a cycle, making topological sorting impossible.
        """
        queue = deque([node for node in in_degree if in_degree[node] == 0])
        sorted_order = []

        self.logger.debug("Starting topological sorting.")

        while queue:
            node = queue.popleft()
            sorted_order.append(node)
            self.logger.debug(f"Node {node} added to the sorted order.")
            
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    self.logger.debug(f"Node {neighbor} now has in-degree 0 and is added to the queue.")
        
        if len(sorted_order) != len(in_degree):
            self.logger.error("Graph contains a cycle, topological sorting cannot be performed.")
            raise ValueError("Graph has a cycle, cannot perform topological sorting.")
        
        self.logger.info("Topological sorting completed successfully.")
        
        return sorted_order

    def write_dependency_to_jsonl(self, filename="data/dependency/operator_dependencies.jsonl"):
        """
        Writes the operator dependency graph to a JSONL file.

        Each line in the file represents a node in the graph, with its primitive operator ID 
        and the list of operators derived from it (i.e., its dependencies).

        Parameters:
            filename (str): The name of the output JSONL file. Default is 'operator_dependencies.jsonl'.
        """
        self.logger.info(f"Writing dependency data to {filename}.")
        
        # Get the graph and topological sort
        graph, topo_sorted = self.build_dependency_graph()

        try:
            with open(filename, 'w') as f:
                for node in topo_sorted:
                    node_info = {
                        "primitive_op_id": node,
                        "derived_op_id_list": graph[node]  # List of dependent operators
                    }
                    f.write(json.dumps(node_info) + "\n")
                    self.logger.debug(f"Written node {node} to {filename}.")
            
            self.logger.info(f"Dependency data successfully written to {filename}.")
        
        except Exception as e:
            self.logger.error(f"Error writing to file {filename}: {e}")

    def visualize_dependency_graph(self):
        """
        Visualizes the operator dependency graph using pyvis.

        This method generates an interactive graph that can be explored in a web browser.
        The graph shows the operators and their dependencies, where nodes represent 
        operators and edges represent dependencies between them.

        The graph is saved as an HTML file for viewing.
        """
        self.logger.info("Visualizing the operator dependency graph.")
        
        # Create an interactive network graph
        net = Network(directed=True)

        # Add nodes and edges to the graph
        for operator_id, operator_info in self.operator_manager.operators.items():
            label = f"{operator_id}:{operator_info.symbol}"  # Combine operator ID and symbol
            net.add_node(operator_id, label=label)
            if operator_info.dependencies:
                for dep_id in operator_info.dependencies:
                    net.add_edge(dep_id, operator_id)
                    self.logger.debug(f"Edge added between {dep_id} and {operator_id}.")
        
        net.force_atlas_2based()  # Enable the ForceAtlas2 layout engine, but disable continuous updates
        net.physics = False  # Disable physics engine for static layout
    
        # Save the graph as an HTML file
        try:
            net.show("operator_dependency_graph.html", notebook=False)
            self.logger.info("Dependency graph saved as 'operator_dependency_graph.html'.")
        except Exception as e:
            self.logger.error(f"Error visualizing the dependency graph: {e}")
