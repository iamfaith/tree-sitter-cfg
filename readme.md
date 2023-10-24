# tree-sitter-cfg

Convert tree-sitter AST to CFG for C programs.
AST -> CFG algorithm is based on Joern, specifically [CfgCreator.scala](https://github.com/joernio/joern/blob/6df0bbe6afad7f9b04bf0d1877e9797a7cdddcc4/joern-cli/frontends/x2cpg/src/main/scala/io/joern/x2cpg/passes/controlflow/cfgcreation/CfgCreator.scala).

# Try it out

Clone [https://github.com/tree-sitter/tree-sitter-c.git](https://github.com/tree-sitter/tree-sitter-c.git) in the project root.
Then run `python main.py tests/data/example.c --print_ast --cfg --draw`


/home/faith/miniconda3/envs/torch_cuda_11.3/bin/python main.py tests/data/example.c --print_ast --cfg --draw

# Contribue

Open issues: [roadmap.md](./roadmap.md)

# Stress test

File [parse.sh](./tests/vs-joern/parse.sh) runs Joern and tree-sitter side by side to compare performance.
Use [joern-install.sh](./tests/vs-joern/joern-install.sh) to install Joern first.

Benchmark 1: long stupid file - 10,000 lines of `x++`.
Output 2022-06-15 19:44, v1.1.891 of Joern:
```bash
(tree-sitter-py38) benjis@AM:~/code/ts$ bash tests/vs-joern/parse.sh --joern tests/data/10000.c
executing /home/benjis/code/ts/tests/vs-joern/get_func_graph.scala with params=Map(filename -> tests/data/10000.c)
Compiling /home/benjis/code/ts/tests/vs-joern/get_func_graph.scala
creating workspace directory: /home/benjis/code/ts/workspace
Creating project `10000.c` for code at `tests/data/10000.c`
moving cpg.bin.zip to cpg.bin because it is already a database file
Creating working copy of CPG to be safe
Loading base CPG from: /home/benjis/code/ts/workspace/10000.c/cpg.bin.tmp
Code successfully imported. You can now query it using `cpg`.
For an overview of all imported code, type `workspace`.
Adding default overlays to base CPG
The graph has been modified. You may want to use the `save` command to persist changes to disk.  All changes will also be saved collectively on exit
script finished successfully
Some(())

real    0m14.143s
user    0m44.302s
sys     0m1.260s
(tree-sitter-py38) benjis@AM:~/code/ts$ bash tests/vs-joern/parse.sh --tree-sitter tests/data/10000.c

real    0m1.503s
user    0m1.385s
sys     0m0.111s
```

Benchmark 2: [Linux kernel 5.18.4](https://cdn.kernel.org/pub/linux/kernel/v5.x/linux-5.18.4.tar.xz)
Output 2022-06-15 21:51, v1.1.891 of Joern:
```bash
(tree-sitter-py38) benjis@AM:~/code/ts$ time python main.py linux-5.18.4 --cfg --file > output_treesitter.txt

real    9m47.570s
user    9m4.308s
sys     0m5.854s

(base) benjis@AM:~/code/ts$ time ./joern/joern-cli/joern --script ./tests/vs-joern/get_func_graph.scala --params filename=linux-5.18.4
executing /home/benjis/code/ts/tests/vs-joern/get_func_graph.scala with params=Map(filename -> linux-5.18.4)
[34mCompiling /home/benjis/code/ts/tests/vs-joern/get_func_graph.scala[39m
creating workspace directory: /home/benjis/code/ts/workspace
Creating project `linux-5.18.4` for code at `linux-5.18.4`
Killed
Error running shell command: List(/home/benjis/code/ts/joern/joern-cli/c2cpg.sh, linux-5.18.4, --output, /home/benjis/code/ts/workspace/linux-5.18.4/cpg.bin.zip)
Exception in thread "main" java.lang.AssertionError: script errored: 
	at io.joern.console.ScriptExecution.runScript(BridgeBase.scala:253)
	at io.joern.console.ScriptExecution.runScript$(BridgeBase.scala:229)
	at io.joern.joerncli.console.AmmoniteBridge$.runScript(AmmoniteBridge.scala:5)
	at io.joern.console.BridgeBase.runAmmonite(BridgeBase.scala:164)
	at io.joern.console.BridgeBase.runAmmonite$(BridgeBase.scala:146)
	at io.joern.joerncli.console.AmmoniteBridge$.runAmmonite(AmmoniteBridge.scala:5)
	at io.joern.joerncli.console.AmmoniteBridge$.delayedEndpoint$io$joern$joerncli$console$AmmoniteBridge$1(AmmoniteBridge.scala:7)
	at io.joern.joerncli.console.AmmoniteBridge$delayedInit$body.apply(AmmoniteBridge.scala:5)
	at scala.Function0.apply$mcV$sp(Function0.scala:39)
	at scala.Function0.apply$mcV$sp$(Function0.scala:39)
	at scala.runtime.AbstractFunction0.apply$mcV$sp(AbstractFunction0.scala:17)
	at scala.App.$anonfun$main$1(App.scala:76)
	at scala.App.$anonfun$main$1$adapted(App.scala:76)
	at scala.collection.IterableOnceOps.foreach(IterableOnce.scala:563)
	at scala.collection.IterableOnceOps.foreach$(IterableOnce.scala:561)
	at scala.collection.AbstractIterable.foreach(Iterable.scala:926)
	at scala.App.main(App.scala:76)
	at scala.App.main$(App.scala:74)
	at io.joern.joerncli.console.AmmoniteBridge$.main(AmmoniteBridge.scala:5)
	at io.joern.joerncli.console.AmmoniteBridge.main(AmmoniteBridge.scala)
Caused by: io.joern.console.ConsoleException: Error creating project for input path: `linux-5.18.4`

real	499m56.583s
user	1193m14.686s
sys	7m26.020s
```
