#!/usr/bin/env python3
#
# Copyright (C) 2016 Vangelis Tasoulas <vangelis@tasoulas.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import re
import argparse
import logging
import time
import xml.etree.ElementTree as et
import xml.dom.minidom as md
from collections import OrderedDict
import pygraphviz as pgv


__all__ = [
    'quick_regexp', 'print_',
    'hex_to_rgb', 'LOG'
]

PROGRAM_NAME = 'InfiniBand-Graphviz-ualization'
VERSION = '0.3.0'
AUTHOR = 'Vangelis Tasoulas'

LOG = logging.getLogger('default.' + __name__)

# ###############################################
# ############## HELPER FUNCTIONS ###############
# ###############################################

# ----------------------------------------------------------------------


def error_and_exit(message):
    """
    Prints the "message" and exits with status 1
    """
    print("\nFATAL ERROR:\n" + message + "\n")
    exit(1)

# ----------------------------------------------------------------------


def print_(
        value_to_be_printed, print_indent=0,
        spaces_per_indent=4, endl="\n"):
    """
    This function, among anything else, it will print dictionaries (even nested
    ones) in a good looking way

    # value_to_be_printed: The only needed argument and it is the
                           text/number/dictionary to be printed
    # print_indent: indentation for the printed text (it is used for
                    nice looking dictionary prints) (default is 0)
    # spaces_per_indent: Defines the number of spaces per indent (default is 4)
    # endl: Defines the end of line character (default is \n)

    More info here:
    http://stackoverflow.com/questions/19473085/create-a-nested-dictionary-for-a-word-python?answertab=active#tab-top
    """

    if isinstance(value_to_be_printed, dict):
        for key, value in value_to_be_printed.items():
            if isinstance(value, dict):
                print_('{0}{1!r}:'.format(
                    print_indent * spaces_per_indent * ' ', key))
                print_(value, print_indent + 1)
            else:
                print_('{0}{1!r}: {2}'.format(
                    print_indent * spaces_per_indent * ' ', key, value))
    else:
        string = ('{0}{1}{2}'.format(
            print_indent * spaces_per_indent * ' ', value_to_be_printed, endl))
        sys.stdout.write(string)

# ----------------------------------------------------------------------


def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

# ----------------------------------------------------------------------


class quick_regexp(object):
    """
    Quick regular expression class, which can be used directly in if()
    statements in a perl-like fashion.

    #### Sample code ####
    r = quick_regexp()
    if(r.search('pattern (test) (123)', string)):
        print(r.groups[0]) # Prints 'test'
        print(r.groups[1]) # Prints '123'
    """

    def __init__(self):
        self.groups = None
        self.matched = False

    def search(self, pattern, string, flags=0):
        match = re.search(pattern, string, flags)
        if match:
            self.matched = True
            if match.groups():
                self.groups = re.search(pattern, string, flags).groups()
            else:
                self.groups = True
        else:
            self.matched = False
            self.groups = None

        return self.matched

# ----------------------------------------------------------------------

# #######################################
# ##### Configure logging behavior ######
# #######################################
# No need to change anything here


def _configureLogging(loglevel):
    """
    Configures the default logger.

    If the log level is set to NOTSET (0), the
    logging is disabled

    # More info here: https://docs.python.org/2/howto/logging.html
    """
    numeric_log_level = getattr(logging, loglevel.upper(), None)
    try:
        if not isinstance(numeric_log_level, int):
            raise ValueError()
    except ValueError:
        error_and_exit('Invalid log level: %s\n'
                       '\tLog level must be set to one of the following:\n'
                       '\t   CRITICAL <- Least verbose\n'
                       '\t   ERROR\n'
                       '\t   WARNING\n'
                       '\t   INFO\n'
                       '\t   DEBUG    <- Most verbose' % loglevel)

    defaultLogger = logging.getLogger('default')

    # If numeric_log_level == 0 (NOTSET), disable logging.
    if not numeric_log_level:
        numeric_log_level = 1000
    defaultLogger.setLevel(numeric_log_level)

    logFormatter = logging.Formatter()

    defaultHandler = logging.StreamHandler()
    defaultHandler.setFormatter(logFormatter)

    defaultLogger.addHandler(defaultHandler)

