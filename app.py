import streamlit as st
import rdflib
from rdflib.namespace import RDF, RDFS, SKOS, OWL, XSD, Namespace
from streamlit_agraph import agraph, Node, Edge, Config

# Load RDF Graph
ttl_url = 'https://raw.githubusercontent.com/BIG-MAP/ProjectKnowledgeGraph/main/bigmap.ttl'
g = rdflib.Graph()
g.parse(ttl_url, format='turtle')

# Define namespaces
DATA = Namespace("https://w3id.org/emmo/domain/datamanagement#")
EURIO = Namespace("http://data.europa.eu/s66#")
BIGMAP = Namespace("https://w3id.org/big-map/resource#")
SCHEMA = Namespace("https://schema.org/")
g.bind("data", DATA)
g.bind("eurio", EURIO)
g.bind("bigmap", BIGMAP)
g.bind("schema", SCHEMA)

# Edge types for sidebar
edge_types = {
    "work packages": "bigmap:hasWorkPackage",
    "wp leaders": "bigmap:hasLeadPartner",
    "publications": "schema:citation",
    "results": "eurio:isResultOf",
    "presentations": "bigmap:hasPresentation",
    "people": "eurio:author"
}

# Edge color dictionary
edge_colors = {
    "eurio:hasBeneficiary": "#FF6347",
    "schema:citation": "#4682B4",
    "eurio:isResultOf": "#32CD32",
    "eurio:author": "#FFD700",
    # Additional edges can be added here
}

def get_unique_predicates(graph):
    predicates = set()
    for _, p, _ in graph.triples((None, None, None)):
        predicates.add(graph.qname(p))  # Convert URI to a more readable QName
    return predicates

def main():
    st.title("BIG-MAP Key Demonstrator Explorer")
    kd_options = [f"KD{i}" for i in range(1, 12)]
    selected_kds = st.multiselect("Select KD Numbers", options=kd_options, default=kd_options)

    # Sidebar for predefined edge types
    with st.sidebar:
        st.header("Predefined Edge Options")
        edge_selections = {label: st.toggle(label, True) for label in edge_types.keys()}

    # Collect predicates for selected edges from sidebar
    selected_edges = [edge_types[label] for label, selected in edge_selections.items() if selected]

    # Expander for additional edge types using st.multiselect
    all_predicates = get_unique_predicates(g)
    additional_predicates = [pred for pred in all_predicates if pred not in edge_types.values()]
    with st.expander("Additional Edge Options"):
        selected_additional_edges = st.multiselect("Select Additional Edge Types", options=additional_predicates)

    # Include additional selected edges
    selected_edges.extend(selected_additional_edges)

    if selected_kds and selected_edges:
        nodes, edges = extract_graph(selected_kds, selected_edges)
        config = Config(width=1000, height=800, directed=True, nodeHighlightBehavior=True, highlightColor="#F7A7A6", collapsible=True)
        agraph(nodes=nodes, edges=edges, config=config)
    else:
        st.write("Please select at least one KD number and enable edge types to visualize.")

def extract_graph(focus_labels, selected_edges):
    nodes = []
    edges = []
    node_dict = {}  # Use a dictionary to track added nodes for easier lookup

    # Add specific node that always needs to be displayed
    always_show_node = rdflib.URIRef(BIGMAP["bigmap_bf15e03c_4a6e_3ed2_8c1c_184014344ebf"])
    if str(always_show_node) not in node_dict:
        node_dict[str(always_show_node)] = create_node(always_show_node)
        nodes.append(node_dict[str(always_show_node)])

    # Initially add focus nodes
    for focus_label in focus_labels:
        for s, _, _ in g.triples((None, SKOS.altLabel, rdflib.Literal(focus_label))):
            if str(s) not in node_dict:
                node_dict[str(s)] = create_node(s)
                nodes.append(node_dict[str(s)])

    # Check all nodes for connected edges
    for node in nodes:
        node_uri = rdflib.URIRef(node.id)  # Convert node ID back to URIRef to query graph

        # Check outgoing edges
        for p, o in g.predicate_objects(subject=node_uri):
            predicate_qname = g.qname(p)
            if predicate_qname in selected_edges:
                if str(o) not in node_dict:
                    node_dict[str(o)] = create_node(o)
                    nodes.append(node_dict[str(o)])
                edges.append(Edge(
                    source=str(node_uri),
                    target=str(o),
                    color=edge_colors.get(predicate_qname, "#888888"),
                    width=3
                ))

        # Check incoming edges
        for p, s in g.subject_predicates(object=node_uri):
            predicate_qname = g.qname(p)
            if predicate_qname in selected_edges:
                if str(s) not in node_dict:
                    node_dict[str(s)] = create_node(s)
                    nodes.append(node_dict[str(s)])
                edges.append(Edge(
                    source=str(s),
                    target=str(node_uri),
                    color=edge_colors.get(predicate_qname, "#888888"),
                    width=3
                ))

    return nodes, edges




def create_node(subject):
    label = str(g.value(subject, SKOS.prefLabel) or g.value(subject, RDFS.label) or "")
    url = str(g.value(subject, SCHEMA.url) or "#")
    presentation_icon = "https://raw.githubusercontent.com/BIG-MAP/ProjectKnowledgeGraph/main/assets/img/icon/presentation_icon.png"

    # Check if this node is an object of the relation bigmap:hasPresentation
    is_presentation_node = any(
        True for _, p in g.subject_predicates(object=subject)
        if p == BIGMAP.hasPresentation
    )

    # Decide on image URL based on whether it's a presentation node
    image_url = presentation_icon if is_presentation_node else str(g.value(subject, SCHEMA.logo) or None)
    shape = "circularImage" if image_url else "dot"
    color = None if image_url else "blue"

    return Node(id=str(subject), label=label, url=url, color=color, image=image_url, shape=shape, font_color="#FAFAFA")


if __name__ == "__main__":
    main()
