# InfiniBand-Graphviz-ualization
Generate graphviz dot files from InfiniBand topology dumps.

To get an InfiniBand topology dump, use the 'ibnetdiscover' tool and redirect its output in an 'infiniband.topo' file.


# Usage
Use the --help parameter to see a list of the available options.

`./InfiniBand-graphviz.py --help`


The following command will read the "infiniband.topo" InfiniBand topology file, and generate a graphviz dot file.
For further analysis and visualization, you can use Gephi.

`./InfiniBand-graphviz.py -f infiniband.topo`

# Create a beautiful graph with [Gephi](http://gephi.github.io/)
If you want to generate a beautiful graph with Gephi, follow the following steps:
  1. Load the generate dot file in Gephi.
  2. Go to the 'Overview' tab and choose a placement layout (I really like the results of 'Force Atlas 3D' algorithm).
  3. Run the layout until you are satisfied with the placement and press stop.
  4. Got the 'Preview window and press the 'Refresh' button.
  5. Under the 'Edges' group, untick the 'Curved' tick box and change the 'Color' of the edges from 'mixed' to 'original'.
  6. Choose a 'black' background if you used the '--optimized-for-black-bg (-o)' option when you ran the script, and press a final refresh.
  7. Once you are satisfied with the result, press the 'Export SVG/PDF/PNG' button to save the layout.