# ######################################################
# ##### Add command line options in this function ######
# ######################################################
# Add the user defined command line arguments in this function


def _command_Line_Options():
    """
    Define the accepted command line arguments in this function

    Read the documentation of argparse for more advanced command line
    argument parsing examples
    http://docs.python.org/2/library/argparse.html
    """

    parser = argparse.ArgumentParser(
        description=PROGRAM_NAME + " version " + VERSION)

    parser.add_argument("-v", "--version",
                        action="version", default=argparse.SUPPRESS,
                        version=VERSION,
                        help="show program's version number and exit")

    loggingGroupOpts = parser.add_argument_group(
        'Logging Options', 'List of optional logging options')
    loggingGroupOpts.add_argument(
        "-q", "--quiet",
        action="store_true",
        default=False,
        dest="isQuiet",
        help="Disable logging in the console. Nothing will be printed.")
    loggingGroupOpts.add_argument(
        "-l", "--loglevel",
        action="store",
        default="INFO",
        dest="loglevel",
        metavar="LOG_LEVEL",
        help=("LOG_LEVEL might be set to: CRITICAL, ERROR,"
              " WARNING, INFO, DEBUG. (Default: INFO)"))

    parser.add_argument(
        "-f", "--topology-file",
        action="store",
        required=True,
        dest="topo_file",
        metavar="TOPOLOGY",
        help="Topology file to load the data from.")
    parser.add_argument(
        "-d", "--detailed-topo",
        action="store_true",
        default=False,
        dest="detailed_topo",
        help=("If the user needs a detailed topology, use 'record' shapes and"
              " draw individual ports on each shape. Note that a detailed"
              " topology might be good for visualization, but it is not"
              " supported by Gephi.\n"
              "Default: False (use 'rectangle' shapes with multiple"
              " connections)."))
    parser.add_argument(
        "-c", "--use-clusters",
        action="store_true",
        default=False,
        dest="use_clusters",
        help=("If enabled, HCAs (nodes) connected to the same switches are"
              " grouped in the same cluster.\n"
              "Unfortunately only 'dot' supports clustering at the moment,"
              " so clustering is disabled by default.\n"
              "Default: False"))
    parser.add_argument(
        "-o", "--optimized-for-black-bg",
        action="store_true",
        default=False,
        dest="optimize_black_bg",
        help=("Gephi can make really good looking graphs on black background."
              " If you are about to plot a final graph on black background"
              " then use this option to optimize the colors for it.\n"
              "Default: False"))
    parser.add_argument(
        "-r", "--render-file",
        action="store_true",
        default=False,
        dest="render_file",
        help=("If enabled, the output will be rendered with the 'neato'"
              " layout, and saved in a PDF file.\n"
              "Default: False"))
    parser.add_argument(
        "-e", "--export-gexf",
        action="store_true",
        default=False,
        dest="export_gexf",
        help=("Support for DOT files in Gephi is really bad. Use this option"
              " to export a gexf file if you want to play with the graph in"
              " Gephi.\n"
              "Default: False"))

    opts = parser.parse_args()

    if opts.isQuiet:
        opts.loglevel = "NOTSET"

    return opts

# #################################################
# ############## WRITE MAIN PROGRAM ###############
# #################################################


