import streamlit as st
import rdflib
from rdflib.namespace import RDF, RDFS, SKOS, OWL, XSD, Namespace
from streamlit_agraph import agraph, Node, Edge, Config

# Edge color dictionary
edge_colors = {
    "eurio:isResultOf": "#FF6347",  # Tomato
    "eurio:isPartOf": "#4682B4",    # SteelBlue
    "eurio:isRelatedTo": "#32CD32", # LimeGreen
    "eurio:isManagedBy": "#FFD700", # Gold
    # Define other edge types and their colors as needed
}


# Load RDF Graph
ttl_url = 'https://raw.githubusercontent.com/BIG-MAP/ProjectKnowledgeGraph/main/bigmap.ttl'
g = rdflib.Graph()
g.parse(ttl_url, format='turtle')

# Define necessary namespaces
DATA = Namespace("https://w3id.org/emmo/domain/datamanagement#")
EURIO = Namespace("http://data.europa.eu/s66#")
BIGMAP = Namespace("https://w3id.org/big-map/resource#")
SCHEMA = Namespace("https://schema.org/")

# Bind namespaces
g.bind("data", DATA)
g.bind("eurio", EURIO)
g.bind("bigmap", BIGMAP)
g.bind("schema", SCHEMA)

# Extract all unique predicates (edge types) from the graph
def get_unique_predicates(graph):
    predicates = set()
    for _, p, _ in graph.triples((None, None, None)):
        predicates.add(graph.qname(p))  # Convert URI to a more readable QName
    return sorted(predicates)  # Sort for consistent ordering

unique_predicates = get_unique_predicates(g)

def extract_graph(focus_labels, edge_types):
    nodes = []
    edges = []
    visited = set()

    for focus_label in focus_labels:
        for s, _, o in g.triples((None, SKOS.altLabel, rdflib.Literal(focus_label))):
            if s not in visited:
                visited.add(s)
                label = str(g.value(s, SKOS.prefLabel) or g.value(s, RDFS.label) or "No Label")
                # Use schema:url if available, otherwise default to "#"
                node_url = str(g.value(s, EURIO.url) if g.value(s, EURIO.url) else "#")
                image_url = str(g.value(s, SCHEMA.logo) or None)
                node_shape = "circularImage" if image_url else "dot"
                node_color = None if image_url else "blue"

                nodes.append(Node(
                    id=str(s),
                    label=label,
                    url=node_url,  # Set to schema:url or fallback to "#"
                    color=node_color,
                    image=image_url,
                    shape=node_shape
                ))

                for p, o in g.predicate_objects(subject=s):
                    predicate_qname = g.qname(p)
                    if predicate_qname in edge_types:
                        edge_color = edge_colors.get(predicate_qname, "#888888")  # Default color if not defined
                        edge_width = 3  # Edge thickness

                        if o not in visited:
                            visited.add(o)
                            o_label = str(g.value(o, SKOS.prefLabel) or g.value(o, RDFS.label) or "No Label")
                            o_node_url = str(g.value(o, EURIO.url) if g.value(o, EURIO.url) else "#")
                            o_image_url = str(g.value(o, SCHEMA.logo) or None)
                            o_node_shape = "circularImage" if o_image_url else "dot"
                            o_node_color = None if o_image_url else "red"

                            nodes.append(Node(
                                id=str(o),
                                label=o_label,
                                url=o_node_url,  # Set to schema:url or fallback to "#"
                                color=o_node_color,
                                image=o_image_url,
                                shape=o_node_shape
                            ))
                        edges.append(Edge(
                            source=str(s),
                            target=str(o),
                            color=edge_color,
                            width=edge_width
                        ))

    return nodes, edges





def main():
    st.title("BIG-MAP Key Demonstrator Explorer")
    kd_options = [f"KD{i}" for i in range(1, 12)]
    selected_kds = st.multiselect("Select KD Numbers", options=kd_options, default=kd_options)

    with st.expander("Edge Options"):
        selected_edge_types = st.multiselect("Select Edge Types to Display", options=unique_predicates, default=["eurio:isResultOf"])

    if selected_kds and selected_edge_types:
        nodes, edges = extract_graph(selected_kds, selected_edge_types)
        config = Config(width=1000, height=800, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6", collapsible=True)
        agraph(nodes=nodes, edges=edges, config=config)
    else:
        st.write("Please select at least one KD number and one type of edge to visualize.")

if __name__ == "__main__":
    main()
