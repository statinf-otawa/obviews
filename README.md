# Obviews

**Obviews** (*OTAWA Binary Viewers) allows to displays program representation and statistics produced by OTAWA tools.



## How to run Obviews?

The program representation (including CFG and source) can be produced with tool **dumpcfg**:
```
	$ dumpcfg -W EXECUTABLE [FUNCTION]
```
Arguments between `[`...`]` are optional. As default, the tool applis to function `main`.


To get statistics and views about a WCET calculation, one has to pass the option `-W' and '--stats`:

```
	$ owcet -W --stats EXECUTABLE [FUNCTION]
```

This will result in a directory named `EXECUTABLE/FUNCTION` containing several `.csv`files. To get a display, run the command:
```
	$ PATH/bin/obviews.py EXECUTABLE [FUNCTION]
```

This opens an HTML page where the program representation and its statistics are displayed.

For example, from the test directory, one can type:
```
	$ ..//bin/obviews.py bs.elf
```


# User interface quick guide

There are mainly 3 parts:
* Left pane contains the list of functions and of sources.
* Left-bottom pane displays specific information depending in the chose statistics.
* Main pane contains colored sources or CFGs depending on what is selected in the left pane.

To navigate in the CFG,
* click and move to change the view point,
* mouse wheel or top-right buttons to zoom/unzoom,
* click on a call vertex to move to the CFG of the called function.

In CFG mode, the program representation can be tuned by the `View` button:
1. Select the required representations,
2. And finally click on `Done`.

To select a displayed statistics, click on the `statistic button`and the program representation (CFG or source) becomes colorized according to the intensity of the statistics (darker is stronger). In addition, in CFG mode, the statistics value is displayed in the vertices.

Over the main pane, is displayed the current exposed source file name or function name. In case of CFG, it is also displayed the context of the function call: the list of functions and calls that leads to the displayed CFG and its statistics. The same function may have different statistics with different contexts. This context may be clicked to move to the corresponding CFG or function call. Back button on the right can be used to come back to caller CFG when the navigation has been performed by clicking on function call vertices.