if __name__ == '__main__':
    """
    Write the main program here
    """
    # Parse the command line options
    options = _command_Line_Options()
    # Configure logging
    _configureLogging(options.loglevel)

    LOG.info("%s v%s is running...\n", PROGRAM_NAME, VERSION)

    ######################################
    # LOG.critical("CRITICAL messages are printed")
    # LOG.error("ERROR messages are printed")
    # LOG.warning("WARNING messages are printed")
    # LOG.info("INFO message are printed")
    # LOG.debug("DEBUG messages are printed")

    # If the user needs a detailed topology, use "record" shapes and draw
    # individual ports on each shape.
    # Otherwise, use "rectangle" shapes with multiple connections.
    #
    # Unfortunately, a detailed topology is not supported by Gephi.
    # Disabling by default.
    detailed = options.detailed_topo

    # If enabled, HCAs (nodes) connected on the same switches are grouped in
    # the same cluster. Unfortunately only 'dot' supports clustering at the
    # moment, so I disable it by default.
    useClusters = options.use_clusters

    exportGexf = options.export_gexf

    # Read the topology and build the graph in an OrderedDict
    topology_file = options.topo_file
    topology = OrderedDict()
    num_of_switches = 0
    num_of_hcas = 0
    current_node = ""
    with open(topology_file, mode='r', buffering=1) as f:
        for line in f:
            line = line.strip()
            isinstance(line, str)
            if line:
                r = quick_regexp()
                # This regexp will read the name of nodes and the number of
                # ports (Switches or HCAs)
                if r.search(
                        r"^(\w+)\s+(\d+)\s+\"(.+?)\"\s+#\s+\"(.+?)\"", line):
                    current_node = r.groups[2]
                    topology[current_node] = OrderedDict()
                    topology[current_node]['number_of_ports'] = int(
                        r.groups[1])
                    if len(r.groups) == 4:
                        # If we have a label, keep track of it
                        topology[current_node]['label'] = r.groups[3]

                    if r.groups[0] == 'Switch':
                        topology[current_node]['node_type'] = 'switch'
                        num_of_switches = num_of_switches + 1
                    else:
                        topology[current_node]['node_type'] = 'hca'
                        num_of_hcas = num_of_hcas + 1

                # This regexp will read the port lines from a dump
                if r.search(r"^\[(\d+)\].*?\"(.+?)\"\[(\d+)\]", line):
                    local_port = int(r.groups[0])
                    connected_to_remote_host = r.groups[1]
                    connected_to_remote_port = int(r.groups[2])
                    topology[current_node][local_port] = {
                        connected_to_remote_host: connected_to_remote_port}

    # if len(topology) > 1000 and detailed:
    #     LOG.warn(
    #         ("The provided network contains %d nodes (too many) and you"
    #          " have chosen to draw a detailed topology.\n"
    #          "If the drawing state takes much longer than anticipated,"
    #          " please run the program again with the detailed topology"
    #          " switch turned off."), len(topology))

    # print_(topology)

    G = pgv.AGraph(name="Fat-tree", strict=False)

    ################
    # Graphviz attribute list!
    #    www.graphviz.org/doc/info/attrs.html
    ################

    # Graph attributes
    G.graph_attr['rankdir'] = 'TB'  # TB, BT, LR, RL
    G.graph_attr['ranksep'] = 1.0
    # G.graph_attr['nodesep'] = 0.0
    # Type of the edges: (line, false), (spline, true), (none, ""),
    # curved, polyline, ortho
    G.graph_attr['splines'] = 'line'
    # Do not allow nodes to overlap. Scale makes the compilation very fast
    # but spreads the graph!
    G.graph_attr['overlap'] = 'scale'
    # The size of the output image in inches. Use a multiple of 7.75 and 10.25
    # http://stackoverflow.com/questions/3489451/how-to-set-the-width-and-heigth-of-the-ouput-image-in-pygraphviz
    G.graph_attr['size'] = "{},{}!".format(7.75 * 12, 10.25 * 12)
    if options.optimize_black_bg:
        G.graph_attr['bgcolor'] = '#000000'

    # Node Attributes
    G.node_attr['style'] = 'filled'
    G.node_attr['margin'] = 0.2
    G.node_attr['fontsize'] = 24

    # Edge Attributes
    G.edge_attr['penwidth'] = 4

    # Colors
    if options.optimize_black_bg:
        HCA_Color = '#cccccc'
        HCA_Edge_Color = '#ff0000'
        Switch_Color = '#ffffff'
        Switch_Edge_Color = '#a0a0a0'
    else:
        HCA_Color = '#ff8080'
        HCA_Edge_Color = '#ff0000'
        Switch_Color = '#d5f6ff'
        Switch_Edge_Color = '#000000'

    Cluster_Color = "yellow"

    if detailed:
        G.node_attr['shape'] = "Mrecord"
    else:
        G.node_attr['shape'] = "rectangle"

    G.add_nodes_from(topology)

    if exportGexf:
        # gephi_edge_id = G.number_of_nodes()
        gephi_edge_id = 0
        root_node = et.Element('gexf')
        root_node.attrib['xmlns'] = "http://www.gexf.net/1.3"
        root_node.attrib['version'] = "1.3"
        root_node.attrib['xmlns:viz'] = "http://www.gexf.net/1.3/viz"
        root_node.attrib['xmlns:xsi'] = (
            "http://www.w3.org/2001/XMLSchema-instance")
        root_node.attrib['xsi:schemaLocation'] = (
            "http://www.gexf.net/1.3 http://www.gexf.net/1.3/gexf.xsd")
        meta_node = et.SubElement(
            root_node, 'meta', attrib={
                'lastmodifieddate': time.strftime("%Y-%m-%d")
            }
        )
        creator_node = et.SubElement(meta_node, 'creator')
        creator_node.text = PROGRAM_NAME
        description_node = et.SubElement(meta_node, 'description')
        description_node.text = "Graph generated from file '{}'".format(
            os.path.realpath(topology_file))
        graph_node = et.SubElement(root_node, 'graph')
        graph_node.attrib['defaultedgetype'] = "undirected"
        graph_node.attrib['mode'] = "static"
        nodes_node = et.SubElement(graph_node, 'nodes')
        edges_node = et.SubElement(graph_node, 'edges')

    # Cluster id for the subgraphs
    if useClusters:
        global_cluster_id = 0

    # Add ports and edges
    for node in G.nodes():
        if useClusters:
            Subgraph_For_Current_Switch = None

        numPorts = topology[node.name]['number_of_ports']
        if topology[node.name]['node_type'] == 'switch':
            node.attr['fillcolor'] = Switch_Color
            node.attr['color'] = Switch_Color
        elif topology[node.name]['node_type'] == 'hca':
            node.attr['fillcolor'] = HCA_Color
            node.attr['color'] = HCA_Color

        label = topology[node.name]['label'] if 'label' in topology[node.name] else node.name
        if exportGexf:
            node_node = et.SubElement(
                nodes_node, 'node', attrib={
                    'id': node.name, 'label': label
                }
            )
            r, g, b = hex_to_rgb(node.attr['color'])
            et.SubElement(
                node_node, 'viz:color', attrib={
                    'r': str(r), 'g': str(g), 'b': str(b), 'a': "0.0"
                }
            )

        if numPorts > 0:
            for port in range(1, numPorts + 1):
                if detailed:
                    if port == 1:
                        separator = ""
                    else:
                        separator = "|"
                    label = "{}|<{}> {}".format(label, port, port)

                if port in topology[node.name].keys():
                    remote_port = list(topology[node.name][port].values())[0]
                    remote_host = list(topology[node.name][port].keys())[0]
                    try:
                        # Check if there is already a link established...
                        # If not, the 'get_edge' command will raise a
                        # KeyError exception and a new edge will be added
                        G.get_edge(remote_host, node.name,
                                   key="{}-{}".format(port, remote_port))
                    except KeyError:
                        if detailed:
                            G.add_edge(
                                node.name,
                                remote_host,
                                key="{}-{}".format(remote_port, port),
                                headport=remote_port,
                                tailport=port)
                        else:
                            G.add_edge(node.name, remote_host,
                                       key="{}-{}".format(remote_port, port))

                        edge = G.get_edge(
                            node.name, remote_host, key="{}-{}".format(
                                remote_port, port))
                        if topology[remote_host]['node_type'] == 'hca':
                            edge.attr['color'] = HCA_Edge_Color
                            if useClusters:
                                if Subgraph_For_Current_Switch is None:
                                    Subgraph_For_Current_Switch = G.subgraph(
                                        remote_host, 'cluster{}'.format(
                                            global_cluster_id))
                                    Subgraph_For_Current_Switch.graph_attr[
                                        'fillcolor'] = Cluster_Color
                                    Subgraph_For_Current_Switch.graph_attr[
                                        'style'] = 'filled'
                                    global_cluster_id = global_cluster_id + 1
                                else:
                                    Subgraph_For_Current_Switch.add_node(
                                        remote_host)
                        else:
                            # Else the node connects two switches.
                            edge.attr['color'] = Switch_Edge_Color

                        if exportGexf:
                            gephi_edge_id += 1
                            edge_node = et.SubElement(
                                edges_node, 'edge',
                                attrib={'id': str(gephi_edge_id),
                                        'source': node.name,
                                        'target': remote_host,
                                        'label': "{} -- {}".format(
                                            node.name, remote_host)})
                            r, g, b = hex_to_rgb(edge.attr['color'])
                            et.SubElement(
                                edge_node, 'viz:color', attrib={
                                    'r': str(r), 'g': str(g), 'b': str(b)})

        node.attr['label'] = label

    # print(G.string())
    LOG.info(("Total number of nodes: %d\n"
              "Total number of Switches: %d\n"
              "Total number of HCAs: %d\n"
              "Total number of Edges: %d"),
             num_of_hcas + num_of_switches,
             num_of_switches,
             num_of_hcas,
             len(G.edges()))

    output_filename = os.path.basename(topology_file)
    dot_filename = "{}.dot".format(output_filename)
    G.write(dot_filename)

    LOG.info(
        "The dot file has been saved in the file '%s'.", dot_filename)

    if options.render_file:
        # twopi, gvcolor, wc, ccomps, tred, sccmap, fdp, circo, neato, acyclic,
        # nop, gvpr, dot, sfdp
        drawing_args = ''
        G.layout(prog='neato', args=drawing_args)
        # 'canon', 'cmap', 'cmapx', 'cmapx_np', 'dia', 'dot',
        # 'fig', 'gd', 'gd2', 'gif', 'hpgl', 'imap', 'imap_np',
        # 'ismap', 'jpe', 'jpeg', 'jpg', 'mif', 'mp', 'pcl', 'pdf',
        # 'pic', 'plain', 'plain-ext', 'png', 'ps', 'ps2', 'svg',
        # 'svgz', 'vml', 'vmlz', 'vrml', 'vtx', 'wbmp', 'xdot', 'xlib'
        render_filename = "{}.pdf".format(output_filename)
        G.draw(render_filename)

        LOG.info("The rendered file has been saved in the file '%s'.",
                 render_filename)

        # Use command line to debug long executing drawings:
        # dot -Tpdf -Gnslimit=1000 k-18-n-3.topology.dot -v -O

    if exportGexf:
        gexf_filename = "{}.gexf".format(output_filename)
        xml_ugly = et.tostring(root_node, encoding='UTF-8', method='xml')
        xml = md.parseString(xml_ugly)
        with open(gexf_filename, 'wb') as f:
            f.write(xml.toprettyxml(indent="  ", newl="\n", encoding='UTF-8'))

        LOG.info(
            "The gexf file has been saved in the file '%s'.", gexf_filename)
        LOG.info(("\nIf you want to generate a beautiful graph with Gephi,"
                  " follow the following steps:\n"
                  "  1. Load the file '%s' in Gephi.\n"
                  "  2. Go to the 'Overview' tab and choose a placement layout"
                  " (I like the results of 'ForceAtlas 2' algorithm).\n"
                  "  3. Tune as needed and run the layout until you are"
                  " satisfied with the placement and press stop.\n"
                  "  4. Go to the 'Preview' tab and press the 'Refresh'"
                  " button.\n"
                  "  5. Under the 'Edges' group, untick the 'Curved' tick box"
                  " and change the 'Color' of the edges from 'mixed' to"
                  " 'original'\n"
                  "  6. Choose a 'black' background if you used the"
                  " '--optimized-for-black-bg (-o)' option, and press a final"
                  " refresh.\n"
                  "  7. Once you are satisfied with the result, press the"
                  " 'Export SVG/PDF/PNG' button to save the layout.\n"),
                 gexf_filename)
