import networkx as nx
import matplotlib.pyplot as plt


def make_triangle():
    graph = nx.Graph()
    graph.add_nodes_from([0, 1, 2])
    graph.add_edges_from([
        (0, 1),
        (1, 2),
        (0, 2),
    ])
    return graph


def make_k4():
    return nx.complete_graph(4)


def draw_graph(graph, title):
    positions = nx.spring_layout(graph, seed=7)

    nx.draw(
        graph,
        positions,
        with_labels=True,
        node_color="#65c3ba",
        node_size=1200,
        font_size=12,
        edge_color="#555555",
    )

    plt.title(title)
    plt.show()


if __name__ == "__main__":
    triangle = make_triangle()
    k4 = make_k4()

    draw_graph(triangle, "Triangle")
    draw_graph(k4, "K4")