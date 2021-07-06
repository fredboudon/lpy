#Regular crashes

Here's a list of regular crashes I've come around when compiling, running, debugging Lpy.
Most of them are documented on Linux and Windows but sometimes you can still find them on macOS.

Let's go.

## Lexicum

**clean dev environment**: what you get after this:
```
conda deactivate; conda env remove -y -n lpydev; conda create -y -n lpydev; conda activate lpydev; conda install -c conda-forge -c fredboudon --only-deps -y openalea.lpy
```

**clean install**: what you get after this:
```
conda deactivate; conda env remove -y -n lpy; conda create -y -n lpy; conda activate lpy; conda install -c conda-forge -c fredboudon -y openalea.lpy
```


## The undefined symbol: `_ZSt28__throw_bad_array_new_lengthv`

- trigger:
Any **clean dev environment**, after compilation, trying to launch `lpy` or `python -m openalea.lpy.gui.objectpanel`
- OS: Linux (any recent)
- cause: libstdc++ and, or GCC is too recent! Happens with GCC-11 and Python 3.9.5, but could happend with other versions too.
- workaround: Try using an older version of gcc. Install an older version then do something like this (for example with GCC 7 putting this in your .bashrc)

```
export CC=/usr/bin/gcc-7
export CXX=/usr/bin/gcc-7
``` 

You could maybe get away with installing GCC from conda but I don't trust them too much.

<!--  You can install it with conda: `conda install -c conda-forge gcc_linux-64=9.3.0`
-->

## editor not displaying (staying black)

- trigger: any **clean installation** or **clean dev environment**, trying to open any 3D visualization
- OS: Linux
- branch: master
- cause: you could be running a VM without hardware acceleration or a bug involving Wayland support
- workarond: don't


## Segfault when opening Nurbs3dPatchEditor

- trigger: any **clean dev environment**, open Nurbs3dPatchEditor -> segfault
- OS: at least Linux, maybe all
- branch: master, objectpanel-widgetlist
- cause: unknown
- workaround: unknown
- valgrind trace: [see here](./valgrind-traces/nurbs3dpatcheditor.txt)

## Segfault when opening twice NurbsPatchEditor

- trigger: any **clean dev environment**, open NurbsPatchEditor, cancel, open it again, cancel -> segfault.
- OS: at least Linux, maybe all
- branch: objectpanel-listwidget
- cause: unknown, could be related to double instantiation of libQGLViewer and some memory not free'd
- workaround: unknown
- valgrind trace: [see here](./valgrind-traces/nurbspatcheditortwice.txt)

## Bottom of the QListWidget is glitchy when an editor is instantiated

- trigger: any **clean dev environment**, open objectpanel, edit any object involving libQGLViewer, try to resize objectpanel -> bottom is glitchy
- OS: all
- branch objectpanel-listwidget
- cause: unknown, probably related to libQGLViewer and Qt parent management

## macOS Segfault when closing the window

- trigger: any **clean dev environment** or any **clean install**, close the program -> segfault
- OS: macOS (tested 10.15+)
- cause: unknown (maybe Qt 5.12 is too old)
- workaround: none

## any lpy or plantgl window don't open, or close silently, on Windows

- trigger: any **clean dev environment** or any **clean install**
- OS: Windows (tested on Windows 10), Python 3.9 (default install)
- cause: at first I thought it was a UI issue but even after fixing it it still doesn't open. Weird. It's completely silent so I assume it's "gracefully" closing somewhere without much room for debugging (plus no debugging symbols on Windows **because conda**)
- workaround: none
