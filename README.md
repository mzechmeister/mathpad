# mathpad
Simple editor with **inline** math.

Demo: https://raw.githack.com/mzechmeister/mathpad/main/index.html

Uses [MathQuill](http://mathquill.com) in a `contenteditable` html element.

The editor aims for a fast drafting of math ideas and derivations having many tedious equation. The resulting text snippets with latex code can be copied back to a more elaborated pad or markdown editors, which usually only provides latex math or pop-up math widgets.
`mathpad` is only a proof of concept. Enjoy.

## Usage

Just clone the repo, open the `index.html` in the browser and you can start editing. There are three options for saving the pad:
1. The pad can be down- and uploaded.
1. It can be saved in the browser with [`localStorage`](https://www.w3schools.com/html/tryit.asp?filename=tryhtml5_webstorage_local_clickcount).
1. When running `./server.py`, the pad can be stored in a subfolder `data` on hard drive.
