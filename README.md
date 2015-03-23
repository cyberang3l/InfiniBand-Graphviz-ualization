# InfiniBand-Graphviz-ualization
Generate graphviz dot files from InfiniBand topology dumps.

To get an InfiniBand topology dump, use the 'ibnetdiscover' tool and redirect its output in an 'infiniband.topo' file.


# Usage
Use the --help parameter to see a list of the available options.

`./InfiniBand-graphviz.py --help`


The following command will read the "infiniband.topo" InfiniBand topology file, and generate a graphviz dot file.
For further analysis and visualization, you can use Gephi.

`./InfiniBand-graphviz.py -f infiniband.topo`
