#!/usr/bin/env python

import os
import sys

import pprint
import networkx as nx
import itertools

# -----------------------------------------------------------------------------
#   Constants.
# -----------------------------------------------------------------------------
ROOT_URI = "http://www.metafilter.com"

CURRENT_DIR = os.path.join(__file__, os.pardir)

DATA_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir, "data"))
FAVORITES_GML_OUTPUT_PATH = os.path.abspath(os.path.join(DATA_DIR, "favorites.gml"))
COMMENTS_GML_OUTPUT_PATH = os.path.abspath(os.path.join(DATA_DIR, "comments.gml"))
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
#   Possible metrics to look at:
#   -   Nodes.
#   -   Edges.
#   -   Nodes in largest connected component (in indirected case weakest
#       same as strongest).
#   -   Average clustering coefficient.
#   -   Number of triangles (number of triples of connected nodes, considering
#       graph as undirected).
#   -   Fraction of closed triangles (number of triangles / number of
#       undirected length 2 paths).
#   -   Diameter (maximum undirected shortest path length, sampled over 1000
#       nodes if necessary).
#   -   90-percentile effective diameter: 90th percentile of undirected
#       shortest path length (sampled over 1000 random nodes).
# -----------------------------------------------------------------------------

def output_metrics(graph, name):
    print '-' * 79
    print "Metrics for graph: %s" % name
    print '-' * 79

def main():
    favorites_graph = nx.read_gml(FAVORITES_GML_OUTPUT_PATH)
    output_metrics(favorites_graph)
    favorites_graph = None

    comments_graph = nx.read_gml(COMMENTS_GML_OUTPUT_PATH)
    output_metrics(comments_graph)
    comments_graph = None

if __name__ == "__main__":
    main()
