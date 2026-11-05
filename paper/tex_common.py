import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=json.load(open(ROOT/'results'/'results.json'))
PAR=D['params']
E=lambda v:f'{v:,.0f}\\,\\texteuro{{}}'.replace(',','{,}') if False else f'{v:,.0f}\\,\\texteuro{{}}'
def n0(v): return f'{v:,.0f}'
def n1(v): return f'{v:,.1f}'
def n2(v): return f'{v:,.2f}'
def n3(v): return f'{v:.3f}'
def pc(v,d=1): return f'{v*100:.{d}f}\\%'
PRE=r'''\documentclass[10pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage{lmodern,textcomp}
\usepackage[margin=2.4cm]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{graphicx,booktabs,array,float}
\usepackage[hidelinks]{hyperref}
\usepackage{microtype}
\setlength{\parskip}{3pt}
\newtheorem{proposition}{Proposition}
\newtheorem{definition}{Definition}
\renewcommand{\arraystretch}{1.1}
\begin{document}
'''
import re
def _fixlabels(t): return re.sub(r'\\label\{([^}]*)\}\\caption\{(.*?)\}\\end\{figure\}',lambda m:'\\caption{'+m.group(2)+'}\\label{'+m.group(1)+'}\\end{figure}',t,flags=re.S)
def make(title,subtitle,abstract,body,refs):
    return _fixlabels(PRE+r'\title{\bfseries '+title+r'\\[2pt]\large '+subtitle+'}\n\\author{Humbert Pou Plana}\n\\date{November 2026}\n\\maketitle\n'
            +'\\begin{abstract}\n'+abstract+'\n\\end{abstract}\n'+body+'\n\\begin{thebibliography}{9}\n'+refs+'\n\\end{thebibliography}\n\\end{document}\n')
def fig(name,cap,w='0.92'):
    return '\\begin{figure}[H]\\centering\\includegraphics[width='+w+'\\linewidth]{fig/'+name+'.pdf}\\caption{'+cap+'}\\end{figure}\n'
def esc(s): return s.replace('&','\\&').replace('%','\\%').replace('_','\\_').replace('#','\\#')

